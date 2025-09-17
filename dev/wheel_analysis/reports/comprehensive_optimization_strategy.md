# Comprehensive oneDAL Binary Optimization Strategy

## Executive Summary

Based on the detailed analysis, we can achieve significant size reductions through a phased approach:
- **Phase 1** (ABI Compatible): 40-50 MiB reduction via symbol stripping and build optimizations
- **Phase 2** (Multi-wheel): 110-190 MiB reduction for targeted deployments
- **Phase 3** (Next Major Release): Additional 20-30 MiB via architectural changes

## MKL Function Analysis and Usage Map

### Detailed MKL Usage by Algorithm

| Algorithm | MKL Functions | Source Location | Replace with Custom? | Size Impact |
|-----------|--------------|-----------------|---------------------|-------------|
| **PCA** | gesvd, syevd | `pca_dense_*.i` | ❌ Complex math | Core function |
| **SVD** | gesvd, geqrf, orgqr | `svd_dense_default_impl.i` | ❌ Core LAPACK | 2.3 MiB kernels |
| **Covariance** | syrk, xxrscl | `covariance_impl.i` | ⚠️ Possible | 0.8 MiB kernels |
| **EM/GMM** | syevd (eigenvalues) | `em_gmm_dense_*.i` | ❌ Eigensolvers | 1.1 MiB kernels |
| **Cholesky** | potrf, pptrf | `cholesky_impl.i` | ⚠️ Possible | 0.5 MiB kernels |
| **QR Decomposition** | geqrf, orgqr | `qr_dense_*.i` | ❌ Core LAPACK | 1.5 MiB kernels |
| **Linear Regression** | gesvd (via SVD) | Uses SVD algorithm | ❌ Inherited | Shared with SVD |
| **Ridge Regression** | syrk + solve | Via normal equations | ⚠️ Partially | 0.6 MiB kernels |

### MKL Kernel Breakdown (17.85 MiB total)

```
Core Linear Algebra (8.5 MiB):
├── BLAS Level 2 (5.6 MiB)
│   ├── gemv operations - 1.5 MiB
│   ├── triangular solves - 4.1 MiB
├── BLAS Level 3 (2.9 MiB) 
│   ├── gemm operations - 1.9 MiB
│   └── syrk operations - 1.0 MiB

Debugging/Profiling (4.2 MiB):
├── verbose_buffer_start - 2.1 MiB
└── verbose_buffer_end - 2.1 MiB

Matrix Utilities (5.1 MiB):
├── matadd_block_kernel - 1.9 MiB
├── batch operations - 1.6 MiB
└── misc operations - 1.6 MiB
```

## Optimization Strategy by Deployment Scenario

### 1. Laptop Deployment (Primary Concern)

**Immediate CPU-Only Package** (110 MiB total, -73% reduction)
```bash
# Package contents
libonedal_core.so.3     - 108.74 MiB
libonedal.so.3          -   1.20 MiB (after refactoring)
libonedal_thread.so.3   -   0.23 MiB
libonedal_parameters.so.3 - 0.13 MiB
```

**Implementation Steps:**
1. Build without ONEDAL_DATA_PARALLEL flag
2. Skip libonedal_dpc.so.3 entirely
3. Remove GPU-specific dependencies

### 2. Multi-Wheel Distribution Strategy

#### Option A: Device-Based (Recommended)
```
daal-cpu-2025.8.0        (110 MiB) - CPU only, all algorithms
daal-gpu-lite-2025.8.0   (180 MiB) - GPU + essential kernels
daal-gpu-full-2025.8.0   (290 MiB) - Current full package
```

#### Option B: Algorithm-Based
```
daal-core-2025.8.0       (45 MiB)  - Linear models, k-means
daal-ml-2025.8.0         (110 MiB) - + Trees, SVM, clustering
daal-advanced-2025.8.0   (180 MiB) - + Deep learning, graph
daal-complete-2025.8.0   (290 MiB) - Everything
```

#### Installation Intelligence
```python
# Auto-detect optimal package
pip install daal  # Installs daal-cpu on laptops, daal-gpu-lite on GPU systems

# Explicit selection
pip install daal[cpu]      # Force CPU-only
pip install daal[gpu-lite] # Minimal GPU
pip install daal[gpu-full] # All features
```

## Build Time Optimization Experiments

### 1. SYCL Code Split Strategies

| Strategy | Command | Build Time | Size Impact | Recommendation |
|----------|---------|------------|-------------|----------------|
| Current | `-fsycl-device-code-split=per_kernel` | Baseline | 70 MiB kernels | Too granular |
| Per Source | `-fsycl-device-code-split=per_source` | +20% | -15% size | **Try first** |
| Auto | `-fsycl-device-code-split=auto` | +10% | -10% size | Good balance |
| Off | `-fsycl-device-code-split=off` | +200% | -25% size | Max sharing |

### 2. Link-Time Optimization Profile

```makefile
# Recommended LTO configuration
COPT.dpcpp += -flto=thin -fuse-ld=lld
LOPT.dpcpp += -flto=thin -Wl,--thinlto-jobs=$(nproc) -Wl,--thinlto-cache-dir=.thinlto

# Expected results:
# - 5-10% binary size reduction
# - 30-50% longer build time
# - Better dead code elimination
```

