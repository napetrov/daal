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

Intel\ |reg| oneDAL PyPI Wheel Analysis Report
==============================================

This document captures the first execution of the
:doc:`onedal_wheel_analysis_plan` for the ``daal==2025.8.0`` PyPI wheel. The
pipeline is automated by ``dev/wheel_analysis/analyze_daal_wheel.py`` which
fetches the wheel, unpacks it under ``build/wheel_analysis`` and exports JSON
summaries into ``build/wheel_analysis/analysis`` for reuse. The analysis
artefacts are ignored by git so the repository only carries the scripts and the
written summary.

To regenerate the artefacts, run::

   python3 dev/wheel_analysis/analyze_daal_wheel.py --output-dir build/wheel_analysis

For a quick Markdown recap of the captured metrics, use::

   python3 dev/wheel_analysis/render_summary.py --analysis-dir build/wheel_analysis/analysis

Redirecting the output to ``build/wheel_analysis/analysis/summary.md`` keeps a
shareable snapshot without committing artefacts to git.

All numbers below originate from a local run of the script (``daal==2025.8.0``)
with artefacts stored under ``build/wheel_analysis/analysis``.

Wheel footprint
---------------

The wheel expands from a 106.1 MiB archive to 417.0 MiB of uncompressed
payload. ``libonedal_dpc.so.3`` carries more than 70 % of the footprint, while
the dispatcher and parameter libraries are comparatively small.

.. csv-table:: ``daal==2025.8.0`` shared object sizes
   :header: "Shared object","Size (MiB)","Share of payload (%)"
   :widths: 45, 20, 20

   ``libonedal_dpc.so.3``,"297.89","71.44"
   ``libonedal_core.so.3``,"108.74","26.08"
   ``libonedal.so.3``,"9.81","2.35"
   ``libonedal_thread.so.3``,"0.23","0.05"
   ``libonedal_parameters_dpc.so.3``,"0.16","0.04"
   ``libonedal_parameters.so.3``,"0.13","0.03"

Section breakdown
-----------------

``libonedal_dpc.so.3`` packages 155.6 MiB of executable text, 102.3 MiB of
read-only data and 72.0 MiB of SYCL offload payload (70.0 MiB of SPIR-V images
plus 2.0 MiB of kernel metadata across ``.tgtsym``/``.tgtimg``). The CPU binary
remains text-heavy but avoids any offload bundles.

.. csv-table:: Major sections per shared object (MiB)
   :header: "Shared object","Text","RO data","RW data","BSS","Device payload","Device sections"
   :widths: 30, 13, 13, 13, 13, 14, 32

   ``libonedal_dpc.so.3``,"155.64","102.32","4.63","0.72","72.01","``__CLANG_OFFLOAD_BUNDLE__sycl-spir64``; ``.tgtsym``; ``.tgtimg``"
   ``libonedal_core.so.3``,"72.28","17.27","1.23","0.11","0.00","-"
   ``libonedal.so.3``,"4.72","2.32","0.53","0.05","0.00","-"
   ``libonedal_thread.so.3``,"0.09","0.07","0.00","0.00","0.00","-"
   ``libonedal_parameters_dpc.so.3``,"0.04","0.06","0.00","0.00","0.00","``__CLANG_OFFLOAD_BUNDLE__sycl-spir64``; ``.tgtimg``"
   ``libonedal_parameters.so.3``,"0.03","0.04","0.00","0.00","0.00","-"

Dynamic symbol inventory
------------------------

Dynamic symbol tables expose the surface area carried by each binary. The CPU
payload exports 13,344 mangled symbols, led by algorithms such as PCA, AdaBoost
and the optimisation solvers. ``libonedal_dpc.so.3`` exports 4,872 symbols that
cluster around SYCL primitives, data-parallel kernels and decision forest
routines. The dispatcher (``libonedal.so.3``) still exposes 3,670 entry points,
primarily forwarding into the oneAPI namespace.

Top namespaces by cumulative symbol size:

* ``libonedal_core.so.3`` – ``daal::algorithms::pca`` (435 KiB),
  ``daal::algorithms::kdtree_knn_classification`` (373 KiB) and
  ``daal::algorithms::adaboost`` (369 KiB) dominate the CPU surface.
