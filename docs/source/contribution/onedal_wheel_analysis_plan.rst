.. Copyright 2024 contributors to the oneDAL project
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

:orphan:

Intel\ |reg| oneDAL PyPI Wheel Analysis Plan
===========================================

Overview
--------

The PyPI wheel ``daal-2025.8.0-py2.py3-none-manylinux_2_28_x86_64.whl`` is a 111 MiB archive
that expands to roughly 417 MiB of shared libraries inside ``daal-2025.8.0.data/data/lib``.
The payload is dominated by three large shared objects that ship the CPU, core runtime and
SYCL/DPC++ implementations. The table below captures the current size split to ground
subsequent investigations::

    File name                         Uncompressed size   Share of payload
    --------------------------------  ------------------  ----------------
    libonedal_dpc.so.3                297.89 MiB          71.44 %
    libonedal_core.so.3               108.74 MiB          26.08 %
    libonedal.so.3                      9.81 MiB           2.35 %
    libonedal_thread.so.3               0.23 MiB           0.05 %
    libonedal_parameters.so.3           0.13 MiB           0.03 %
    libonedal_parameters_dpc.so.3       0.16 MiB           0.04 %

Goals
-----

* Build an inventory of all assets shipped in the wheel, including metadata, license
  files and binary dependencies.
* Quantify how much each shared object contributes to the final wheel size at the
  archive level and within the uncompressed payload.
* Identify hot spots of duplicated code across the CPU (``libonedal_core.so.3``),
  dispatcher (``libonedal.so.3``) and GPU/SYCL (``libonedal_dpc.so.3``) binaries.
* Produce a component-level breakdown (by namespace, translation unit, section or
  symbol family) to explain where code and data volume originates.
* Capture dynamic dependencies that bring additional runtime requirements (for
  example ``libsycl.so.8`` or Intel oneAPI runtimes) to inform pruning strategies.

Phase 1 – Wheel Inventory and Baseline Metrics
----------------------------------------------

**Status:** Completed for ``daal==2025.8.0`` using ``dev/wheel_analysis/analyze_daal_wheel.py``
and captured in :doc:`onedal_wheel_analysis_report`.

1. **Completed** – Automate ``pip download daal --no-deps`` to archive the wheel alongside
   the ``.dist-info`` metadata for traceability.
2. **Completed** – Expand the archive under a deterministic location (``build/wheel_analysis``)
   and hash every file to make diffing new releases trivial.
3. **Completed** – Script ``du``/``stat`` reporting that captures:

   * Compressed wheel size vs. total uncompressed payload.
   * Per-file size contributions (as in the table above) and cumulative percentages.
   * Section sizes inside each ``.so`` using ``readelf --section-headers`` to
     separate ``.text``, ``.rodata``, ``.data`` and ``.bss`` without requiring
     Python-specific ELF tooling.
4. **Completed** – Parse ``METADATA``, ``WHEEL``, ``LICENSE.txt`` and ``RECORD`` to document
   licensing, versioning, and bundled third-party obligations.
5. **Completed** – Run ``auditwheel show`` and ``ldd`` to capture dynamic loader requirements,
   noting missing external runtimes (``libsycl``, ``libOpenCL``, ``libimf``, etc.).

Phase 2 – Section and Symbol-Level Attribution
----------------------------------------------

**Status:** In progress – dynamic section and symbol summaries are published; deeper static
attribution is queued to refine ownership. Device offload payload sizing is now
captured directly from the binaries.

1. **Completed** – Use ``readelf -SW`` to extract per-section sizes and flags, allowing
   separate accounting for executable text versus constant tables and template instantiations.
2. **Completed** – Collect dynamic symbol tables via ``nm -D --size-sort --radix=d`` with
   demangling and namespace aggregation using only binutils.
3. **Planned** – If debug symbols surface, rely on ``llvm-objdump -t`` combined with
   ``pyelftools`` scripts to attribute internal symbols to source directories using embedded
   ``.comment``/``.note`` metadata when available.
4. **Completed** – Cluster demangled names from the static ``.symtab`` to
   highlight heavy template instantiations (e.g., ``oneapi::mkl::gpu`` GEMM wrappers
   and ``.sycl_offloading`` bundles), record the heaviest local namespaces/functions, and
   track the extremely long kernel names that bloat ``.strtab``.
