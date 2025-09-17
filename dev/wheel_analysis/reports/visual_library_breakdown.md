# Visual Library Content Breakdown

## libonedal_dpc.so.3 (297.89 MiB) - What's Inside?

```
┌─────────────────────────────────────────────────────────────┐
│                    libonedal_dpc.so.3                       │
│                      297.89 MiB                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────┐  52.3%               │
│  │      Host Code (.text)          │  155.7 MiB           │
│  │  • SYCL Runtime      40 MiB     │                      │
│  │  • Algorithm Host    70 MiB     │                      │
│  │  • Templates         30 MiB     │                      │
│  │  • MKL Integration   15 MiB     │                      │
│  └─────────────────────────────────┘                      │
│                                                             │
│  ┌─────────────────────────────────┐  24.2%               │
│  │    SYCL Device Kernels          │  72.0 MiB            │
│  │  • SPIR-V Images    70.1 MiB    │                      │
│  │  • Kernel Metadata   1.9 MiB    │                      │
│  └─────────────────────────────────┘                      │
│                                                             │
│  ┌─────────────────────────────────┐  11.5%               │
│  │     Symbol Metadata             │  34.3 MiB            │
│  │  • Symbol Names     24.9 MiB    │                      │
│  │  • Symbol Tables     9.4 MiB    │                      │
│  └─────────────────────────────────┘                      │
│                                                             │
│  ┌─────────────────────────────────┐  12.0%               │
│  │         Other                   │  35.9 MiB            │
│  │  • Read-only Data   15.6 MiB    │                      │
│  │  • Debug/Exception   7.9 MiB    │                      │
│  │  • Linking           7.8 MiB    │                      │
│  │  • Writable Data     5.2 MiB    │                      │
│  └─────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘

Key Insight: Only 24% is actual GPU kernels!
             52% is CPU-side code (host orchestration)
             24% is overhead (symbols, metadata, linking)
```

## libonedal_core.so.3 (108.74 MiB) - Algorithm Distribution

```
┌─────────────────────────────────────────────────────────────┐
│                    libonedal_core.so.3                      │
│                      108.74 MiB                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Algorithm Code Distribution (72.28 MiB total)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  Tree-Based ████████████ 10.3 MiB                  │  │
│  │  - GBT (5.0)  - Random Forest (2.5)  - DTree (1.1) │  │
│  │                                                      │  │
│  │  Services   ████████ 3.5 MiB                       │  │
│  │  - Memory mgmt, threading, data structures          │  │
│  │                                                      │  │
│  │  Clustering ██████ 2.9 MiB                         │  │
│  │  - K-Means (2.0)  - DBSCAN (0.9)                   │  │
│  │                                                      │  │
│  │  Linear     █████ 2.5 MiB                          │  │
│  │  - PCA (0.6)  - LinReg (0.4)  - SVD (0.4)         │  │
│  │                                                      │  │
│  │  Statistics ████ 1.7 MiB                           │  │
│  │  - Moments (1.0)  - Covariance (0.7)               │  │
│  │                                                      │  │
│  │  SVM        ██ 1.1 MiB                             │  │
│  │  - Kernel functions, SMO solver                     │  │
│  │                                                      │  │
│  │  Other Algorithms ████████████████ 15.2 MiB         │  │
│  │  - Neural nets, optimization, neighbors, etc.       │  │
│  │                                                      │  │
│  │  Core Infrastructure ██████████████████████ 35 MiB  │  │
│  │  - Base classes, utilities, common code             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Data Sections (36.46 MiB total)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Read-only Data  ████████████ 17.3 MiB              │  │
│  │  - Math tables (5.2)  - RNG data (3.1)              │  │
│  │  - Algorithm constants (8.9)                         │  │
│  │                                                      │  │
│  │  Metadata       ███████████ 17.9 MiB                │  │
│  │  - Symbols, relocations, debug info                  │  │
│  │                                                      │  │
│  │  Writable       █ 1.3 MiB                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Split Options for libonedal_core.so.3

### Option 1: Essential vs Full
```
┌─────────────────┐     ┌──────────────────────────┐
│ libonedal_lite  │     │    libonedal_full        │
│    25 MiB       │     │      108.74 MiB          │
├─────────────────┤     ├──────────────────────────┤
│ • K-Means       │     │ • Everything             │
│ • Linear Reg    │     │ • All algorithms         │
│ • PCA           │     │ • All optimizations      │
│ • Basic Stats   │     │ • All data types         │
│ • Core only     │     │                          │
└─────────────────┘     └──────────────────────────┘
```

### Option 2: Modular Components
```
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ libonedal_tree │ │libonedal_linear│ │libonedal_cluster
│    10.3 MiB    │ │    2.5 MiB     │ │    2.9 MiB     │
├────────────────┤ ├────────────────┤ ├────────────────┤
│ • GBT          │ │ • PCA          │ │ • K-Means      │
│ • Random Forest│ │ • Linear Reg   │ │ • DBSCAN       │
│ • Decision Tree│ │ • Ridge/Lasso  │ │ • Clustering   │
└────────────────┘ └────────────────┘ └────────────────┘

┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ libonedal_ml   │ │ libonedal_stat │ │ libonedal_core │
│    5.2 MiB     │ │    3.5 MiB     │ │    40 MiB      │
├────────────────┤ ├────────────────┤ ├────────────────┤
│ • SVM          │ │ • Statistics   │ │ • Services     │
│ • Neural Nets  │ │ • Covariance   │ │ • Memory mgmt  │
│ • Optimization │ │ • Quantiles    │ │ • Base classes │
└────────────────┘ └────────────────┘ └────────────────┘
```

### Option 3: Use-case Based
```
Data Scientist Package (45 MiB):
├── Trees (RF, GBT) 
├── Linear models
├── Clustering
├── Basic stats
└── Core services

ML Engineer Package (75 MiB):
├── Everything in DS package +
├── SVM
├── Neural Networks
├── Advanced optimization
└── Extended services

Enterprise Package (108.74 MiB):
├── Complete functionality
├── All algorithms
├── All optimizations
└── Debug capabilities
```

## Memory Footprint Comparison

```
Current Deployment:
┌────────────────────────────────────┐
│         Total: 417 MiB             │
├────────────────────────────────────┤
│ libonedal_dpc.so.3    298 MiB     │
│ libonedal_core.so.3   109 MiB     │
│ libonedal.so.3         10 MiB     │
└────────────────────────────────────┘

Optimized Laptop Deployment:
┌────────────────────────────────────┐
│         Total: 35 MiB              │
├────────────────────────────────────┤
│ libonedal_lite.so      25 MiB     │
│ libonedal_thread.so     1 MiB     │
│ Dependencies           9 MiB       │
└────────────────────────────────────┘

Savings: 382 MiB (91.6% reduction!)
```

## Key Recommendations

1. **For Laptops**: Ship modular CPU-only libraries
   - Start with essential algorithms (25-35 MiB)
   - Add components as needed

2. **For Cloud/Server**: Keep monolithic for performance
   - Full 417 MiB package acceptable
   - Optimize build flags instead

3. **For Edge Devices**: Custom minimal builds
   - Single algorithm libraries (2-10 MiB each)
   - Strip all unnecessary features

4. **Universal Strategy**: 
   - Default to "libonedal_lite" (25 MiB)
   - Auto-download additional components on demand
   - Cache downloaded components