#!/usr/bin/env python3
"""Render a human-readable summary from wheel analysis artefacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis-dir",
        default="build/wheel_analysis/analysis",
        help="Directory containing compact_summary.json (default: %(default)s)",
    )
    parser.add_argument(
        "--top-namespaces",
        type=int,
        default=5,
        help="Number of namespace entries to include for each library",
    )
    return parser.parse_args()


def format_bytes_to_mib(value: int | float) -> str:
    return f"{value / (1024 * 1024):.2f} MiB"


def format_bytes_to_kib(value: int | float) -> str:
    return f"{value / 1024:.1f} KiB"


def load_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_library_section(library: Dict[str, object], top_n: int) -> List[str]:
    lines: List[str] = []
    name = library.get("name", "<unknown>")
    size_bytes = int(library.get("size_bytes") or 0)
    section_aggregates = library.get("section_aggregates", {}) or {}
    device_sections: Iterable[Dict[str, object]] = library.get("device_sections", []) or []
    device_overview: Dict[str, object] = library.get("device_overview", {}) or {}
    dynamic_symbol_count = int(library.get("dynamic_symbol_count") or 0)
    top_namespaces: Iterable[Tuple[str, int]] = library.get("top_namespaces", []) or []
    static_info: Dict[str, object] = library.get("static_symbols", {}) or {}

    lines.append(f"## {name}")
    lines.append("")
    lines.append(f"* Size: {format_bytes_to_mib(size_bytes)}")

    if section_aggregates:
        lines.append(
            "* Section mix: "
            f"code {format_bytes_to_mib(int(section_aggregates.get('code_bytes', 0)))}"
            ", rodata "
            f"{format_bytes_to_mib(int(section_aggregates.get('rodata_bytes', 0)))}"
            ", data "
            f"{format_bytes_to_mib(int(section_aggregates.get('data_bytes', 0)))}"
            ", bss "
            f"{format_bytes_to_mib(int(section_aggregates.get('bss_bytes', 0)))}"
        )

    lines.append(f"* Dynamic symbols: {dynamic_symbol_count:,}")

    defined_static = int(static_info.get("defined_symbols") or 0)
    if defined_static:
        counts_by_bind: Dict[str, int] = static_info.get("counts_by_bind", {}) or {}
        local_count = int(counts_by_bind.get("LOCAL", 0))
        global_count = int(counts_by_bind.get("GLOBAL", 0)) + int(
            counts_by_bind.get("WEAK", 0)
        )
        lines.append(
            "* Static symbols: "
            f"{defined_static:,} defined ({local_count:,} local, {global_count:,} global/weak)"
        )

    name_bytes_by_bind: Dict[str, int] = static_info.get("name_bytes_by_bind", {}) or {}
    if name_bytes_by_bind:
        local_bytes = int(name_bytes_by_bind.get("LOCAL", 0))
        exported_bytes = int(name_bytes_by_bind.get("GLOBAL", 0)) + int(
            name_bytes_by_bind.get("WEAK", 0)
        )
        lines.append(
            "* Estimated name table split: "
            f"{format_bytes_to_mib(local_bytes)} local, "
            f"{format_bytes_to_mib(exported_bytes)} exported"
        )

    size_by_storage: Dict[str, int] = static_info.get("size_by_storage", {}) or {}
    if size_by_storage:
        ro_bytes = int(size_by_storage.get("rodata", 0))
        rw_bytes = int(size_by_storage.get("rwdata", 0)) + int(
            size_by_storage.get("common", 0)
        )
        bss_bytes = int(size_by_storage.get("bss", 0))
        other_bytes = int(size_by_storage.get("other", 0)) + int(
            size_by_storage.get("absolute", 0)
        )
        parts: List[str] = []
        if ro_bytes:
            parts.append(f"rodata {format_bytes_to_mib(ro_bytes)}")
        if rw_bytes:
            parts.append(f"rw data {format_bytes_to_mib(rw_bytes)}")
        if bss_bytes:
            parts.append(f"bss {format_bytes_to_mib(bss_bytes)}")
        if other_bytes:
            parts.append(f"other {format_bytes_to_mib(other_bytes)}")
        text_bytes = int(size_by_storage.get("text", 0))
        if text_bytes and not parts:
            # When only text is present (pure dispatcher stubs), still surface it.
            parts.append(f"text {format_bytes_to_mib(text_bytes)}")
        elif text_bytes and parts:
            parts.append(f"text {format_bytes_to_mib(text_bytes)}")
        if parts:
            lines.append("* Static storage split: " + ", ".join(parts))

    length_stats: Dict[str, float | int] = static_info.get("name_length_stats", {}) or {}
    if length_stats:
        average = float(length_stats.get("average", 0.0))
        p99 = int(length_stats.get("p99", 0))
        max_length = int(length_stats.get("max", 0))
        lines.append(
            "* Symbol name lengths: "
            f"avg {average:.1f} chars, p99 {p99}, max {max_length}"
        )

    total_device = int(device_overview.get("total_bytes", 0))
    if total_device:
        image_bytes = int(device_overview.get("image_bytes", 0))
        metadata_bytes = int(device_overview.get("metadata_bytes", 0))
        lines.append(
            "* Device payload: "
            f"{format_bytes_to_mib(total_device)} "
            f"({format_bytes_to_mib(image_bytes)} images, "
            f"{format_bytes_to_mib(metadata_bytes)} metadata)"
        )

    device_entries = list(device_sections)
    if device_entries:
        lines.append("* Device sections captured:")
        for entry in device_entries[:top_n]:
            name = entry.get("name", "<unknown>")
            size = int(entry.get("size") or 0)
            category = entry.get("category", "device_related")
            lines.append(
                f"  - {name} ({category}) – {format_bytes_to_mib(size)}"
            )

    device_kernel_info: Dict[str, object] = library.get("sycl_device_kernels") or {}
    if device_kernel_info:
        entry_count = int(device_kernel_info.get("entry_count", 0))
        total_bytes = int(device_kernel_info.get("total_bytes", 0))
        average_bytes = float(device_kernel_info.get("average_bytes", 0.0))
        lines.append(
            "* SYCL kernel bundle: "
            f"{entry_count:,} entries totalling {format_bytes_to_mib(total_bytes)} "
            f"(avg {format_bytes_to_kib(average_bytes)})"
        )

        size_stats: Dict[str, int] = device_kernel_info.get("size_stats", {}) or {}
        if size_stats:
            lines.append(
                "  - Kernel sizes: "
                f"median {format_bytes_to_kib(int(size_stats.get('median', 0)))}"
                f", p90 {format_bytes_to_kib(int(size_stats.get('p90', 0)))}"
                f", max {format_bytes_to_kib(int(size_stats.get('max', 0)))}"
            )

        families = device_kernel_info.get("top_families", []) or []
        family_entries = list(families)[:top_n]
        if family_entries:
            lines.append("  - Heaviest kernel families:")
            for entry in family_entries:
                family_name = entry.get("family", "<unknown>")
                family_bytes = int(entry.get("bytes", 0))
                family_count = int(entry.get("count", 0))
                lines.append(
                    f"    * {family_name} – {format_bytes_to_mib(family_bytes)} "
                    f"across {family_count} kernels"
                )

        top_kernels = device_kernel_info.get("top_kernels", []) or []
        kernel_entries = list(top_kernels)[: min(top_n, 5)]
        if kernel_entries:
            lines.append("  - Largest kernels:")
            for entry in kernel_entries:
                kernel_name = entry.get("demangled") or entry.get("mangled")
                kernel_size = int(entry.get("size", 0))
                lines.append(
                    f"    * {kernel_name} – {format_bytes_to_kib(kernel_size)}"
                )

    top_namespace_entries = list(top_namespaces)[:top_n]
    if top_namespace_entries:
        lines.append("* Top namespaces by cumulative symbol size:")
        for namespace, size in top_namespace_entries:
            lines.append(f"  - {namespace} – {format_bytes_to_kib(int(size))}")

    local_namespaces: Iterable[Tuple[str, int]] = (
        static_info.get("namespace_level3_local", []) or []
    )
    local_entries = list(local_namespaces)[:top_n]
    if local_entries:
        lines.append("* Heaviest local namespaces:")
        for namespace, size in local_entries:
            lines.append(f"  - {namespace} – {format_bytes_to_kib(int(size))}")

    rodata_namespaces: Iterable[Tuple[str, int]] = static_info.get("namespace_rodata", []) or []
    rodata_entries = list(rodata_namespaces)[:top_n]
    if rodata_entries:
        lines.append("* Read-only data hot spots:")
        for namespace, size in rodata_entries:
            lines.append(f"  - {namespace} – {format_bytes_to_kib(int(size))}")

    rw_namespaces: Iterable[Tuple[str, int]] = static_info.get("namespace_rwdata", []) or []
    rw_entries = list(rw_namespaces)[:top_n]
    if rw_entries:
        lines.append("* Writable data hot spots:")
        for namespace, size in rw_entries:
            lines.append(f"  - {namespace} – {format_bytes_to_kib(int(size))}")

    local_funcs: Iterable[Dict[str, object]] = (
        static_info.get("top_local_functions", []) or []
    )
    local_func_entries = list(local_funcs)[:top_n]
    if local_func_entries:
        lines.append("* Largest local functions:")
        for entry in local_func_entries:
            lines.append(
                f"  - {entry.get('name', '<unknown>')} – "
                f"{format_bytes_to_kib(int(entry.get('size', 0)))}"
            )

    rodata_objects: Iterable[Dict[str, object]] = (
        static_info.get("top_rodata_objects", []) or []
    )
    rodata_object_entries = list(rodata_objects)[: min(top_n, 3)]
    if rodata_object_entries:
        lines.append("* Largest read-only objects:")
        for entry in rodata_object_entries:
            lines.append(
                f"  - {entry.get('name', '<unknown>')} – "
                f"{format_bytes_to_kib(int(entry.get('size', 0)))}"
            )

    rw_objects: Iterable[Dict[str, object]] = static_info.get("top_rw_objects", []) or []
    rw_object_entries = list(rw_objects)[: min(top_n, 3)]
    if rw_object_entries:
        lines.append("* Largest writable objects:")
        for entry in rw_object_entries:
            lines.append(
                f"  - {entry.get('name', '<unknown>')} – "
                f"{format_bytes_to_kib(int(entry.get('size', 0)))}"
            )

    bss_objects: Iterable[Dict[str, object]] = static_info.get("top_bss_objects", []) or []
    bss_entries = list(bss_objects)[: min(top_n, 3)]
    if bss_entries:
        lines.append("* Largest zero-initialised objects:")
        for entry in bss_entries:
            lines.append(
                f"  - {entry.get('name', '<unknown>')} – "
                f"{format_bytes_to_kib(int(entry.get('size', 0)))}"
            )

    longest_names: Iterable[Dict[str, object]] = static_info.get("longest_names", []) or []
    longest_entries = list(longest_names)[: min(top_n, 3)]
    if longest_entries:
        lines.append("* Longest symbol names:")
        for entry in longest_entries:
            raw_name = entry.get("name", "<unknown>")
            display = raw_name if len(raw_name) <= 120 else f"{raw_name[:117]}..."
            lines.append(
                f"  - {display} ({int(entry.get('length', 0))} chars)"
            )

    lines.append("")
    return lines


def render_symbol_overlap(overlap: Dict[str, object]) -> List[str]:
    if not overlap:
        return []

    lines = ["## Symbol overlap", ""]
    for pair, payload in sorted(overlap.items()):
        if pair == "triple_overlap":
            shared = int(payload.get("shared_count", 0))
            if shared:
                lines.append(f"* Triple overlap across all libraries: {shared} symbols")
            continue
        shared_count = int(payload.get("shared_count", 0))
        if shared_count == 0:
            continue
        lines.append(f"* {pair}: {shared_count} shared symbols")
        top_namespaces: Iterable[Dict[str, object]] = payload.get("top_namespaces", []) or []
        namespace_entries = list(top_namespaces)[:3]
        if namespace_entries:
            formatted = []
            for entry in namespace_entries:
                namespace = entry.get("namespace", "<unknown>")
                combined_size = int(entry.get("size_a", 0)) + int(entry.get("size_b", 0))
                formatted.append(
                    f"{namespace} ({int(entry.get('count', 0))} syms, {format_bytes_to_kib(combined_size)})"
                )
            lines.append(f"  - Hot namespaces: {', '.join(formatted)}")
    lines.append("")
    return lines


def render_runtime_deps(runtime_deps: Dict[str, List[str]]) -> List[str]:
    if not runtime_deps:
        return []
    lines = ["## Runtime dependencies", ""]
    for lib, deps in sorted(runtime_deps.items()):
        formatted = ", ".join(deps) if deps else "<none>"
        lines.append(f"* {lib}: {formatted}")
    lines.append("")
    return lines


def render_auditwheel(report: Dict[str, object] | None) -> List[str]:
    if not report:
        return []
    lines = ["## Auditwheel", ""]
    platform_tag = report.get("platform_tag")
    constrained = report.get("constrained_tag")
    external_libs = report.get("external_libs", []) or []
    if platform_tag:
        lines.append(f"* Reported platform tag: {platform_tag}")
    if constrained and constrained != platform_tag:
        lines.append(f"* Constrained tag: {constrained}")
    if external_libs:
        lines.append("* External system libraries:")
        for lib in external_libs:
            lines.append(f"  - {lib}")
    lines.append("")
    return lines


def main() -> None:
    args = parse_args()
    analysis_dir = Path(args.analysis_dir)
    compact_path = analysis_dir / "compact_summary.json"
    if not compact_path.exists():
        raise FileNotFoundError(f"{compact_path} not found. Run analyze_daal_wheel.py first.")

    data = load_json(compact_path)
    wheel_file = data.get("wheel_file", "daal wheel")
    wheel_size = int(data.get("wheel_size_bytes") or 0)
    uncompressed = int(data.get("total_uncompressed_bytes") or 0)
    libraries: Iterable[Dict[str, object]] = data.get("libraries", []) or []
    runtime_deps: Dict[str, List[str]] = data.get("runtime_dependencies", {}) or {}
    overlap = data.get("symbol_overlap", {}) or {}
    auditwheel_report = data.get("auditwheel")

    lines: List[str] = []
    lines.append(f"# Summary for {wheel_file}")
    lines.append("")
    lines.append(f"* Wheel size: {format_bytes_to_mib(wheel_size)} compressed")
    lines.append(f"* Uncompressed payload: {format_bytes_to_mib(uncompressed)}")
    lines.append("")

    for library in libraries:
        lines.extend(render_library_section(library, args.top_namespaces))

    lines.extend(render_symbol_overlap(overlap))
    lines.extend(render_runtime_deps(runtime_deps))
    lines.extend(render_auditwheel(auditwheel_report))

    print("\n".join(lines))


if __name__ == "__main__":
    main()