* ``libonedal_dpc.so.3`` – SYCL queue primitives (175 KiB), data-parallel backend
  helpers (110 KiB) and ``oneapi::dal::decision_forest`` (106 KiB) represent the
  heaviest exported kernels.
* ``libonedal.so.3`` – dispatcher exports concentrate on
  ``oneapi::dal::svm`` (58 KiB), ``oneapi::dal::decision_forest`` (49 KiB) and
  ``oneapi::dal::knn`` entry points, confirming the thin forwarding layer.

Static metadata overhead
------------------------

Parsing the static ``.symtab`` uncovers 333,387 defined symbols inside
``libonedal_dpc.so.3`` (328,515 of them local). Local-only names consume about
56.6 MiB of that library's string table whereas exported names add only 1.1 MiB.
Name lengths are extreme: the 99th percentile exceeds 1,000 characters and the
longest SYCL kernel name stretches to 9,622 characters. ``libonedal_core.so.3``
contributes another 124,922 defined symbols (111,580 local) and 29.9 MiB of
local string-table entries, with decision tree kernels topping out at 18,941
characters per name. Even the dispatcher retains 12,696 local symbols and 1.9
MiB of string data despite exporting only 3,670 entry points. The bulk of the
metadata therefore originates from templated internals rather than the exported
API surface.

Local namespace hot spots
-------------------------

The static tables highlight where non-exported code accumulates. In
``libonedal_dpc.so.3`` the heaviest namespaces are the SYCL offload blobs
(``.sycl_offloading`` – ~20 MiB) and ``oneapi::mkl::gpu`` kernels (~18 MiB),
followed by MKL sparse primitives and SYCL runtime helpers. Large local
functions include ``mkl_blas_avx512_gemm_s8u8s32_copy_down32_eb`` (≈737 KiB) and
the sparse GEMM shims (~350 KiB each), underscoring how much MKL glue lives in
the GPU binary. On the CPU side, ``void daal::algorithms::gbt`` (~5.1 MiB) and
``daal::services::interface1`` (~3.2 MiB) dominate the local footprint, while
``libonedal.so.3`` keeps MKL RNG helpers around 39 KiB apiece even though those
symbols never escape the dispatcher.

Constant data pressure
----------------------

Tracking ``nm`` storage classes surfaces the read-only tables that swell each
binary:

* ``libonedal_dpc.so.3`` dedicates more than 80 MiB of static ``.rodata`` to
  ``.sycl_offloading.*`` bundles, with individual entries surpassing 600 KiB
  apiece, alongside 0.5 MiB ``oneapi::mkl::gpu::gemm_catalog`` and 52 KiB
  ``trsm_catalog`` arrays in ``.bss``. The writable side also reveals the
  0.5 MiB ``.sycl_offloading.device_images`` descriptor and a shared ``mm_book``
  allocator map (64.5 KiB).
* ``libonedal_core.so.3`` exposes VML constant datasets including
  ``_VAPI_COMMON_DATA_NAME`` (~1.2 MiB), ``vdpowx_data`` (~372 KiB) and
  ``vdcdfnorminv_data_avx512`` (~371 KiB). RNG metadata is duplicated via the
  ``_vsl_mt2203_table`` (~71 KiB) table, while ``mm_book`` and
  ``mkl_vsl_sub_kernel_z0_*`` (28 KiB) highlight writable RNG scaffolding.
* ``libonedal.so.3`` keeps a leaner 0.37 MiB of ``.rodata``, but half of that is
  consumed by RNG polynomials such as ``_vsl_sfmt19937_poly`` (~131 KiB) and the
  shared ``_vsl_mt2203_table`` (~71 KiB). Its writable payload mirrors the CPU
  binary, carrying another ``mm_book`` map plus four 28 KiB VSL kernels.

These findings single out reusable catalogues and RNG tables as prime targets
for deduplication or runtime generation in addition to the previously observed
template-heavy code.

Cross-library duplication
-------------------------

Symbol intersections highlight how much code is shared between binaries:

