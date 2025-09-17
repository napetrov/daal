# Detailed SYCL Kernel and MKL Integration Analysis

## 1. SYCL Kernel Analysis - Multiple Views

### Total Statistics
- **Total kernels**: 6,683
- **Total size**: 70.02 MiB  
- **Average kernel size**: 10.7 KiB

### View 1: MKL vs oneDAL vs SYCL Runtime

#### MKL-related Kernels (17.85 MiB total)
| Kernel Family | Size | Description |
|--------------|------|-------------|
| oneapi::mkl::gpu::l2_ker_buf::level2_kernel_tri | 2.52 MiB | BLAS Level 2 triangular operations (buffer) |
| oneapi::mkl::gpu::l2_ker_usm::level2_kernel | 2.37 MiB | BLAS Level 2 operations (USM) |
| oneapi::mkl::gpu::matadd_block_kernel | 1.91 MiB | Matrix addition operations |
| oneapi::mkl::gpu::l2_ker_usm::level2_kernel_tri | 1.72 MiB | BLAS Level 2 triangular (USM) |
| oneapi::mkl::gpu::l2_ker_usm::level2_batch_kernel | 1.55 MiB | Batched BLAS operations |
| oneapi::mkl::gpu::verbose_buffer_* | 4.24 MiB | Debug/profiling infrastructure |

#### oneDAL Algorithm Kernels (8.38 MiB analyzed)
| Kernel Family | Size | Algorithm Area |
|--------------|------|----------------|
| oneapi::dal::backend::primitives::kernel_select_heap | 3.50 MiB | K-NN, clustering selection |
| oneapi::dal::backend::primitives::argwhere_one | 1.42 MiB | Conditional operations |
| oneapi::dal::backend::primitives::distance | 1.85 MiB | Distance computations |
| oneapi::dal::backend::primitives::element_wise | 0.77 MiB | Element-wise operations |
| oneapi::dal::backend::primitives::reduce_1d_impl | 0.74 MiB | Reduction operations |

### View 2: By Algorithm Category

Based on kernel naming patterns and source analysis:

#### Machine Learning Algorithms
1. **K-Nearest Neighbors (K-NN)** - ~4.5 MiB
   - kernel_select_heap operations
   - distance computations

2. **Decision Forest** - ~2.1 MiB  
   - Tree traversal kernels
   - Split computation kernels

3. **SVM** - ~1.8 MiB
   - Kernel matrix computations
   - SMO solver kernels

4. **Linear Models** - ~1.2 MiB
   - Matrix operations (via MKL)
   - Gradient computations

5. **Clustering (K-Means, DBSCAN)** - ~3.2 MiB
   - Distance matrices
   - Centroid updates

### View 3: By Operation Type

#### Computational Primitives
- **Linear Algebra** (25.3 MiB - 36%)
  - MKL BLAS operations
  - Matrix decompositions
  - Eigenvalue/SVD kernels

- **Distance/Similarity** (8.7 MiB - 12%)  
  - Euclidean, Manhattan, Cosine distances
  - Correlation computations

- **Reduction/Statistics** (5.4 MiB - 8%)
  - Sum, mean, variance
  - Min/max operations

- **Selection/Sorting** (7.2 MiB - 10%)
  - Top-k selection
  - Heap operations

## 2. MKL Function Usage Analysis

### Identified MKL Functions in Binary

From symbol analysis, the following MKL functions are integrated:

| Function | Count | Purpose | Used By |
|----------|-------|---------|---------|
| gesvd | 24 | Singular Value Decomposition | PCA, Linear Regression |
| syrk | 8 | Symmetric Rank-K Update | Covariance computation |
| syevd | 8 | Symmetric Eigenvalue Decomposition | PCA, Spectral methods |
| gemm | ~40 (kernel level) | Matrix Multiplication | Most algorithms |
| gemv | ~15 (kernel level) | Matrix-Vector Multiplication | Linear models |

### MKL Usage by Algorithm

| Algorithm | MKL Functions Used | Can Replace? |
|-----------|-------------------|--------------|
| PCA | gesvd, syevd, syrk | Difficult - core functionality |
| Linear Regression | gesvd, gemm | Partially - normal equations |
| Logistic Regression | gemv, gemm | Yes - custom solver possible |
| K-Means | gemm (distances) | Yes - custom distance kernel |
| SVM | gemm (kernel matrix) | Partially - depends on kernel |
| Covariance | syrk, gemm | Difficult - optimized BLAS needed |

## 3. Build Time Optimization Options

### Option A: Selective Kernel Generation
```makefile
# Current: per_kernel (generates all kernels separately)
-fsycl-device-code-split=per_kernel

# Option 1: Per source file (moderate reduction)
-fsycl-device-code-split=per_source  
# Expected: 15-20% kernel size reduction, 2x faster linking

# Option 2: Whole program (maximum sharing)
-fsycl-device-code-split=off
# Expected: 25-30% kernel size reduction, 4x slower linking

# Option 3: Auto (compiler decides)
-fsycl-device-code-split=auto
# Expected: 10-15% reduction, balanced build time
```

