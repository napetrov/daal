# Symbol Overlap Analysis for oneDAL Binary Consolidation

## Executive Summary

The binary analysis reveals significant symbol duplication between `libonedal_dpc.so.3` and `libonedal.so.3`, with 3,260 shared symbols totaling approximately 987 KiB of redundant code. This duplication represents 98% of the dispatcher library's exported symbol size, suggesting substantial opportunities for consolidation.

## Key Findings

### 1. Major Overlap: libonedal_dpc.so.3 ↔ libonedal.so.3

**3,260 shared symbols** representing:
- ~542 KiB in libonedal_dpc.so.3 (43% of its dynamic symbol surface)
- ~445 KiB in libonedal.so.3 (98% of its dynamic symbol surface)

#### Top Duplicate Namespaces:
1. **oneapi::dal::preview::spmd** (145 symbols, ~120 KiB total)
   - SPMD communication helpers (bcast, sendrecv_replace families)
   - Appears to be full implementation duplicated in both libraries

2. **oneapi::dal::svm** (288 symbols, ~58 KiB total)
   - Support Vector Machine implementations
   - Full algorithm bodies present in dispatcher

3. **oneapi::dal::decision_forest::detail** (234 symbols, ~55 KiB total)
   - Decision forest internal implementations
   - Complete algorithm logic duplicated

4. **oneapi::dal::preview graph algorithms** (~50 KiB)
   - Connected components, triangle counting, Jaccard similarity
   - Full host orchestration in both libraries

### 2. Minimal Cross-Architecture Overlap

- libonedal_dpc.so.3 ↔ libonedal_core.so.3: Only 2 shared symbols
- Indicates mostly disjoint CPU vs GPU code paths
- Good separation of concerns between architectures

### 3. Parameter Library Duplication

- 91 shared symbols between parameter libraries
- Mainly decision forest, PCA, and linear regression parameters
- Small size impact (~10 KiB total) but architectural inconsistency

## Consolidation Opportunities

### Immediate Actions (High Impact)

1. **Centralize SPMD Communication Layer**
   - Move oneapi::dal::preview::spmd to a single library
   - Potential savings: ~120 KiB
   - Impact: Reduces duplication without affecting API

2. **Consolidate Preview Algorithms**
   - Graph algorithms (connected components, triangle counting)
   - Currently full implementations in both libraries
   - Potential savings: ~50 KiB

3. **Dispatcher Refactoring**
   - Convert libonedal.so.3 to true thin forwarding layer
   - Move algorithm implementations to backend libraries
   - Potential savings: ~400 KiB (most of dispatcher size)

### Medium-term Actions

4. **Visibility Annotations**
   - Mark internal symbols as hidden visibility
   - The analysis shows 328,515 local symbols in libonedal_dpc.so.3
   - Local symbols consume 56.6 MiB of string table
   - Potential metadata savings: 30-40 MiB

5. **Template Instantiation Control**  
   - Review duplicate template instantiations across libraries
   - Explicit instantiation in single translation unit
   - Focus on high-frequency templates (chunked_array, SPMD communicator)

## Build System Insights

The analysis revealed key SYCL compilation settings:
- `-fsycl-device-code-split=per_kernel`: Creates separate device code for each kernel
- This contributes to the 6,683 individual SYCL kernels in libonedal_dpc.so.3
- Consider experimenting with different code split strategies for size reduction

## Recommendations

1. **Phase 1**: Consolidate preview namespace and SPMD layer
   - Low risk, high impact
   - Clear ownership boundaries
   - Estimated reduction: 150-200 KiB

2. **Phase 2**: Refactor dispatcher architecture  
   - Higher complexity but larger gains
   - Estimated reduction: 300-400 KiB

3. **Phase 3**: Symbol visibility and metadata optimization
   - Requires comprehensive testing
   - Potential for 30+ MiB reduction in metadata

4. **Future Work**: Kernel consolidation
   - Analyze the 6,683 SYCL kernels for duplication
   - Correlate with property sets as mentioned in PR
   - Focus on MKL wrapper kernels (identified as heavy consumers)

## Technical Details for Implementation

### SPMD Consolidation Approach
```cpp
// Current: Duplicate implementations
// libonedal.so.3: Full implementation
// libonedal_dpc.so.3: Same full implementation

// Proposed: Single implementation with forwarding
// libonedal_common.so.3: Full SPMD implementation  
// libonedal.so.3: Forward to common
// libonedal_dpc.so.3: Forward to common
```

### Visibility Control Example
```cpp
// Add to internal headers
#define ONEDAL_INTERNAL __attribute__((visibility("hidden")))

// Apply to internal symbols
namespace detail {
    ONEDAL_INTERNAL void internal_function();
}
```