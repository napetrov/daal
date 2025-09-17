# MKL Usage Summary

## MKL Integration in oneDAL

### CPU Library (libonedal_core.so.3)
- **MKL is statically linked** - No external MKL dependencies
- **No unused MKL routines** - All linked MKL code is used
- Integration is optimal for CPU deployment

### GPU Library (libonedal_dpc.so.3)
MKL GPU kernels identified (17.85 MiB total):

| Kernel Family | Size | Count | Purpose |
|---------------|------|-------|---------|
| Level 2 BLAS | 8.1 MiB | 760 | gemv, triangular operations |
| Level 3 BLAS | 5.6 MiB | 320 | gemm, syrk operations |
| Verbose/Debug | 4.2 MiB | 274 | **REMOVABLE - Not needed in production** |

### Algorithms Using MKL Functions

Based on source analysis, MKL functions are used in:
- **Linear Kernel**: Uses gemm for kernel computation
- **PCA**: Uses syevd for eigenvalue decomposition
- **Covariance**: Uses syrk for symmetric matrix operations
- **K-Means**: Uses gemm/gemv for distance calculations

### Key Finding: No Unused MKL Code

Both CPU and GPU libraries contain only the MKL functionality they actually use:
- CPU: MKL statically linked, no waste
- GPU: MKL GPU kernels generated on-demand

The only removable MKL components are the verbose/debug kernels in the GPU library (4.2 MiB).

## Recommendations

1. **Immediate**: Remove MKL verbose kernels from GPU build (-4.2 MiB)
   ```makefile
   # Add to build flags
   -DMKL_VERBOSE=0
   ```

2. **No action needed** for CPU library - MKL integration is already optimal

3. **Consider**: Dynamic MKL linking would add external dependency without size benefit