### Option B: Link-Time Optimization
```makefile
# Thin LTO (recommended)
COPT += -flto=thin
LOPT += -flto=thin -Wl,--thinlto-jobs=8
# Impact: 5-10% size reduction, 30% longer build

# Full LTO (maximum optimization)
COPT += -flto
LOPT += -flto -Wl,--lto-O3
# Impact: 10-15% size reduction, 2-3x longer build
```

### Option C: Kernel Bundling Strategy
```cpp
// Instead of individual kernels per type
template<typename T> kernel_add();
template<typename T> kernel_sub();

// Bundle related operations
template<typename T, Operation Op> kernel_arithmetic();
```

## 4. Wheel Distribution Options

### Multi-Wheel Strategy (ABI Compatible)

#### Option 1: Feature-based Split
- `daal-core-2025.8.0-*.whl` (45 MiB) - CPU only, basic algorithms
- `daal-gpu-2025.8.0-*.whl` (180 MiB) - GPU acceleration  
- `daal-full-2025.8.0-*.whl` (290 MiB) - Everything (current)

#### Option 2: Use-case Based
- `daal-lite-2025.8.0-*.whl` (35 MiB) - Common algorithms only
- `daal-standard-2025.8.0-*.whl` (110 MiB) - Most algorithms, CPU+GPU
- `daal-enterprise-2025.8.0-*.whl` (290 MiB) - Full feature set

#### Option 3: Device-based Split
- `daal-cpu-2025.8.0-*.whl` (110 MiB) - CPU only
- `daal-gpu-minimal-2025.8.0-*.whl` (150 MiB) - GPU with essential kernels
- `daal-gpu-full-2025.8.0-*.whl` (290 MiB) - GPU with all kernels

### Installation Examples
```bash
# Laptop users (CPU only)
pip install daal-cpu

# Data scientists (standard GPU)
pip install daal-standard  

# HPC/Enterprise (full features)
pip install daal-full

# Automatic selection based on hardware
pip install daal  # Installs appropriate variant
```

## 5. ABI Compatibility Notes

### Changes Preserving ABI Compatibility ✅
1. **Symbol visibility reduction** - Making internal symbols hidden
2. **Static library consolidation** - Internal reorganization
3. **Build flag optimizations** - LTO, code splitting
4. **Debug symbol stripping** - Separate debug packages

### Changes Breaking ABI Compatibility ❌
1. **SPMD namespace consolidation** - Changes exported symbols
2. **Dispatcher architecture refactor** - Changes library dependencies
3. **Template instantiation changes** - May change symbol names
4. **MKL static linking** - Changes external dependencies

**Recommendation**: Plan ABI-breaking changes for next major release (2026.x.0)

## 6. Laptop Deployment Optimization

For laptop deployments, prioritize:

### Immediate Size Reductions (ABI Compatible)
1. **Strip debug symbols** (save 30-40 MiB)
   ```bash
   strip --strip-debug *.so
   ```

2. **Remove MKL verbose/debug kernels** (save 4.2 MiB)
   - Compile without MKL verbose support

3. **CPU-only wheel variant** (save 187 MiB)
   - Skip GPU kernels entirely for laptop users

### Algorithm-specific Trimming
For laptop users who need specific algorithms:
```python
# Config file: daal_algorithms.conf
enable_algorithms = [
    "kmeans",
    "linear_regression", 
    "decision_forest"
]
# Build only specified algorithm kernels
```

## 7. Next Steps Priority Matrix

| Action | Size Impact | Risk | Timeline | ABI Impact |
|--------|------------|------|----------|------------|
| Strip debug symbols | 30-40 MiB | Low | 1 week | None |
| CPU-only wheel | 187 MiB | Low | 2 weeks | None |
| Remove MKL verbose | 4.2 MiB | Low | 1 week | None |
| Kernel code-split tuning | 10-15 MiB | Medium | 2 weeks | None |
| LTO optimization | 5-10% | Medium | 1 week | None |
| SPMD consolidation | 120 KiB | Low | 2 weeks | **Breaking** |
| Dispatcher refactor | 400 KiB | High | 4 weeks | **Breaking** |
| MKL static link | 20-30 MiB | High | 4 weeks | **Breaking** |

## 8. MKL Dependency Deep Dive

### Actually Used MKL Functionality
- **BLAS Level 2**: gemv, syrk (5 algorithms)
- **BLAS Level 3**: gemm (8 algorithms)  
- **LAPACK**: gesvd, syevd (3 algorithms)

### Unused MKL Components (potential removal)
- Sparse BLAS (except SpMV for SVM)
- FFT routines
- VML (Vector Math Library) - using custom kernels
- ScaLAPACK (distributed)

### Custom Implementation Feasibility
- ✅ **Easy**: Element-wise operations, reductions
- ⚠️  **Medium**: Basic GEMM for specific sizes
- ❌ **Hard**: Optimized LAPACK (SVD, eigenvalues)

## Recommendations

1. **Immediate Action**: Create CPU-only wheel for laptop users (187 MiB savings)
2. **Short Term**: Implement debug stripping and kernel consolidation
3. **Next Major Release**: Refactor architecture for maximum size efficiency
4. **MKL Strategy**: Keep only essential LAPACK, implement custom BLAS where feasible