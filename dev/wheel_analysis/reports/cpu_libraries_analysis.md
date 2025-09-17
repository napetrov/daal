# CPU Libraries Analysis

## Overview

The CPU deployment consists of:
- **libonedal_core.so.3** (108.74 MiB) - Main CPU algorithms
- **libonedal.so.3** (9.81 MiB) - Dispatcher/API layer
- **libonedal_thread.so.3** (0.23 MiB) - Threading runtime
- **libonedal_parameters.so.3** (0.13 MiB) - Parameter handling

**Total CPU deployment: 119 MiB**

## libonedal_core.so.3 Breakdown (108.74 MiB)

### Content Distribution
- **Code (.text)**: 72.28 MiB (66.5%)
- **Read-only data**: 17.27 MiB (15.9%)
- **Metadata**: 17.85 MiB (16.4%)
- **Writable data**: 1.34 MiB (1.2%)

### Algorithm Distribution

| Algorithm Category | Size | Key Components |
|-------------------|------|----------------|
| **Tree-based** | 10.3 MiB | GBT (5.0 MiB), Random Forest (2.5 MiB), Decision Tree (1.1 MiB) |
| **Clustering** | 2.9 MiB | K-Means (2.0 MiB), DBSCAN (0.9 MiB) |
| **Linear models** | 2.5 MiB | PCA (0.6 MiB), Linear Regression (0.4 MiB), SVD (0.4 MiB) |
| **Statistics** | 3.5 MiB | Moments (1.0 MiB), Covariance (0.7 MiB) |
| **SVM** | 1.1 MiB | Kernel functions, SMO solver |
| **Optimization** | 1.6 MiB | Various solvers |
| **Core services** | ~40 MiB | Memory management, threading, base infrastructure |
| **Other algorithms** | ~47 MiB | Neural nets, neighbors, recommender, etc. |

### MKL Integration
- **Statically linked** - MKL symbols are compiled into the library
- **No external MKL dependencies** - Self-contained
- **Integrated functions** include:
  - BLAS: gemm, gemv, syrk (matrix operations)
  - LAPACK: gesvd, syevd, potrf, geqrf (decompositions)

### Read-only Data (17.27 MiB)
- **Math tables**: 5.2 MiB
  - VML constants (1.2 MiB)
  - Transcendental function data
- **RNG tables**: 3.1 MiB
- **Algorithm constants**: 8.9 MiB

### Optimization Opportunities

1. **Algorithm modularity** (save 60-80 MiB)
   - Split into algorithm-specific libraries
   - Core + selected algorithms deployment

2. **Template deduplication** (save 10-15 MiB)
   - Many algorithms instantiated for multiple types
   - Could share implementations where performance allows

3. **Math table generation** (save 3-5 MiB)
   - Generate some constants at runtime
   - Trade initialization time for size

4. **Debug metadata stripping** (save 10-15 MiB)
   - Remove .symtab and reduce .strtab
   - Keep only essential symbols

## libonedal.so.3 - Dispatcher (9.81 MiB)

### Current State
- Contains 3,260 duplicate symbols with libonedal_dpc.so.3
- 98% of exported symbols are duplicates (445 KiB)
- Should be a thin forwarding layer

### Refactoring Opportunity
Convert to pure dispatcher (save ~8 MiB):
```cpp
// Current: Full implementation
result svm_train(...) {
    // 500 lines of implementation
}

// Proposed: Forward only
result svm_train(...) {
    return get_backend()->svm_train(...);
}
```

## Enabling Debug Symbols

### For C++ Users

1. **Download debug package** (when available):
```bash
# Future: oneDAL-debug package with .debug files
apt install onedal-debug
```

2. **Build from source with debug**:
```bash
make REQDBG=yes
# Or for CMake:
cmake -DCMAKE_BUILD_TYPE=Debug
```

3. **Use separate debug files**:
```bash
# Debug symbols are in separate .debug files
gdb ./myapp
(gdb) set debug-file-directory /usr/lib/debug
```

### For Python Users

1. **Install debug wheel** (when available):
```bash
pip install daal[debug]  # Would include debug symbols
```

2. **Use with Python debugger**:
```python
import faulthandler
faulthandler.enable()

# For C++ debugging from Python
gdb python
(gdb) run -m your_script
```

3. **Environment variable** (proposed):
```bash
export ONEDAL_ENABLE_DEBUG_SYMBOLS=1
python your_script.py
```

## CPU Deployment Options

### Option 1: Monolithic (Current)
- **Size**: 119 MiB
- **Pros**: Simple, all features
- **Cons**: Large for embedded/edge

### Option 2: Modular
```
onedal-core (40 MiB) - Base infrastructure
onedal-trees (10 MiB) - GBT, RF, DT
onedal-linear (3 MiB) - Linear models, PCA
onedal-clustering (3 MiB) - K-Means, DBSCAN
onedal-advanced (63 MiB) - Everything else
```

### Option 3: Tiered
```
onedal-minimal (25 MiB) - K-Means, LinReg, PCA
onedal-standard (60 MiB) - + Trees, SVM, Stats  
onedal-complete (119 MiB) - Everything
```

## Summary

The CPU libraries are well-optimized but monolithic. Key findings:
1. MKL is statically linked (no unused external deps)
2. Tree algorithms dominate size (10.3 MiB)
3. Significant metadata overhead (17.85 MiB)
4. Dispatcher contains unnecessary duplicates

Immediate optimizations:
- Strip debug symbols: 10-15 MiB
- Fix dispatcher: 8 MiB
- **Total quick wins: 18-23 MiB (15-19% reduction)**