5. **Completed** – Detect ``__CLANG_OFFLOAD_BUNDLE__``/``.tgtimg``/``.tgtsym`` sections
   produced by the SYCL toolchain, extract their sizes with ``objcopy`` and
   report the resulting device-image and metadata footprint to quantify how much
   of ``libonedal_dpc.so.3`` is devoted to GPU kernels.
6. **Completed** – Decode the ``.tgtimg``/``.tgtsym`` tables to count individual
   SPIR-V kernels, demangle their names and aggregate sizes by namespace so the
   heaviest device families (e.g. MKL sparse GEMV blocks, DAL backend selectors
   and SYCL reduction wrappers) are called out explicitly.

Phase 3 – Cross-Library Deduplication Study
-------------------------------------------

**Status:** In progress – dynamic overlap metrics are captured; deeper binary comparisons are
scheduled to validate deduplication strategies.

1. **Completed** – Build sorted symbol lists for ``libonedal.so.3``, ``libonedal_core.so.3``
   and ``libonedal_dpc.so.3``. Use set operations to identify overlapping demangled names and
   flag common implementations that could be shared.
2. **Planned** – Leverage ``radiff2`` or ``llvm-objcopy --extract-subfile`` to compare
   identical sections or functions across CPU and GPU binaries, confirming whether
   duplication is byte-for-byte or independent builds of similar logic.
3. **Completed** – Cluster symbols by namespace/module (e.g. ``daal::algorithms`` vs.
   ``daal::services``) and use aggregated sizes to see which functional areas are duplicated
   across architectures. Overlap summaries now surface hot namespaces (``oneapi::dal::preview::spmd``,
   ``oneapi::dal::svm``, ``oneapi::dal::decision_forest``) alongside representative symbols.
4. **In progress** – Inspect ``libonedal.so.3``'s relocation tables and exported functions to
   confirm it mainly hosts dispatch logic into ``libonedal_dpc.so.3`` and ``libonedal_core.so.3``.
   Additional relocation review will document remaining unique code.
5. **Planned** – Profile the two small ``libonedal_parameters*.so.3`` libraries to document
   whether they only contain metadata structures that could be merged.

Phase 4 – Component-Level Attribution and Reporting
---------------------------------------------------

**Status:** Partially completed – namespace aggregation and reporting are in place; further
ownership mapping and visualisation remain open. Read-only versus writable data hot spots
are now captured from the static symbol tables to prioritise large constant payloads.

1. **In progress** – Map namespaces/algorithms to product features (e.g., linear models,
   clustering, decision forests) and sum symbol sizes to build a stacked breakdown per
   category. Initial aggregation for graph analytics, SVM and decision forest is available in
   the report, and the new read-only/writable object splits highlight VML constant tables,
   RNG polynomials and SYCL bundle metadata that dominate the data footprint.
2. **Planned** – Where debug info is missing, exploit ``--print-source-filenames`` (if
   available) or pattern-match mangled names to known source file naming conventions to
   estimate translation unit contributions.
3. **Completed** – Surface large ``.rodata``/``.data`` allocations directly from
   ``nm`` output, attributing the heaviest tables (e.g. VML polynomial datasets, SYCL
   image manifests, RNG state tables) to their namespaces so mitigation ideas can focus on
   concrete owners without additional disassembly passes.
4. **Completed** – Codify the above steps into reproducible Python scripts that emit JSON
   summaries (``analyze_daal_wheel.py``) enabling trend tracking across releases.
5. **Planned** – Generate charts (sunburst or stacked bar plots) from aggregated CSVs or JSON
   to communicate the weight of each component inside the wheel.

Phase 5 – Synthesis and Next Actions
------------------------------------

**Status:** Planned – will be revisited once deeper ownership and deduplication data is ready.

1. **In progress** – Assemble findings into a narrative covering package layout,
   duplication hotspots, and potential slimming levers. The current report documents the
   baseline and will be extended with remediation proposals.
2. **Planned** – Establish baselines so future wheels can be diffed quickly (size regression
   gates in CI, alerts when new sections exceed thresholds).
