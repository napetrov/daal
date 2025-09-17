# oneDAL Wheel Analysis Reports

This directory contains analysis reports generated from the oneDAL binary wheel analysis tools.

## Reports (Consolidated)

### 1. [CPU Libraries Analysis](cpu_libraries_analysis.md)
Comprehensive analysis of CPU-only deployment:
- Total size: 119 MiB (well-optimized)
- Algorithm distribution and size breakdown
- MKL integration (statically linked)
- Optimization opportunities and deployment options

### 2. [GPU Libraries Analysis](gpu_libraries_analysis.md)
Detailed analysis of GPU deployment:
- Additional size: 298 MiB (on top of CPU)
- Critical finding: Only 24% is actual GPU kernels
- Host code analysis (52% of library)
- MKL GPU kernel breakdown
- Immediate wins: 34-44 MiB through build optimizations

### 3. [Symbol Overlap Analysis](symbol_overlap_analysis.md)
Cross-library duplication analysis:
- 3,260 shared symbols between libraries
- Consolidation opportunities
- Architecture recommendations

### 4. [PR Response and Next Steps](pr_response_and_next_steps.md)
Response to PR #78 comments and completion status:
- Summary of completed SYCL kernel analysis
- Remaining analysis steps
- Implementation recommendations

### 5. [MKL Usage Summary](mkl_usage_summary.md)
Analysis of MKL integration:
- CPU: Optimally integrated (statically linked)
- GPU: 17.85 MiB of kernels, 4.2 MiB removable verbose/debug
- No unused MKL routines found

### 6. [Property Set Correlation Approach](property_set_correlation_approach.md)
Future work documentation:
- Approach for correlating SYCL property sets with kernels
- Expected optimization opportunities
- Implementation challenges and recommendations

## How These Reports Were Generated

1. Run the wheel analysis:
   ```bash
   python3 dev/wheel_analysis/analyze_daal_wheel.py --output-dir build/wheel_analysis
   ```

2. The analysis includes:
   - SYCL kernel extraction from .tgtimg/.tgtsym sections
   - Symbol overlap detection between libraries
   - MKL dependency analysis
   - Size profiling by component

3. Generate summary:
   ```bash
   python3 dev/wheel_analysis/render_summary.py --analysis-dir build/wheel_analysis/analysis
   ```

4. Check for size regression (for CI):
   ```bash
   # Save current as baseline
   python3 dev/wheel_analysis/check_size_regression.py --save-baseline
   
   # Check against baseline
   python3 dev/wheel_analysis/check_size_regression.py --baseline size_baseline.json --max-growth 5%
   ```

## Key Findings

### CPU vs GPU Deployments
- **CPU-only**: 119 MiB (all algorithms, MKL statically linked)
- **CPU+GPU**: 417 MiB (+298 MiB for GPU support)
- **GPU library breakdown**: 52% host code, 24% device kernels, 24% overhead

### Optimization Opportunities
- **Immediate savings**: 34-44 MiB (strip debug, remove MKL verbose, optimize build)
- **Medium-term**: 25-40 MiB (reduce templates, fix duplicates)
- **Long-term**: 65-90 MiB (architecture refactoring)
- **Total potential**: 124-174 MiB reduction for GPU deployment

### MKL Integration
- **CPU**: MKL statically linked, no external dependencies
- **GPU**: Additional MKL GPU kernels (17.85 MiB)
- **Removable**: MKL verbose/debug kernels (4.2 MiB) in GPU library

## Enabling Debug Symbols

### For C++ Users
```bash
# Build with debug symbols
make REQDBG=yes ONEDAL_USE_DPCPP=yes

# Or keep symbols separate
objcopy --only-keep-debug libonedal_dpc.so.3 libonedal_dpc.so.3.debug
strip --strip-debug libonedal_dpc.so.3
```

### For Python Users
```bash
# Environment variable (proposed)
export ONEDAL_ENABLE_DEBUG_SYMBOLS=1

# Or future debug wheel
pip install daal[debug]
```

## Next Steps

1. **Immediate**: Strip debug symbols and remove MKL verbose (38-44 MiB)
2. **Short-term**: Optimize build flags and templates (35-45 MiB)
3. **Medium-term**: Create CPU vs CPU+GPU deployment options
4. **Long-term**: Architecture split for modular deployment

See the individual reports for detailed implementation guidance.