# GPU Libraries Analysis

## Overview

The CPU+GPU deployment adds:
- **libonedal_dpc.so.3** (297.89 MiB) - SYCL/GPU implementation
- **libonedal_parameters_dpc.so.3** (0.16 MiB) - GPU parameter handling

**Additional size for GPU: 298 MiB**
**Total CPU+GPU deployment: 417 MiB**

## libonedal_dpc.so.3 Breakdown (297.89 MiB)

### Critical Finding: Only 24% is GPU Code!

| Component | Size | % of Library | Description |
|-----------|------|--------------|-------------|
| **Host Code** | 155.7 MiB | 52.3% | CPU-side orchestration |
| **Device Kernels** | 72.0 MiB | 24.2% | Actual GPU kernels |
| **Symbol Metadata** | 34.3 MiB | 11.5% | Names and tables |
| **Other** | 35.9 MiB | 12.0% | Data, linking, debug |

### Why is Host Code So Large? (155.7 MiB)

Analysis shows 82.7 MiB excess compared to CPU library:

1. **SYCL Runtime Integration** (~40 MiB)
   - Queue management
   - Event synchronization  
   - Memory transfer orchestration
   - Error handling

2. **SYCL-specific Code** (~30 MiB)
   - `.sycl_offloading.*.data`: 27.5 MiB
   - `std::_Function_handler` for SYCL: 12.4 MiB
   - `sycl::_V1::detail` runtime: 9 MiB

3. **MKL GPU Wrappers** (~18 MiB)
   - `oneapi::mkl::gpu` namespace
   - Host-side setup for GPU BLAS/LAPACK

4. **Duplicate Algorithm Implementations** (~28 MiB)
   - Many algorithms have both CPU and GPU paths
   - Template instantiations for device types

### Device Kernels (72.0 MiB)

**6,683 SYCL kernels** with size distribution:
- Median: 5.9 KiB
- 90th percentile: 19.1 KiB  
- Maximum: 628.6 KiB

**Breakdown by Type**:
| Kernel Family | Size | Description |
|---------------|------|-------------|
| MKL GPU kernels | 17.85 MiB | BLAS Level 2/3 operations |
| oneDAL primitives | 8.38 MiB | Selection, distance, reductions |
| MKL verbose/debug | 4.24 MiB | **Removable!** |
| Other kernels | 41.53 MiB | Algorithm-specific |

### Symbol Duplication with CPU

- **3,260 shared symbols** with libonedal.so.3
- Duplicated namespaces:
  - `oneapi::dal::preview::spmd`: 120 KiB
  - `oneapi::dal::svm`: 58 KiB
  - `oneapi::dal::decision_forest`: 55 KiB

### MKL Integration in GPU Library

**Identified MKL GPU kernels**:
- Level 2 BLAS: 8.1 MiB (gemv, triangular)
- Level 3 BLAS: 5.6 MiB (gemm, syrk)
- Utilities: 4.1 MiB (verbose, debug)

**Key insight**: MKL verbose/debug kernels (4.2 MiB) serve no purpose in production!

## Optimization Strategy

### Immediate Wins (No Code Changes)

1. **Strip Debug Symbols**
   - Save: 20-25 MiB
   - Command: `strip --strip-debug`

2. **Remove MKL Verbose**
   - Save: 4.2 MiB
   - Build flag: `-DMKL_VERBOSE=0`

3. **Optimize Build Flags**
   ```makefile
   # Change device code splitting
   -fsycl-device-code-split=per_source  # Instead of per_kernel
   # Enable LTO
   -flto=thin
   ```
   - Save: 10-15 MiB

**Total immediate savings: 34-44 MiB (11-15%)**

### Medium-term Optimizations

1. **Reduce Template Bloat** (20-30 MiB)
   - Share host code between types
   - Consolidate SYCL templates

2. **Split Host/Device Libraries** (architectural change)
   ```
   libonedal_sycl_host.so (100 MiB) - Host orchestration
   libonedal_sycl_device.so (72 MiB) - Device kernels only
   libonedal_sycl_runtime.so (30 MiB) - SYCL runtime wrappers
   ```

3. **Kernel Consolidation** (10-15 MiB)
   - Merge similar kernels
   - Share code for common patterns

## Enabling Debug Symbols for GPU

### For C++ Users

1. **Keep debug build separate**:
```bash
# Production build (stripped)
make REQDBG=no ONEDAL_USE_DPCPP=yes

# Debug build (with symbols)
make REQDBG=yes ONEDAL_USE_DPCPP=yes
objcopy --only-keep-debug libonedal_dpc.so.3 libonedal_dpc.so.3.debug
```

2. **Use Intel VTune/Advisor**:
```bash
# Profile with debug symbols
vtune -collect gpu-hotspots -result-dir=profile ./app
```

### For Python Users

1. **Environment-based loading**:
```python
import os
if os.environ.get('ONEDAL_DEBUG'):
    import daal_debug as daal  # Debug version
else:
    import daal  # Production version
```

2. **SYCL debugging**:
```bash
export SYCL_PI_TRACE=1  # Trace SYCL calls
export SYCL_DEVICE_FILTER=level_zero:gpu  # Force GPU
```

## CPU vs CPU+GPU Deployment Comparison

| Metric | CPU Only | CPU+GPU | Difference |
|--------|----------|---------|------------|
| **Total Size** | 119 MiB | 417 MiB | +298 MiB (+250%) |
| **Libraries** | 4 | 6 | +2 |
| **Algorithms** | All CPU | All CPU+GPU | Same coverage |
| **Dependencies** | libc, libm | + libsycl, OpenCL | More runtime deps |
| **Complexity** | Simple | Complex | SYCL runtime |

## Recommendations

### For CPU+GPU Deployments

1. **Default to CPU** with GPU as optional download
2. **Create GPU-lite variant** (remove debug/verbose): -4.2 MiB immediately
3. **Implement lazy loading** for GPU kernels
4. **Consider cloud deployment** where size is less critical

### Size Reduction Priority

1. **Immediate** (this week):
   - Strip symbols: 20-25 MiB
   - Remove verbose: 4.2 MiB
   - Build flags: 10-15 MiB
   - **Total: 34-44 MiB**

2. **Short-term** (this month):
   - Template reduction: 20-30 MiB
   - Fix duplicates: 5-10 MiB
   - **Total: 25-40 MiB**

3. **Long-term** (next release):
   - Architecture split: 50-70 MiB
   - Kernel optimization: 15-20 MiB
   - **Total: 65-90 MiB**

**Potential total reduction: 124-174 MiB (42-58% of current 298 MiB)**

## Summary

The GPU library is dominated by host-side code (52%), not GPU kernels (24%). This presents significant optimization opportunities through:
1. Removing unnecessary components (debug, verbose)
2. Reducing template bloat and duplication
3. Architectural improvements to separate concerns

The current monolithic approach bundles everything together, but a more modular design could reduce the GPU overhead from 298 MiB to potentially 150-170 MiB while maintaining full functionality.