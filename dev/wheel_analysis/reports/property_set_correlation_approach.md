# SYCL Property Set Correlation Approach (Future Work)

## Overview

Property sets in SYCL control kernel behavior through specialization constants, work-group sizes, and other runtime parameters. Correlating these with heavy kernels could reveal optimization opportunities.

## Current State

The SYCL kernel analysis has successfully identified:
- 6,683 individual kernels in libonedal_dpc.so.3
- Kernel sizes ranging from 512 bytes to 628.6 KiB
- Heavy kernel families consuming significant space

However, the property sets that control these kernels are not yet analyzed.

## Proposed Approach

### 1. Property Set Extraction

SYCL property sets are typically embedded in the binary as metadata associated with each kernel. They may include:
- **Specialization constants**: Runtime-configurable values
- **Work-group size hints**: Optimization parameters
- **Required features**: Hardware capabilities needed
- **Reduction operations**: Special handling for reductions

### 2. Correlation Methodology

```python
def correlate_properties_with_kernels(binary_path):
    """
    Future implementation to correlate property sets with kernels.
    """
    # Step 1: Extract kernel information (already done)
    kernels = extract_kernel_info(binary_path)  # .tgtimg/.tgtsym
    
    # Step 2: Find property metadata sections
    # These might be in:
    # - ELF notes sections
    # - Custom SYCL sections
    # - Embedded in the SPIR-V modules themselves
    
    # Step 3: Parse property descriptors
    # Property sets likely contain:
    # - Kernel ID/name reference
    # - List of specialization constants
    # - Default values
    # - Type information
    
    # Step 4: Build correlation map
    correlation = {}
    for kernel in kernels:
        properties = find_properties_for_kernel(kernel.name)
        correlation[kernel.name] = {
            'size': kernel.size,
            'properties': properties,
            'optimization_potential': estimate_savings(properties)
        }
    
    return correlation
```

### 3. Optimization Opportunities

Once correlated, we could identify:

#### Specialization Constant Reduction
- Kernels with many specialization constants could be simplified
- Constants with fixed values could be compiled in
- Estimated savings: 5-10% of kernel size

#### Work-group Size Consolidation
- Multiple kernels with similar work-group requirements could share code
- Dynamic work-group sizing adds overhead
- Estimated savings: 10-15% for affected kernels

#### Feature Requirement Analysis
- Kernels requiring specific hardware features
- Could create targeted builds for different hardware
- Enable feature-based kernel selection

### 4. Implementation Challenges

1. **Binary Format**: SYCL property format is implementation-specific
2. **Tool Support**: May need Intel SYCL tools or custom parsers
3. **Documentation**: Limited public documentation on property set format

## Example Analysis (Hypothetical)

Based on the heavy kernel families identified:

```yaml
oneapi::dal::backend::primitives::kernel_select_heap:
  total_size: 3.50 MiB
  kernel_count: 96
  potential_properties:
    - work_group_size: [256, 512, 1024]
    - specialization_constants:
        - data_type: [float, double]
        - k_value: [1, 5, 10, 50, 100]
    - optimization_potential: 
        - fixed_k_variants: 0.5 MiB savings
        - single_precision_only: 1.5 MiB savings

oneapi::mkl::gpu::l2_ker_buf:
  total_size: 2.52 MiB
  kernel_count: 288
  potential_properties:
    - matrix_layout: [row_major, col_major]
    - transpose_flags: [N, T, C]
    - optimization_potential:
        - layout_specific_kernels: 0.8 MiB savings
```

## Recommended Next Steps

1. **Research Phase**:
   - Contact Intel SYCL team for property set documentation
   - Study SYCL runtime source if available
   - Analyze SPIR-V modules for embedded metadata

2. **Prototype Phase**:
   - Build property set parser
   - Create correlation tool
   - Test on small subset of kernels

3. **Integration Phase**:
   - Add to analyze_daal_wheel.py
   - Generate property correlation reports
   - Identify optimization candidates

## Expected Outcomes

- 10-20% reduction in heavy kernel families (5-10 MiB)
- Better understanding of kernel specialization overhead
- Targeted optimization strategies per algorithm
- Foundation for build-time kernel selection

## Priority

While valuable, this work requires:
- Deep SYCL runtime knowledge
- Potentially proprietary format documentation
- Significant development effort

Therefore, it's appropriately placed in "Future optimization opportunities" after the immediate wins of:
1. Debug symbol stripping (30-40 MiB)
2. CPU-only variants (307 MiB for laptops)
3. Build optimizations (5-10%)

The property set analysis would be most valuable after these easier wins are captured.