3. **Planned** – Feed results back to build/packaging owners with specific recommendations
   (e.g. enable LTO, share common runtime libraries, introduce symbol visibility annotations).

Immediate Data Already Collected
--------------------------------

* The wheel unpacks into six ``.so`` files totaling 416.95 MiB, with ``libonedal_dpc.so.3``
  alone accounting for more than 70 % of the payload.
* ``libonedal_dpc.so.3`` links against Intel oneAPI runtimes such as ``libsycl.so.8`` and
  OpenCL/Math Kernel Library components that are not bundled inside the wheel, implying a
  runtime dependency surface that also influences perceived footprint during deployment.
* Static symbol sweeps expose large read-only tables (e.g. ``_VAPI_COMMON_DATA_NAME`` at 1.2 MiB,
  ``_vsl_sfmt19937_poly`` at 128 KiB) and zero-initialised catalogues such as
  ``oneapi::mkl::gpu::gemm_catalog`` (512 KiB), providing concrete knobs for pruning constant
  datasets and RNG scaffolding across CPU and GPU binaries.
* ``libonedal_dpc.so.3`` and ``libonedal.so.3`` duplicate 3,260 exported symbols (~542 KiB in
  the SYCL binary and ~445 KiB in the dispatcher), primarily covering preview graph
  algorithms and the SPMD communication helpers. ``libonedal_dpc.so.3`` also dedicates
  72.0 MiB to SYCL device images (70.0 MiB of SPIR-V plus 2.0 MiB of metadata), giving a
  concrete split between host orchestration and GPU kernels for future reduction work.
* ``libonedal_dpc.so.3`` keeps 24.9 MiB of ``.strtab`` data and 8.5 MiB of ``.symtab`` metadata
  in addition to the 70.1 MiB SYCL device image bundle, signalling that symbol visibility and
  metadata trimming could yield meaningful savings.
* Forty exported entry points wrap ``oneapi::mkl`` primitives (``gesvd``, ``syevd``, ``syrk``),
  proving that MKL-backed routines are present even though the actual ``libmkl`` binaries ship
  outside the wheel.
* Static ``.symtab`` parsing shows 333,387 defined symbols in ``libonedal_dpc.so.3`` and
  124,922 in ``libonedal_core.so.3``. Local-only names account for ~56.6 MiB of the SYCL
  library's string table (versus 1.1 MiB for exported names), so visibility and debug stripping
  have clear room to reduce metadata.
* Symbol name lengths are extreme: the 99th percentile exceeds 1,000 characters and peaks at
  9,622 characters for SYCL reductions (``libonedal_dpc.so.3``) and 18,941 characters for
  decision tree kernels (``libonedal_core.so.3``), explaining the oversized ``.strtab``.
* Local namespace aggregation highlights ``.sycl_offloading`` blobs (~20 MiB),
  ``oneapi::mkl::gpu`` kernels (~18 MiB) and MKL sparse primitives as the dominant contributors
  to non-exported code in ``libonedal_dpc.so.3``. These clusters, alongside the
  ``oneapi::dal::preview::spmd`` duplication (~145 symbols, ~120 KiB), are prime reduction targets.

These baselines anchor the deeper investigation steps described above.

Immediate next actions
----------------------

* Prototype symbol-visibility and ``strip --strip-debug`` experiments using the new
  static-symbol metrics to estimate how much of the ~56.6 MiB local string-table payload in
  ``libonedal_dpc.so.3`` can be reclaimed without breaking consumers.
* Use the namespace overlap data to target ``oneapi::dal::preview::spmd`` and SVM/decision-forest
  wrappers for consolidation so the dispatcher stops duplicating ~445 KiB of SYCL exports.
* Trace the MKL-backed entry points and the large ``oneapi::mkl::gpu`` local kernels to their build
  definitions to decide whether they should live in a dedicated runtime package instead of the
  core wheel.
* Extend the SYCL kernel sweep to correlate the property-set arrays (``__sycl_offload_prop_sets``)
  with the heavy SPIR-V families so runtime features (e.g. specialization constants, reductions)
  can be trimmed alongside the code payload.

The first execution of this plan against ``daal==2025.8.0`` is documented in
:doc:`onedal_wheel_analysis_report`, which explains how to regenerate the JSON
artefacts for further exploration without checking them into the repository.
