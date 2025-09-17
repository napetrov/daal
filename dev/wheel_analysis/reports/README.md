# oneDAL Wheel Analysis Reports

This directory contains analysis reports generated from the oneDAL binary wheel analysis tools.

## Reports

### 1. [Executive Action Summary](executive_action_summary.md)
Quick wins and decision guide for immediate actions. Start here for:
- Immediate savings opportunities (44.2 MiB)
- Multi-wheel strategy recommendations
- Priority timeline

### 2. [Detailed Kernel and MKL Analysis](detailed_kernel_and_mkl_analysis.md)
Technical deep-dive into SYCL kernels and MKL usage:
- 6,683 SYCL kernels categorized by type
- MKL function usage mapped to algorithms
- Build optimization experiments

### 3. [Comprehensive Optimization Strategy](comprehensive_optimization_strategy.md)
Full implementation roadmap including:
- Phased approach with ABI compatibility notes
- Deployment scenarios (laptop, cloud, HPC)
- Risk assessment and success metrics

### 4. [Symbol Overlap Analysis](symbol_overlap_analysis.md)
Cross-library duplication analysis:
- 3,260 shared symbols between libraries
- Consolidation opportunities
- Architecture recommendations

### 5. [Library Content Deep Dive](library_content_deep_dive.md)
Detailed breakdown of what's inside each library:
- libonedal_dpc.so.3: Only 24% is GPU kernels, 52% is host code
- libonedal_core.so.3: Multiple splitting strategies analyzed
- Read-only data analysis (math tables, RNG data)

### 6. [Visual Library Breakdown](visual_library_breakdown.md)
Visual representation of library contents:
- ASCII diagrams showing size distributions
- Proposed modular split options
- Memory footprint comparisons

### 7. [PR Response and Next Steps](pr_response_and_next_steps.md)
Response to PR #78 comments and completion status:
- Summary of completed SYCL kernel analysis
- Remaining analysis steps
- Implementation recommendations

### 8. [Property Set Correlation Approach](property_set_correlation_approach.md)
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

- **Total wheel size**: 417 MiB uncompressed (106 MiB compressed)
- **Immediate savings**: 44.2 MiB through debug stripping and build opts
- **Laptop optimization**: CPU-only variant saves 307 MiB (73% reduction)
- **SYCL kernels**: 70 MiB across 6,683 kernels (only 24% of libonedal_dpc.so.3)
- **Symbol duplication**: ~1 MiB between dispatcher and DPC++ library
- **libonedal_dpc.so.3 breakdown**: 52% host code, 24% device kernels, 24% overhead
- **libonedal_core.so.3 content**: Tree algorithms (10.3 MiB), services (3.5 MiB), clustering (2.9 MiB)

## Next Steps

1. **Immediate**: Implement debug symbol stripping (30-40 MiB savings)
2. **Short-term**: Create CPU-only wheel for laptops (110 MiB total size)
3. **Medium-term**: Optimize SYCL kernel generation (15-20 MiB savings)
4. **Long-term**: Architecture refactoring for next major release

See the individual reports for detailed recommendations and implementation guidance.