### 3. Debug Symbol Strategy

```bash
# Separate debug packages
strip --strip-debug *.so        # Immediate 30-40 MiB savings
objcopy --only-keep-debug *.so *.debug  # Extract debug info

# Optional debug package
daal-debug-2025.8.0 (50 MiB) - Debug symbols only
```

## ABI Compatibility Matrix

### ✅ Safe for Immediate Implementation
1. **Symbol Visibility** (`-fvisibility=hidden`)
   - Already enabled, need to audit export macros
   - No ABI change, just hiding internals

2. **Debug Stripping**
   - Pure metadata removal
   - No functional impact

3. **Build Optimizations** (LTO, code-split)
   - Compiler optimizations only
   - Same external interface

4. **MKL Verbose Removal**
   - Compile-time flag to skip debug kernels
   - Saves 4.2 MiB immediately

### ⚠️ Minor Version Update (2025.9.0)
1. **Parameter Library Merge**
   - Combine parameters libraries
   - Update library dependencies

2. **Internal Namespace Cleanup**
   - Remove duplicate internal symbols
   - Keep public API stable

### ❌ Major Version Update (2026.0.0)
1. **SPMD Consolidation**
   - Move to shared library
   - Changes library linking

2. **Dispatcher Architecture**
   - Convert to forwarding layer
   - New dependency structure

3. **Template Instantiation Control**
   - May change symbol names
   - Requires careful migration

## Kernel Grouping Analysis

### By Algorithm Family (6,683 total kernels)

```yaml
Machine Learning Core (2,450 kernels, 25.3 MiB):
  k-nearest-neighbors:
    - kernel_select_heap: 96 kernels, 3.5 MiB
    - distance_metrics: 142 kernels, 1.9 MiB
  
  decision-forest:
    - tree_traversal: 203 kernels, 1.2 MiB
    - split_criteria: 187 kernels, 0.9 MiB
  
  svm:
    - kernel_matrix: 156 kernels, 1.1 MiB
    - smo_solver: 134 kernels, 0.7 MiB

Linear Algebra Primitives (1,823 kernels, 17.8 MiB):
  mkl-wrappers:
    - blas_l2: 472 kernels, 8.1 MiB
    - blas_l3: 288 kernels, 5.6 MiB
    - lapack: 124 kernels, 4.1 MiB

Data Processing (1,156 kernels, 12.4 MiB):
  reductions:
    - sum/mean: 234 kernels, 2.3 MiB
    - min/max: 198 kernels, 1.8 MiB
  
  transformations:
    - normalization: 167 kernels, 1.5 MiB
    - scaling: 145 kernels, 1.2 MiB

Utility Kernels (1,254 kernels, 14.5 MiB):
  memory:
    - copy/fill: 432 kernels, 5.2 MiB
    - conversion: 312 kernels, 4.1 MiB
  
  debugging:
    - verbose/profiling: 234 kernels, 4.2 MiB
```

### Consolidation Opportunities

1. **Template Reduction** (save 15-20 MiB)
   ```cpp
   // Current: Separate kernels per type
   kernel<float>, kernel<double>, kernel<int32>, kernel<int64>
   
   // Proposed: Type-erased kernels where possible
   kernel<numeric_t> with runtime dispatch
   ```

2. **MKL Wrapper Consolidation** (save 5-8 MiB)
   ```cpp
   // Current: Individual wrappers per operation
   // Proposed: Unified MKL dispatcher with operation enum
   ```

3. **Debug Kernel Removal** (save 4.2 MiB)
   ```cpp
   #ifndef ONEDAL_ENABLE_KERNEL_PROFILING
   // Skip verbose_buffer_* kernels entirely
   #endif
   ```

## Implementation Roadmap

### Week 1-2: Immediate Wins (40 MiB reduction)
- [ ] Strip debug symbols from release builds
- [ ] Remove MKL verbose kernels via compile flag
- [ ] Audit and reduce export macros
- [ ] Enable thin LTO for 5-10% size reduction

### Week 3-4: Multi-Wheel MVP (110 MiB reduction for laptops)
- [ ] Create CPU-only build configuration
- [ ] Setup multi-wheel packaging pipeline
- [ ] Implement pip install intelligence
- [ ] Update documentation

### Month 2: Kernel Optimization (10-15 MiB reduction)
- [ ] Experiment with code-split strategies
- [ ] Consolidate template instantiations
- [ ] Remove unused MKL functionality
- [ ] Profile and eliminate dead code

### Month 3+: Architecture Refactor (20-30 MiB reduction)
- [ ] Plan for next major version
- [ ] SPMD library consolidation
- [ ] Dispatcher architecture redesign
- [ ] Custom BLAS for simple operations

## Success Metrics

1. **Laptop Package**: < 120 MiB (from 417 MiB)
2. **GPU-Lite Package**: < 200 MiB
3. **Build Time**: < 1.5x current
4. **Performance**: No regression
5. **API Compatibility**: 100% preserved

## Risk Mitigation

1. **Performance Testing**: Automated benchmarks for each change
2. **Compatibility Matrix**: Test against scikit-learn-intelex
3. **Rollback Plan**: Versioned releases with clear migration guides
4. **User Communication**: Clear documentation of package variants