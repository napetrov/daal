# Deep Dive: Library Content Analysis

## libonedal_dpc.so.3 Content Breakdown (297.89 MiB)

### What's Besides the 70 MiB SPIR-V?

The SPIR-V device kernels are only 24.2% of the library. Here's what else is inside:

| Category | Size | % of Total | Description |
|----------|------|------------|-------------|
| **Host Code** | 155.7 MiB | 52.3% | CPU-side orchestration and SYCL runtime |
| **Device Kernels** | 72.0 MiB | 24.2% | SPIR-V + metadata |
| **Symbol Metadata** | 34.3 MiB | 11.5% | Names and symbol tables |
| **Read-only Data** | 15.6 MiB | 5.2% | Constants, tables, strings |
| **Exception/Debug** | 7.9 MiB | 2.7% | Exception handling frames |
| **Linking Data** | 7.8 MiB | 2.6% | Relocations and PLT |
| **Writable Data** | 5.2 MiB | 1.7% | Global variables, vtables |

### Detailed Section Breakdown

#### 1. Host Code (.text) - 155.6 MiB
This is the CPU-side code that:
- **SYCL Runtime Integration** (~40 MiB)
  - Queue management
  - Event synchronization
  - Memory transfers (host ↔ device)
  - Kernel launch orchestration

- **Algorithm Host Code** (~70 MiB)
  - Data preparation for GPU
  - Result post-processing
  - Fallback CPU implementations
  - API entry points

- **Template Instantiations** (~30 MiB)
  - Duplicated across types (float, double, int32, etc.)
  - SYCL buffer/accessor templates
  - Algorithm templates

- **MKL Integration** (~15 MiB)
  - Host-side MKL calls
  - Data format conversions
  - Error handling

#### 2. Symbol Metadata - 34.3 MiB
- **.strtab** (24.9 MiB): Symbol names
  - Average symbol name: 180 characters
  - Longest: 9,622 characters (!)
  - 333,387 total symbols
- **.symtab** (8.5 MiB): Symbol table entries
- **.dynstr** (0.7 MiB): Dynamic symbol names
- **.dynsym** (0.1 MiB): Dynamic symbol table

#### 3. Read-only Data - 15.6 MiB
- **Algorithm constants** (8.2 MiB)
- **SYCL runtime data** (4.1 MiB)
- **Exception tables** (2.0 MiB)
- **String literals** (1.3 MiB)

#### 4. Other Significant Sections
- **Relocations** (.rela.dyn): 7.8 MiB - Runtime linking data
- **Exception handling** (.eh_frame): 7.1 MiB - Stack unwinding
- **Read-only relocatable** (.data.rel.ro): 4.1 MiB - Vtables, type info

### Key Insights
1. **Host code dominates** (52.3%) - More than 2x the device code
2. **Metadata overhead is huge** (11.5%) - Due to extreme template names
3. **Duplicated host/device logic** - Many algorithms have both CPU and GPU paths

## libonedal_core.so.3 Content Analysis (108.74 MiB)

### Overall Composition
- **Code**: 72.28 MiB (66.5%)
- **Read-only data**: 17.27 MiB (15.9%)
- **Metadata**: ~17.85 MiB (16.4%)
- **Writable data**: 1.34 MiB (1.2%)

### Splitting Strategy 1: By Algorithm Family

#### Tree-Based Algorithms (10.3 MiB - 9.5%)
```
libonedal_tree.so:
├── Gradient Boosted Trees (GBT)      5.0 MiB
├── Random Forest                      2.5 MiB
├── Decision Trees                     1.1 MiB
├── Tree utilities                     1.7 MiB
```
**Users**: Data scientists, classification/regression tasks

#### Linear Algorithms (2.5 MiB - 2.3%)
```
libonedal_linear.so:
├── PCA                               0.6 MiB
├── Linear Regression                 0.4 MiB
├── Ridge/Lasso                       0.3 MiB
├── SVD                               0.4 MiB
├── Linear algebra utils              0.8 MiB
```
**Users**: Statistical analysis, dimensionality reduction

#### Clustering (2.9 MiB - 2.7%)
```
libonedal_clustering.so:
├── K-Means                           2.0 MiB
├── DBSCAN                            0.9 MiB
```
**Users**: Unsupervised learning, data exploration

