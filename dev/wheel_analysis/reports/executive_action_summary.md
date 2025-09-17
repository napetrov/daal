# Executive Action Summary for oneDAL Binary Size Reduction

## Quick Wins (1-2 weeks, 44.2 MiB savings)

### 1. Debug Symbol Stripping (30-40 MiB)
```bash
# Add to build pipeline
strip --strip-debug libonedal_*.so
# Package debug symbols separately
objcopy --only-keep-debug libonedal_dpc.so.3 libonedal_dpc.so.3.debug
```
**ABI Impact**: None ✅

### 2. Remove MKL Verbose Kernels (4.2 MiB)
```makefile
# Add build flag
COPT += -DMKL_VERBOSE=0 -DONEDAL_DISABLE_KERNEL_PROFILING
```
**ABI Impact**: None ✅

## Multi-Wheel Strategy (2-4 weeks, up to 307 MiB savings)

### Recommended Package Structure
```
daal-cpu          (110 MiB)  # Laptop users
daal              (180 MiB)  # Default: CPU + essential GPU
daal-gpu          (290 MiB)  # Full GPU support
daal-debug        (50 MiB)   # Debug symbols (optional)
```

### Smart Installation
```python
# In setup.py
def get_optimal_wheel():
    if has_cuda() or has_level_zero():
        return "daal-gpu" if power_user else "daal"
    return "daal-cpu"
```
**ABI Impact**: None (separate packages) ✅

## Kernel Consolidation (4-6 weeks, 15-20 MiB savings)

### Build Configuration Changes
```makefile
# Test these options in order
-fsycl-device-code-split=per_source  # Try first
-fsycl-device-code-split=auto       # If build time acceptable
-flto=thin                          # Always beneficial
```
**ABI Impact**: None ✅

## Architecture Changes (Next Major Release)

### SPMD Consolidation (120 KiB savings)
- Create `libonedal_spmd_common.so`
- Both dispatcher and DPC++ link to it
**ABI Impact**: Breaking ❌ (Plan for 2026.0.0)

### Dispatcher Slim-down (400 KiB savings)
- Convert to pure forwarding
- Move implementations to backends
**ABI Impact**: Breaking ❌ (Plan for 2026.0.0)

## MKL Analysis Results

### Essential MKL Functions (Keep)
- **SVD** (gesvd) - Used by: PCA, Linear Regression
- **Eigenvalues** (syevd) - Used by: PCA, EM/GMM
- **Cholesky** (potrf) - Used by: Covariance, Gaussian
- **QR** (geqrf) - Used by: QR decomposition, SVD

### Potentially Removable
- Sparse BLAS (except SpMV for SVM)
- FFT routines (unused)
- Complex number support (if not needed)

### Custom Implementation Candidates
- Simple GEMV for specific sizes
- Element-wise operations
- Basic reductions

## Timeline and Priorities

### Immediate (This Week)
1. **Strip symbols**: 1 day work, 30-40 MiB saved
2. **Disable verbose**: 0.5 day work, 4.2 MiB saved
3. **Test LTO**: 1 day work, 5-10% size reduction

### Short Term (This Month)
1. **CPU-only wheel**: 1 week work, 307 MiB saved for laptop users
2. **Kernel consolidation experiments**: 1 week work, 10-15 MiB saved
3. **Export audit**: 3 days work, 5-10 MiB metadata saved

### Medium Term (Next Quarter)
1. **Multi-wheel infrastructure**: 2 weeks work
2. **Custom BLAS for small ops**: 3 weeks work, 5-8 MiB saved
3. **Dead code elimination**: 2 weeks work, 10-15 MiB saved

### Long Term (Next Major Version)
1. **SPMD refactor**: 1 month work, cleaner architecture
2. **Dispatcher redesign**: 1 month work, 400 KiB saved
3. **Template consolidation**: 3 weeks work, 15-20 MiB saved

## Laptop-Specific Optimization

For immediate laptop relief:
```bash
# Build CPU-only variant
make ONEDAL_USE_DPCPP=no

# Results in:
# - 110 MiB package (73% reduction)
# - No GPU dependencies
# - All CPU algorithms intact
# - Full scikit-learn-intelex compatibility
```

## Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Symbol stripping | Low | Keep debug package |
| Multi-wheel | Low | Clear documentation |
| LTO | Medium | Performance testing |
| Kernel consolidation | Medium | A/B testing |
| Architecture changes | High | Major version bump |

## Decision Points

1. **Q: Start with CPU-only wheel for laptops?**
   - Recommendation: **YES** - Biggest immediate impact

2. **Q: Which code-split strategy?**
   - Recommendation: Try `per_source` first, measure build time

3. **Q: When to break ABI?**
   - Recommendation: Bundle all breaking changes for 2026.0.0

4. **Q: Custom BLAS implementation?**
   - Recommendation: Only for high-frequency small operations

## Next Actions

1. **Today**: Start debug symbol stripping in CI
2. **This Week**: Create CPU-only build configuration
3. **Next Week**: Begin multi-wheel packaging infrastructure
4. **This Month**: Complete immediate optimizations, plan major version

Total Potential Savings:
- **Immediate**: 44.2 MiB (10.6%)
- **With CPU-only**: 307 MiB for laptop users (73.6%)
- **Long term**: 60-80 MiB additional (14-19%)