* ``libonedal_dpc.so.3`` and ``libonedal.so.3`` expose 3,260 common exported
  symbols. The duplicates add up to roughly 542 KiB of the SYCL binary's
  exported text (43 % of its dynamic symbol surface) and 445 KiB inside the
  dispatcher (98 % of that library's exported symbol size). Most of the shared
  names belong to the SPMD communication helpers (``communicator<...>::bcast``
  and ``sendrecv_replace`` families) and preview graph algorithms such as
  connected components, triangle counting and Jaccard similarity, confirming
  that both libraries ship full host orchestrations for these workloads.
  Namespace aggregation shows ``oneapi::dal::preview::spmd`` (~145 symbols,
  ~120 KiB), ``oneapi::dal::svm`` (~58 KiB) and
  ``oneapi::dal::decision_forest::detail`` (~55 KiB) as the dominant overlap
  clusters, providing concrete targets for consolidation.
* Only two exported symbols overlap between ``libonedal_dpc.so.3`` and the CPU
  binary, pointing to mostly disjoint code generation paths.
* ``libonedal_parameters_{dpc,}`` share 91 dynamic symbols that encode parameter
  objects for PCA, covariance and decision forest components.

Deep dive: dispatcher vs SYCL binary
------------------------------------

``libonedal_dpc.so.3``
~~~~~~~~~~~~~~~~~~~~~~

* The library holds 155.6 MiB of ``.text`` alongside a 70.1 MiB
  ``__CLANG_OFFLOAD_BUNDLE__`` section that packages the SPIR-V device images
  for SYCL kernels. Metadata also weighs heavily: ``.strtab`` contributes
  24.9 MiB and ``.symtab`` accounts for 8.5 MiB of additional payload.
* Exported symbol weight concentrates on SYCL primitives (``sycl::_V1::event`` –
  175 KiB), preview namespace graph analytics (``oneapi::dal::preview`` –
  130 KiB) and the backend primitives (110 KiB). Decision forest, k-NN and SVM
  front-ends each contribute between 75 KiB and 108 KiB of exported text.
* The heaviest individual exports are radix-sort kernels and index shuffles
  (9–10 KiB each), followed by graph workloads such as Afforest connected
  components (6.3 KiB) and SPMD collectives. This highlights template
  instantiations in the data-parallel primitives as a prime reduction target.
* Forty exported entry points wrap ``oneapi::mkl`` primitives (``gesvd``,
  ``syevd``, ``syrk`` variants, ~1 KiB apiece), so the wheel relies on the
  external oneAPI Math Kernel Library at runtime even though the binaries ship
  the orchestration layer.

``libonedal.so.3``
~~~~~~~~~~~~~~~~~~

* The dispatcher carries 4.69 MiB of ``.text`` with an additional 1.0 MiB of
  string tables (``.strtab`` + ``.dynstr``) and 0.49 MiB of ``.rodata``.
  Its metadata footprint is therefore comparable to the executable surface.
* Namespace aggregation shows ``oneapi::dal::svm`` (57.7 KiB),
  ``oneapi::dal::preview`` (53.9 KiB) and ``oneapi::dal::decision_forest``
  (49.1 KiB) dominating the exported surface. The largest functions are chunked
  array helpers, triangle counting orchestrators and CSV prefix-sum utilities,
  each around 1–2 KiB, reinforcing that the dispatcher keeps full algorithm
  bodies rather than thin trampolines.
* Because 98 % of the export size overlaps with ``libonedal_dpc.so.3``, any
  reduction strategy should examine whether these preview graph algorithms and
  SPMD helpers can be centralised in a single binary or downgraded to hidden
  visibility to avoid paying the cost twice.

ELF metadata primer
-------------------

* ``.symtab`` is the full static symbol table emitted by the linker. It lists
  every function, object and section-local symbol (including those not exported
  at runtime) so that static linkers, debuggers and post-link tools can resolve
  references. Because each entry is 24 bytes on ELF64 and ``libonedal_dpc.so.3``
  carries 365,439 of them, the section alone weighs 8.4 MiB even though it is
  not required when the library is loaded.
* ``.strtab`` is the companion string table that holds the textual names used by
  ``.symtab``. Each symbol name is null-terminated and stored once in
  ``.strtab``; symbol table entries point at their offset. For the SYCL binary
  this adds 24.9 MiB of metadata because the device compiler instantiates many
  long, templated kernel names.

SYCL device image bundles
-------------------------

The SYCL toolchain emits device kernels into
``__CLANG_OFFLOAD_BUNDLE__sycl-spir64`` sections. Each bundle contains a
sequence of SPIR-V modules (the binary begins with the ``0x07230203`` SPIR-V
magic) and is accompanied by ``.tgtsym`` and ``.tgtimg`` sections. ``.tgtsym``
is a string table storing kernel entry-point names, while ``.tgtimg`` lists
offset/size descriptors that map those names to the SPIR-V payload inside the
bundle. By dumping these sections with ``objcopy`` the analysis now quantifies
their size: ``libonedal_dpc.so.3`` carries 70.0 MiB of SPIR-V kernels plus
1.95 MiB of metadata, which explains almost a quarter of the binary even before
host orchestration is counted. The same structure (albeit only 104 bytes) is
present in ``libonedal_parameters_dpc.so.3`` for the SYCL parameter helpers.

Decoding the ``.tgtimg``/``.tgtsym`` tables further shows that
``libonedal_dpc.so.3`` ships 6,683 individual SPIR-V kernels that add up to
70.0 MiB (median size ≈ 6.0 KiB, 99th percentile ≈ 87 KiB and a maximum of
0.61 MiB). The heaviest families belong to
``oneapi::dal::backend::primitives`` selectors (≈3.5 MiB) and a suite of MKL
sparse GEMV helpers such as ``oneapi::mkl::gpu::l2_ker_{buf,usm}``,
``matadd_block_kernel`` and ``verbose_buffer_start`` (each between 1.1 MiB and
2.6 MiB). The largest individual kernels mirror those aggregates: the
double-precision ``compute_probabilities_sparse`` functor weighs 0.61 MiB, the
``convert_vector_kernel<double, unsigned short>`` path takes 0.60 MiB and the
``primitives::copy`` helpers contribute another 0.40 MiB. These findings mean
that a sizeable fraction of the device image is dedicated to host-side
adaptation code (type conversion, selector orchestration and MKL wrappers)
rather than pure graph or tree kernels, highlighting concrete areas for future
size trimming. For readers less familiar with the SYCL toolchain: each of these
entries is the SPIR-V representation of a C++ kernel functor that executes on
the GPU device; reducing their count, sharing common implementations or moving
MKL-heavy families into a dedicated component directly shaves bytes from the
70 MiB offload bundle.

Runtime dependencies
--------------------

``ldd`` confirms that the GPU binaries rely on the Intel oneAPI runtime stack
and OpenCL components that are not bundled inside the wheel (``libsycl.so.8``,
``libOpenCL.so.1``, ``libimf.so``, ``libsvml.so``, ``libirng.so``,
``libintlc.so.5``). ``libonedal_thread.so.3`` expects TBB runtimes, while the
parameter libraries depend on the respective dispatcher (``libonedal.so.3``) and
SYCL implementation (``libonedal_dpc.so.3``).

Auditwheel summary
------------------

``auditwheel show`` constrains the platform tag to ``manylinux_2_27_x86_64`` due
to references against glibc 2.14 and libstdc++ 3.4.21 symbols. External version
constraints also capture ``libOpenCL.so.1`` in addition to libc, libm, libdl,
libpthread, libgcc and libstdc++.

Metadata highlights
-------------------

* ``METADATA`` advertises the Intel Simplified Software License and points to
  the ``uxlfoundation/oneDAL`` repository as the home page.
* ``WHEEL`` records ``Root-Is-Purelib: true`` and dual tags for ``py2`` and
  ``py3`` with the ``manylinux_2_28_x86_64`` compatibility tag.

Next steps
----------

The captured JSON summaries (``compact_summary.json``, ``file_inventory.json``
and ``sections_summary.json``) can be found under
``build/wheel_analysis/analysis`` after running the script. They are ready for
ingestion into notebooks to extend the analysis towards namespace aggregation,
visualisations and release-over-release regression tracking.