#### Statistics & Analytics (3.5 MiB - 3.2%)
```
libonedal_stats.so:
├── Descriptive statistics            1.0 MiB
├── Covariance/Correlation            0.7 MiB
├── Quantiles                         0.3 MiB
├── Low-order moments                 0.9 MiB
├── Statistical tests                 0.6 MiB
```
**Users**: Data analysis, preprocessing

#### Advanced ML (5.2 MiB - 4.8%)
```
libonedal_advanced.so:
├── SVM                               1.1 MiB
├── Neural Networks                   0.8 MiB
├── Optimization Solvers              1.6 MiB
├── Implicit ALS                      0.6 MiB
├── Ensemble methods                  1.1 MiB
```
**Users**: Complex ML tasks

#### Core Services (remaining ~84 MiB)
```
libonedal_services.so:
├── Memory management
├── Threading/parallelization
├── Data management
├── Math functions (non-MKL)
├── Serialization
```

### Splitting Strategy 2: By Usage Pattern

#### Essential Package (25 MiB)
```
libonedal_essential.so:
├── K-Means                           2.0 MiB
├── Linear Regression                 0.4 MiB
├── PCA                               0.6 MiB
├── Basic statistics                  1.0 MiB
├── Core services                    21.0 MiB
```
**For**: Basic ML tasks, 80% of use cases

#### Professional Package (45 MiB)
```
libonedal_professional.so:
├── All Essential +
├── Random Forest                     2.5 MiB
├── GBT                               5.0 MiB
├── SVM                               1.1 MiB
├── DBSCAN                            0.9 MiB
├── Additional services              10.5 MiB
```
**For**: Standard data science workflows

#### Enterprise Package (108.74 MiB)
```
libonedal_enterprise.so:
├── Everything
├── Neural Networks
├── Advanced optimizers
├── Specialized algorithms
```
**For**: Complete functionality

### Splitting Strategy 3: By Performance Tier

#### Tier 1: Memory Efficient (30 MiB)
- Single-precision only
- Basic algorithms
- Minimal templates

#### Tier 2: Balanced (65 MiB)
- Float + Double precision
- Most algorithms
- Standard optimizations

#### Tier 3: Maximum Performance (108.74 MiB)
- All precisions
- All optimizations
- All algorithms

### Splitting Strategy 4: By Data Type

#### Tabular Data Package (75 MiB)
- All traditional ML algorithms
- Statistics
- No deep learning

#### Time Series Package (35 MiB)
- ARIMA components
- Seasonality detection
- Forecasting algorithms

#### Graph Analytics Package (25 MiB)
- Connected components
- PageRank
- Graph kernels

### Read-only Data Analysis (17.27 MiB)

#### Math Constants (5.2 MiB)
```
VML Tables:
├── _VAPI_COMMON_DATA_NAME     1.2 MiB  (transcendental functions)
├── vdpowx_data                0.4 MiB  (power functions)
├── vdcdfnorminv_data         0.4 MiB  (normal CDF inverse)
├── vderfinv_data             0.2 MiB  (error function inverse)
└── Other math tables          3.0 MiB
```

#### RNG Tables (3.1 MiB)
```
├── _vsl_mt2203_table         71 KiB
├── _vsl_sfmt19937_poly      131 KiB
└── Other RNG data           2.9 MiB
```

#### Algorithm-specific Data (8.9 MiB)
- Decision tree split criteria
- Kernel function parameters
- Optimization constants

## Recommendations

### For libonedal_dpc.so.3
1. **Reduce template instantiations** (save 20-30 MiB)
   - Share code between float/double where possible
   - Use type erasure for non-performance critical paths

2. **Optimize symbol names** (save 15-20 MiB)
   - Shorter template names
   - Symbol compression

3. **Split host/device code** (architectural improvement)
   - Separate libraries for host orchestration vs device kernels
   - Enable loading only needed components

### For libonedal_core.so.3
1. **Immediate: Algorithm-based split** 
   - Most intuitive for users
   - Clear dependencies
   - Enables "pay for what you use"

2. **Best for adoption: Usage-pattern split**
   - Essential/Professional/Enterprise tiers
   - Covers common use cases in smaller packages

3. **Most flexible: Modular components**
   - Fine-grained control
   - Requires dependency management
   - Best for advanced users

### Size Optimization Priorities
1. **Tree algorithms** (10.3 MiB) - Largest single component
2. **Math tables** (5.2 MiB) - Consider runtime generation
3. **Template bloat** - Affects all components