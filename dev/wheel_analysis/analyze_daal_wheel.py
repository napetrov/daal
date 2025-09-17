#!/usr/bin/env python3
"""Utility to inspect the PyPI daal wheel payload.

The script automates the data-collection phases described in
``docs/source/contribution/onedal_wheel_analysis_plan.rst`` by downloading the
requested wheel, unpacking it and emitting machine-readable summaries covering:

* File inventory with SHA-256 hashes and size breakdowns.
* Section statistics for each shared library in the payload.
* Dynamic symbol tables with demangled names and namespace aggregation.
* Cross-library symbol overlap metrics to highlight duplication.
* Runtime dependency captures via ``ldd`` and ``auditwheel show``.

All results are written to the selected output directory in JSON form so that
subsequent reporting notebooks can reuse the data without re-running heavy
binary tooling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from heapq import heappush, heappushpop, nlargest
from pathlib import Path
from statistics import median
from typing import Dict, Iterator, List, Optional, Sequence

# ``auditwheel`` is imported lazily because it may not be available in the
# execution environment.  The script falls back gracefully when the module
# cannot be imported.
try:  # pragma: no cover - import guard
    from auditwheel.wheel_abi import analyze_wheel_abi
except Exception:  # pragma: no cover - fallback handled at runtime
    analyze_wheel_abi = None  # type: ignore


@dataclass
class SectionSummary:
    name: str
    size: int
    flags: str


DEVICE_IMAGE_PREFIXES = (
    "__CLANG_OFFLOAD_BUNDLE__",
    ".sycl_offload",
    ".llvm_offloading",
)

DEVICE_METADATA_NAMES = {
    ".tgtimg": "image_table",
    ".tgtsym": "kernel_symbol_table",
}


def _classify_device_section(name: str) -> Optional[str]:
    """Return the device payload category for *name* if it matches heuristics."""

    lowered = name.lower()
    if any(lowered.startswith(prefix.lower()) for prefix in DEVICE_IMAGE_PREFIXES):
        return "device_image"
    if lowered in DEVICE_METADATA_NAMES:
        return DEVICE_METADATA_NAMES[lowered]
    if "spir" in lowered or "sycl" in lowered:
        return "device_related"
    return None


@dataclass
class SymbolSummary:
    name: str
    demangled: str
    size: int
    bind: str
    typ: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package",
        default="daal==2025.8.0",
        help="Wheel specifier understood by pip (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default="build/wheel_analysis",
        help="Directory where the wheel and analysis artefacts are stored",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Reuse an existing wheel in the output directory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log subprocess commands before executing them",
    )
    return parser.parse_args()


def run_command(cmd: Sequence[str], verbose: bool = False) -> subprocess.CompletedProcess:
    if verbose:
        print("[cmd]", " ".join(cmd))
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def download_wheel(package_spec: str, download_dir: Path, verbose: bool = False) -> Path:
    download_dir.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"Downloading wheel {package_spec!r} into {download_dir}")
    cmd = [sys.executable, "-m", "pip", "download", package_spec, "--no-deps", "-d", str(download_dir)]
    run_command(cmd, verbose=verbose)
    wheels = sorted(download_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No wheels found in {download_dir}")
    # Return the most recently modified wheel to support repeated runs.
    wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)
    if verbose:
        print(f"Found wheel {wheel_path.name}")
    return wheel_path


def extract_wheel(wheel_path: Path, extract_dir: Path, verbose: bool = False) -> Path:
    import zipfile

    ensure_clean_dir(extract_dir)
    with zipfile.ZipFile(wheel_path, "r") as zf:
        zf.extractall(extract_dir)
    if verbose:
        print(f"Extracted {wheel_path.name} into {extract_dir}")
    return extract_dir


def iter_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def categorize_file(path: Path) -> str:
    parts = path.parts
    if any(part.endswith(".dist-info") for part in parts):
        return "metadata"
    if any(part.endswith(".data") for part in parts) and "lib" in parts:
        if any(suffix.startswith(".so") for suffix in path.suffixes) or path.suffix == ".so":
            return "shared_library"
        return "native_payload"
    if path.suffix == ".py":
        return "python"
    return "other"


def build_file_inventory(extracted_dir: Path, wheel_path: Path, output_dir: Path) -> Dict[str, object]:
    manifest: List[Dict[str, object]] = []
    total_uncompressed = 0
    for file_path in iter_files(extracted_dir):
        rel_path = file_path.relative_to(extracted_dir).as_posix()
        size = file_path.stat().st_size
        file_info = {
            "path": rel_path,
            "size": size,
            "sha256": sha256sum(file_path),
            "category": categorize_file(file_path),
        }
        manifest.append(file_info)
        total_uncompressed += size

    manifest.sort(key=lambda entry: entry["size"], reverse=True)

    archive_size = wheel_path.stat().st_size
    top_entries = manifest[:25]
    by_category: Dict[str, int] = defaultdict(int)
    for entry in manifest:
        by_category[entry["category"]] += int(entry["size"])

    inventory = {
        "wheel_file": wheel_path.name,
        "wheel_size_bytes": archive_size,
        "total_uncompressed_bytes": total_uncompressed,
        "files": manifest,
        "top_entries": top_entries,
        "bytes_by_category": by_category,
    }

    with (output_dir / "file_inventory.json").open("w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    return inventory


SECTION_HEADER_RE = re.compile(
    r"\[\s*\d+\]\s+(?P<name>\S+)\s+\S+\s+[0-9a-fA-F]+\s+"
    r"[0-9a-fA-F]+\s+(?P<size>[0-9a-fA-F]+)\s+\S+\s+(?P<flags>[A-Za-z]*)"
)


def summarize_sections(library: Path, verbose: bool = False) -> Dict[str, object]:
    sections: List[SectionSummary] = []
    aggregates = {
        "code_bytes": 0,
        "rodata_bytes": 0,
        "data_bytes": 0,
        "bss_bytes": 0,
    }
    device_sections: List[Dict[str, object]] = []
    device_totals = {
        "total_bytes": 0,
        "image_bytes": 0,
        "metadata_bytes": 0,
    }

    result = run_command(
        ["readelf", "--section-headers", "--wide", str(library)], verbose=verbose
    )
    for line in result.stdout.splitlines():
        match = SECTION_HEADER_RE.search(line)
        if not match:
            continue
        name = match.group("name")
        size = int(match.group("size"), 16)
        flags = match.group("flags") or ""
        sections.append(SectionSummary(name=name, size=size, flags=flags))

        if "X" in flags:
            aggregates["code_bytes"] += size
        elif name == ".bss":
            aggregates["bss_bytes"] += size
        elif "W" in flags:
            aggregates["data_bytes"] += size
        elif "A" in flags:
            aggregates["rodata_bytes"] += size

        device_category = _classify_device_section(name)
        if device_category:
            entry = {"name": name, "size": size, "category": device_category}
            device_sections.append(entry)
            device_totals["total_bytes"] += size
            if device_category == "device_image":
                device_totals["image_bytes"] += size
            elif device_category in {"image_table", "kernel_symbol_table"}:
                device_totals["metadata_bytes"] += size

    sections.sort(key=lambda s: s.size, reverse=True)
    device_sections.sort(key=lambda entry: entry["size"], reverse=True)

    return {
        "library": library.name,
        "path": library.as_posix(),
        "sections": [section.__dict__ for section in sections],
        "aggregates": aggregates,
        "device_sections": device_sections,
        "device_overview": device_totals,
    }


def _percentile(sorted_values: Sequence[int], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * percentile
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(sorted_values[lower])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight = rank - lower
    return float(lower_value + (upper_value - lower_value) * weight)


def _classify_kernel_family(demangled: str) -> str:
    namespace_markers = [
        "oneapi::dal::",
        "oneapi::mkl::",
        "daal::",
        "sycl::_V1::",
    ]
    for marker in namespace_markers:
        if marker in demangled:
            tail = demangled.split(marker, 1)[1]
            parts = [token for token in tail.split("::") if token]
            if not parts:
                return marker.rstrip(":")
            limit = 2 if marker == "sycl::_V1::" else 3
            chosen = parts[:limit]
            return marker + "::".join(chosen)
    return "other"


def _build_size_histogram(sizes: Sequence[int]) -> List[Dict[str, object]]:
    bins: List[tuple[int, str]] = [
        (512, "≤0.5 KiB"),
        (1024, "≤1 KiB"),
        (2048, "≤2 KiB"),
        (4096, "≤4 KiB"),
        (8192, "≤8 KiB"),
        (16384, "≤16 KiB"),
        (32768, "≤32 KiB"),
        (65536, "≤64 KiB"),
        (131072, "≤128 KiB"),
        (262144, "≤256 KiB"),
        (524288, "≤512 KiB"),
    ]
    counters: Counter[str] = Counter()
    for size in sizes:
        bucket_label = None
        for threshold, label in bins:
            if size <= threshold:
                bucket_label = label
                break
        if bucket_label is None:
            bucket_label = ">512 KiB"
        counters[bucket_label] += 1
    histogram: List[Dict[str, object]] = []
    for _threshold, label in bins:
        if counters[label]:
            histogram.append({"bucket": label, "count": counters[label]})
    if counters[">512 KiB"]:
        histogram.append({"bucket": ">512 KiB", "count": counters[">512 KiB"]})
    return histogram


def analyze_device_kernels(
    library: Path, verbose: bool = False, *, top_limit: int = 25
) -> Optional[Dict[str, object]]:
    objcopy = shutil.which("objcopy")
    if objcopy is None:  # pragma: no cover - environment dependent
        return {"error": "objcopy tool not available"}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        tgtimg_path = tmpdir_path / "device.tgtimg"
        tgtsym_path = tmpdir_path / "device.tgtsym"
        try:
            run_command(
                [
                    objcopy,
                    f"--dump-section",
                    f".tgtimg={tgtimg_path}",
                    str(library),
                ],
                verbose=verbose,
            )
            run_command(
                [
                    objcopy,
                    f"--dump-section",
                    f".tgtsym={tgtsym_path}",
                    str(library),
                ],
                verbose=verbose,
            )
        except subprocess.CalledProcessError as exc:
            return {"error": exc.stderr or exc.stdout or str(exc)}

        if not tgtimg_path.exists() or tgtimg_path.stat().st_size == 0:
            return None
        if not tgtsym_path.exists() or tgtsym_path.stat().st_size == 0:
            return None

        tgtimg_data = tgtimg_path.read_bytes()
        entries: List[tuple[int, int]] = []
        for i in range(0, len(tgtimg_data), 16):
            chunk = tgtimg_data[i : i + 16]
            if len(chunk) < 16:
                break
            offset, size = struct.unpack("<QQ", chunk)
            if size:
                entries.append((offset, size))

        if not entries:
            return None

        tgtsym_data = tgtsym_path.read_bytes()
        names: List[str] = [
            part.decode("utf-8", errors="ignore")
            for part in tgtsym_data.split(b"\x00")
            if part
        ]

    pair_count = min(len(entries), len(names))
    if pair_count == 0:
        return None

    paired_entries = entries[:pair_count]
    paired_names = names[:pair_count]

    mangled: List[str] = []
    for name in paired_names:
        if "._Z" in name:
            mangled.append(name.split(".", 1)[1])
        else:
            mangled.append(name)

    demangled = _demangle_batch(tuple(mangled))

    sizes = sorted(size for _, size in paired_entries)
    total_bytes = sum(sizes)
    average = float(total_bytes) / pair_count if pair_count else 0.0
    size_stats = {
        "min": sizes[0],
        "median": int(median(sizes)),
        "p90": int(_percentile(sizes, 0.90)),
        "p99": int(_percentile(sizes, 0.99)),
        "max": sizes[-1],
    }

    families: Dict[str, Dict[str, int]] = {}
    detailed_entries: List[Dict[str, object]] = []
    for (offset, size), original_name, demangled_name in zip(
        paired_entries, paired_names, demangled
    ):
        family = _classify_kernel_family(demangled_name)
        bucket = families.setdefault(family, {"bytes": 0, "count": 0})
        bucket["bytes"] += int(size)
        bucket["count"] += 1
        detailed_entries.append(
            {
                "offset": offset,
                "size": int(size),
                "mangled": original_name,
                "demangled": demangled_name,
            }
        )

    top_families = sorted(
        (
            {
                "family": family,
                "bytes": stats["bytes"],
                "count": stats["count"],
            }
            for family, stats in families.items()
        ),
        key=lambda item: item["bytes"],
        reverse=True,
    )[: min(top_limit, 20)]

    largest_entries = sorted(
        detailed_entries,
        key=lambda entry: entry["size"],
        reverse=True,
    )[:top_limit]
    for entry in largest_entries:
        demangled_name = entry.get("demangled", "")
        if demangled_name and len(demangled_name) > 512:
            entry["demangled"] = demangled_name[:512] + "…"

    histogram = _build_size_histogram([entry["size"] for entry in detailed_entries])

    return {
        "entry_count": pair_count,
        "total_bytes": total_bytes,
        "average_bytes": average,
        "raw_entry_count": len(entries),
        "raw_name_count": len(names),
        "size_stats": size_stats,
        "size_histogram": histogram,
        "top_families": top_families,
        "top_kernels": largest_entries,
    }


def _nm_command(
    library: Path, *, demangle: bool, verbose: bool, dynamic_only: bool
) -> List[str]:
    args = ["nm", "--size-sort", "--print-size", "--radix=d", "--format=posix"]
    if dynamic_only:
        args.append("-D")
    if demangle:
        args.append("--demangle")
    args.append(str(library))
    result = run_command(args, verbose=verbose)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _parse_nm_output(lines: List[str], *, demangled: bool) -> List[tuple[str, str, int]]:
    entries: List[tuple[str, str, int]] = []
    for line in lines:
        if line.startswith("nm:"):
            continue
        parts = line.rsplit(" ", 3) if demangled else line.split()
        if len(parts) != 4:
            continue
        name, kind, _value, size_str = parts
        try:
            size = int(size_str, 0)
        except ValueError:
            continue
        entries.append((name, kind, size))
    return entries


@lru_cache()
def _find_external_demangler() -> Optional[List[str]]:
    for candidate in ("c++filt", "llvm-cxxfilt"):
        path = shutil.which(candidate)
        if path:
            return [path]
    return None


def _demangle_batch(names: Sequence[str]) -> List[str]:
    if not names:
        return []
    demangler = _find_external_demangler()
    if demangler is None:
        return list(names)
    proc = subprocess.run(
        demangler,
        input="\n".join(names) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return list(names)
    output = [line.rstrip("\n") for line in proc.stdout.splitlines()]
    if len(output) != len(names):
        return list(names)
    return output


def _classify_symbol_kind(kind: str) -> tuple[str, str]:
    upper = kind.upper()
    if upper == "U":
        return ("UNDEFINED", "UNKNOWN")
    if upper in {"W", "V"}:
        bind = "WEAK"
    elif kind.islower():
        bind = "LOCAL"
    else:
        bind = "GLOBAL"

    if upper in {"T", "W"}:
        typ = "FUNC"
    elif upper in {"V", "D", "B", "R", "S", "C"}:
        typ = "OBJECT"
    else:
        typ = "UNKNOWN"
    return bind, typ


def _classify_storage_class(kind: str) -> str:
    """Map an ``nm`` kind code to a coarse storage class."""

    upper = kind.upper()
    if upper in {"T", "W"}:
        return "text"
    if upper == "R":
        return "rodata"
    if upper in {"D", "S", "V"}:
        return "rwdata"
    if upper == "B":
        return "bss"
    if upper == "C":
        return "common"
    if upper == "A":
        return "absolute"
    return "other"


def collect_dynamic_symbols(library: Path, verbose: bool = False) -> Dict[str, object]:
    symbols: List[SymbolSummary] = []
    namespace_level3: Counter[str] = Counter()
    namespace_level4: Counter[str] = Counter()

    try:
        raw_lines = _nm_command(
            library, demangle=False, verbose=verbose, dynamic_only=True
        )
    except FileNotFoundError as exc:  # pragma: no cover - external tool missing
        raise RuntimeError(f"nm tool not available: {exc}")
    base_entries = _parse_nm_output(raw_lines, demangled=False)

    demangled_lines: List[str] = []
    demangled_entries: List[tuple[str, str, int]] = []
    try:
        demangled_lines = _nm_command(
            library, demangle=True, verbose=verbose, dynamic_only=True
        )
        demangled_entries = _parse_nm_output(demangled_lines, demangled=True)
    except Exception:
        demangled_entries = []

    if demangled_entries and len(demangled_entries) == len(base_entries):
        demangled_names = [entry[0] for entry in demangled_entries]
    else:
        demangled_names = _demangle_batch([entry[0] for entry in base_entries])

    for idx, (name, kind, size) in enumerate(base_entries):
        bind, typ = _classify_symbol_kind(kind)
        if bind == "UNDEFINED":
            continue
        demangled_name = demangled_names[idx] if idx < len(demangled_names) else name
        symbols.append(
            SymbolSummary(
                name=name,
                demangled=demangled_name,
                size=size,
                bind=bind,
                typ=typ,
            )
        )
        if demangled_name:
            tokens = [token for token in demangled_name.split("::") if token]
            if len(tokens) >= 3:
                namespace_level3["::".join(tokens[:3])] += size
            elif tokens:
                namespace_level3[tokens[0]] += size
            if len(tokens) >= 4:
                namespace_level4["::".join(tokens[:4])] += size
            elif len(tokens) >= 2:
                namespace_level4["::".join(tokens[:2])] += size

    symbols.sort(key=lambda s: s.size, reverse=True)

    return {
        "library": library.name,
        "path": library.as_posix(),
        "symbols": [symbol.__dict__ for symbol in symbols],
        "namespace_level3": namespace_level3.most_common(50),
        "namespace_level4": namespace_level4.most_common(50),
    }


def collect_static_symbol_stats(
    library: Path,
    verbose: bool = False,
    *,
    top_limit: int = 50,
) -> Dict[str, object]:
    try:
        raw_lines = _nm_command(
            library, demangle=False, verbose=verbose, dynamic_only=False
        )
    except FileNotFoundError as exc:  # pragma: no cover - external tool missing
        raise RuntimeError(f"nm tool not available: {exc}")
    base_entries = _parse_nm_output(raw_lines, demangled=False)

    demangled_entries: List[tuple[str, str, int]] = []
    try:
        demangled_lines = _nm_command(
            library, demangle=True, verbose=verbose, dynamic_only=False
        )
        demangled_entries = _parse_nm_output(demangled_lines, demangled=True)
    except Exception:
        demangled_entries = []

    if demangled_entries and len(demangled_entries) == len(base_entries):
        demangled_names = [entry[0] for entry in demangled_entries]
    else:
        demangled_names = _demangle_batch([entry[0] for entry in base_entries])

    counts_by_bind: Counter[str] = Counter()
    size_by_bind: Counter[str] = Counter()
    counts_by_type: Counter[str] = Counter()
    size_by_type: Counter[str] = Counter()
    counts_by_kind: Counter[str] = Counter()
    size_by_kind: Counter[str] = Counter()
    counts_by_storage: Counter[str] = Counter()
    size_by_storage: Counter[str] = Counter()
    namespace_level3_all: Counter[str] = Counter()
    namespace_level3_local: Counter[str] = Counter()
    namespace_level3_global: Counter[str] = Counter()
    namespace_rodata: Counter[str] = Counter()
    namespace_rwdata: Counter[str] = Counter()
    namespace_bss: Counter[str] = Counter()
    name_bytes_by_bind: Counter[str] = Counter()

    name_lengths: List[int] = []
    local_funcs_heap: List[tuple[int, str]] = []
    global_funcs_heap: List[tuple[int, str]] = []
    local_objects_heap: List[tuple[int, str]] = []
    global_objects_heap: List[tuple[int, str]] = []
    rodata_objects_heap: List[tuple[int, str]] = []
    rw_objects_heap: List[tuple[int, str]] = []
    bss_objects_heap: List[tuple[int, str]] = []
    longest_names_heap: List[tuple[int, tuple[str, str, str, int]]] = []

    total_symbols = len(base_entries)
    defined_symbols = 0

    for idx, (name, kind, size) in enumerate(base_entries):
        bind, typ = _classify_symbol_kind(kind)
        if bind == "UNDEFINED":
            continue
        defined_symbols += 1

        storage_class = _classify_storage_class(kind)
        counts_by_kind[kind.upper()] += 1
        size_by_kind[kind.upper()] += size
        counts_by_storage[storage_class] += 1
        size_by_storage[storage_class] += size

        demangled_name = demangled_names[idx] if idx < len(demangled_names) else name
        display_name = demangled_name or name

        counts_by_bind[bind] += 1
        size_by_bind[bind] += size
        counts_by_type[typ] += 1
        size_by_type[typ] += size

        name_length = len(display_name)
        if name_length:
            name_lengths.append(name_length)
            # Include null terminator to approximate .strtab contribution.
            name_bytes_by_bind[bind] += name_length + 1
            record = (display_name, bind, typ, size)
            if len(longest_names_heap) < top_limit:
                heappush(longest_names_heap, (name_length, record))
            elif name_length > longest_names_heap[0][0]:
                heappushpop(longest_names_heap, (name_length, record))

        tokens = [token for token in display_name.split("::") if token]
        if tokens and size:
            key = "::".join(tokens[:3]) if len(tokens) >= 3 else tokens[0]
            namespace_level3_all[key] += size
            if bind == "LOCAL":
                namespace_level3_local[key] += size
            else:
                namespace_level3_global[key] += size

        if size > 0 and typ == "FUNC":
            if bind == "LOCAL":
                if len(local_funcs_heap) < top_limit:
                    heappush(local_funcs_heap, (size, display_name))
                elif size > local_funcs_heap[0][0]:
                    heappushpop(local_funcs_heap, (size, display_name))
            else:
                if len(global_funcs_heap) < top_limit:
                    heappush(global_funcs_heap, (size, display_name))
                elif size > global_funcs_heap[0][0]:
                    heappushpop(global_funcs_heap, (size, display_name))

        if size > 0 and typ == "OBJECT":
            if bind == "LOCAL":
                if len(local_objects_heap) < top_limit:
                    heappush(local_objects_heap, (size, display_name))
                elif size > local_objects_heap[0][0]:
                    heappushpop(local_objects_heap, (size, display_name))
            else:
                if len(global_objects_heap) < top_limit:
                    heappush(global_objects_heap, (size, display_name))
                elif size > global_objects_heap[0][0]:
                    heappushpop(global_objects_heap, (size, display_name))

            if tokens:
                key = "::".join(tokens[:3]) if len(tokens) >= 3 else tokens[0]
            else:
                key = display_name

            if storage_class == "rodata":
                namespace_rodata[key] += size
                if len(rodata_objects_heap) < top_limit:
                    heappush(rodata_objects_heap, (size, display_name))
                elif size > rodata_objects_heap[0][0]:
                    heappushpop(rodata_objects_heap, (size, display_name))
            elif storage_class in {"rwdata", "common"}:
                namespace_rwdata[key] += size
                if len(rw_objects_heap) < top_limit:
                    heappush(rw_objects_heap, (size, display_name))
                elif size > rw_objects_heap[0][0]:
                    heappushpop(rw_objects_heap, (size, display_name))
            elif storage_class == "bss":
                namespace_bss[key] += size
                if len(bss_objects_heap) < top_limit:
                    heappush(bss_objects_heap, (size, display_name))
                elif size > bss_objects_heap[0][0]:
                    heappushpop(bss_objects_heap, (size, display_name))

    def _heap_to_list(heap: List[tuple[int, str]]) -> List[Dict[str, object]]:
        entries: List[Dict[str, object]] = []
        for size, symbol in nlargest(top_limit, heap):
            entries.append({"name": symbol, "size": size})
        return entries

    longest_entries: List[Dict[str, object]] = []
    for length, record in nlargest(top_limit, longest_names_heap):
        symbol_name, bind, typ, size = record
        longest_entries.append(
            {
                "name": symbol_name,
                "length": length,
                "bind": bind,
                "type": typ,
                "size": size,
            }
        )

    length_stats: Dict[str, float | int] = {}
    if name_lengths:
        sorted_lengths = sorted(name_lengths)
        count = len(sorted_lengths)
        total = sum(sorted_lengths)

        def percentile(p: float) -> int:
            if count == 1:
                return sorted_lengths[0]
            index = int(round(p * (count - 1)))
            return sorted_lengths[index]

        length_stats = {
            "count": count,
            "average": total / count,
            "p50": percentile(0.5),
            "p90": percentile(0.9),
            "p99": percentile(0.99),
            "max": sorted_lengths[-1],
        }

    return {
        "library": library.name,
        "path": library.as_posix(),
        "total_symbols": total_symbols,
        "defined_symbols": defined_symbols,
        "counts_by_bind": dict(counts_by_bind),
        "size_by_bind": dict(size_by_bind),
        "counts_by_kind": dict(counts_by_kind),
        "size_by_kind": dict(size_by_kind),
        "counts_by_storage": dict(counts_by_storage),
        "size_by_storage": dict(size_by_storage),
        "counts_by_type": dict(counts_by_type),
        "size_by_type": dict(size_by_type),
        "namespace_level3_all": namespace_level3_all.most_common(top_limit),
        "namespace_level3_local": namespace_level3_local.most_common(top_limit),
        "namespace_level3_global": namespace_level3_global.most_common(top_limit),
        "namespace_rodata": namespace_rodata.most_common(top_limit),
        "namespace_rwdata": namespace_rwdata.most_common(top_limit),
        "namespace_bss": namespace_bss.most_common(top_limit),
        "name_bytes_by_bind": dict(name_bytes_by_bind),
        "top_local_functions": _heap_to_list(local_funcs_heap),
        "top_global_functions": _heap_to_list(global_funcs_heap),
        "top_local_objects": _heap_to_list(local_objects_heap),
        "top_global_objects": _heap_to_list(global_objects_heap),
        "top_rodata_objects": _heap_to_list(rodata_objects_heap),
        "top_rw_objects": _heap_to_list(rw_objects_heap),
        "top_bss_objects": _heap_to_list(bss_objects_heap),
        "longest_names": longest_entries,
        "name_length_stats": length_stats,
    }


def compute_symbol_overlap(symbol_maps: Dict[str, Dict[str, object]]) -> Dict[str, object]:
    symbol_sets: Dict[str, Dict[str, int]] = {}
    for lib, payload in symbol_maps.items():
        entries = payload.get("symbols", [])
        library_symbols: Dict[str, int] = {}
        for entry in entries:
            demangled = entry.get("demangled")
            size = int(entry.get("size", 0))
            if not demangled:
                continue
            library_symbols[demangled] = size
        symbol_sets[lib] = library_symbols

    libraries = list(symbol_sets.keys())
    overlaps: Dict[str, object] = {}
    for i, lib_a in enumerate(libraries):
        for lib_b in libraries[i + 1 :]:
            symbols_a = symbol_sets[lib_a]
            symbols_b = symbol_sets[lib_b]
            shared = set(symbols_a).intersection(symbols_b)
            namespace_stats: Dict[str, Dict[str, int]] = {}
            top_shared = sorted(
                (
                    (
                        name,
                        symbols_a.get(name, 0),
                        symbols_b.get(name, 0),
                    )
                    for name in shared
                ),
                key=lambda item: max(item[1], item[2]),
                reverse=True,
            )[:25]

            for name in shared:
                size_a = symbols_a.get(name, 0)
                size_b = symbols_b.get(name, 0)
                tokens = [token for token in name.split("::") if token]
                if not tokens:
                    key = name
                elif len(tokens) >= 4:
                    key = "::".join(tokens[:4])
                elif len(tokens) >= 3:
                    key = "::".join(tokens[:3])
                elif len(tokens) >= 2:
                    key = "::".join(tokens[:2])
                else:
                    key = tokens[0]
                entry = namespace_stats.setdefault(
                    key, {"count": 0, "size_a": 0, "size_b": 0}
                )
                entry["count"] += 1
                entry["size_a"] += size_a
                entry["size_b"] += size_b

            top_namespaces = sorted(
                namespace_stats.items(),
                key=lambda item: item[1]["size_a"] + item[1]["size_b"],
                reverse=True,
            )[:15]

            overlaps[f"{lib_a}::{lib_b}"] = {
                "shared_count": len(shared),
                "top_symbols": [
                    {
                        "name": name,
                        "size_a": size_a,
                        "size_b": size_b,
                    }
                    for name, size_a, size_b in top_shared
                ],
                "top_namespaces": [
                    {
                        "namespace": namespace,
                        "count": stats["count"],
                        "size_a": stats["size_a"],
                        "size_b": stats["size_b"],
                    }
                    for namespace, stats in top_namespaces
                ],
            }

    if len(libraries) == 3:
        a, b, c = libraries
        shared_all = set(symbol_sets[a]).intersection(symbol_sets[b]).intersection(symbol_sets[c])
        overlaps["triple_overlap"] = {
            "shared_count": len(shared_all),
            "examples": sorted(list(shared_all))[:25],
        }

    return overlaps


def run_ldd(library: Path, verbose: bool = False) -> List[str]:
    try:
        result = run_command(["ldd", str(library)], verbose=verbose)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        return [exc.stderr.strip() or exc.stdout.strip()]
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def run_auditwheel(wheel_path: Path, verbose: bool = False) -> Optional[Dict[str, object]]:
    try:
        result = run_command(["auditwheel", "show", str(wheel_path)], verbose=verbose)
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        return {"error": exc.stderr or exc.stdout}

    stdout = result.stdout
    platform_tag = None
    constrained_tag = None
    external_libs: List[str] = []

    platform_match = re.search(r'platform tag: "([^"]+)"', stdout)
    if platform_match:
        platform_tag = platform_match.group(1)

    constrained_match = re.search(r'This constrains the platform tag to "([^"]+)"', stdout)
    if constrained_match:
        constrained_tag = constrained_match.group(1)

    libs_match = re.search(
        r"system-provided shared libraries:(.*?)(?:\n\n|$)", stdout, re.DOTALL
    )
    if libs_match:
        segment = libs_match.group(1)
        for token in segment.replace("{", " ").replace("}", " ").split(","):
            token = token.strip()
            if token.startswith("lib") and " " in token:
                external_libs.append(token.split()[0])

    return {
        "platform_tag": platform_tag,
        "constrained_tag": constrained_tag,
        "external_libs": external_libs,
        "raw_output": stdout,
    }


def write_json(path: Path, payload: Dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def build_compact_summary(
    inventory: Dict[str, object],
    sections: Dict[str, Dict[str, object]],
    symbols: Dict[str, Dict[str, object]],
    static_symbols: Dict[str, Dict[str, object]],
    runtime_deps: Dict[str, List[str]],
    overlap: Dict[str, object],
    auditwheel_report: Optional[Dict[str, object]],
) -> Dict[str, object]:
    files_by_name = {
        Path(entry["path"]).name: entry for entry in inventory.get("files", [])
    }
    libs: List[Dict[str, object]] = []
    for lib_name, section_info in sections.items():
        file_entry = files_by_name.get(lib_name)
        symbol_info = symbols.get(lib_name, {})
        static_info = static_symbols.get(lib_name, {})
        libs.append(
            {
                "name": lib_name,
                "size_bytes": file_entry["size"] if file_entry else None,
                "section_aggregates": section_info.get("aggregates"),
                "device_sections": section_info.get("device_sections", []),
                "device_overview": section_info.get("device_overview", {}),
                "sycl_device_kernels": section_info.get("sycl_device_kernels"),
                "dynamic_symbol_count": len(symbol_info.get("symbols", [])),
                "top_namespaces": symbol_info.get("namespace_level3", [])[:15],
                "static_symbols": {
                    "defined_symbols": static_info.get("defined_symbols"),
                    "counts_by_bind": static_info.get("counts_by_bind", {}),
                    "size_by_bind": static_info.get("size_by_bind", {}),
                    "counts_by_kind": static_info.get("counts_by_kind", {}),
                    "size_by_kind": static_info.get("size_by_kind", {}),
                    "counts_by_storage": static_info.get("counts_by_storage", {}),
                    "size_by_storage": static_info.get("size_by_storage", {}),
                    "name_bytes_by_bind": static_info.get("name_bytes_by_bind", {}),
                    "name_length_stats": static_info.get("name_length_stats", {}),
                    "namespace_level3_local": (
                        static_info.get("namespace_level3_local", [])[:15]
                    ),
                    "namespace_level3_global": (
                        static_info.get("namespace_level3_global", [])[:15]
                    ),
                    "namespace_rodata": static_info.get("namespace_rodata", [])[:15],
                    "namespace_rwdata": static_info.get("namespace_rwdata", [])[:15],
                    "namespace_bss": static_info.get("namespace_bss", [])[:15],
                    "top_local_functions": (
                        static_info.get("top_local_functions", [])[:10]
                    ),
                    "top_global_functions": (
                        static_info.get("top_global_functions", [])[:10]
                    ),
                    "top_local_objects": (
                        static_info.get("top_local_objects", [])[:10]
                    ),
                    "top_global_objects": (
                        static_info.get("top_global_objects", [])[:10]
                    ),
                    "top_rodata_objects": (
                        static_info.get("top_rodata_objects", [])[:10]
                    ),
                    "top_rw_objects": (
                        static_info.get("top_rw_objects", [])[:10]
                    ),
                    "top_bss_objects": (
                        static_info.get("top_bss_objects", [])[:10]
                    ),
                    "longest_names": static_info.get("longest_names", [])[:10],
                },
            }
        )

    compact_overlap = {}
    for key, value in overlap.items():
        if key == "triple_overlap":
            compact_overlap[key] = value
        else:
            compact_overlap[key] = {
                "shared_count": value.get("shared_count"),
                "top_symbols": value.get("top_symbols", [])[:10],
                "top_namespaces": value.get("top_namespaces", [])[:10],
            }

    return {
        "wheel_file": inventory.get("wheel_file"),
        "wheel_size_bytes": inventory.get("wheel_size_bytes"),
        "total_uncompressed_bytes": inventory.get("total_uncompressed_bytes"),
        "libraries": libs,
        "runtime_dependencies": runtime_deps,
        "symbol_overlap": compact_overlap,
        "auditwheel": auditwheel_report,
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    download_dir = output_dir / "download"
    extract_dir = output_dir / "extracted"
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if args.skip_download:
        wheels = sorted(download_dir.glob("*.whl"))
        if not wheels:
            raise FileNotFoundError("--skip-download requested but no wheel present")
        wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)
    else:
        wheel_path = download_wheel(args.package, download_dir, verbose=args.verbose)

    extract_wheel(wheel_path, extract_dir, verbose=args.verbose)
    inventory = build_file_inventory(extract_dir, wheel_path, analysis_dir)

    libraries = []
    for file_info in inventory["files"]:
        if file_info["category"] == "shared_library":
            libraries.append(extract_dir / file_info["path"])

    section_summaries: Dict[str, Dict[str, object]] = {}
    symbol_maps: Dict[str, Dict[str, object]] = {}
    static_symbol_maps: Dict[str, Dict[str, object]] = {}
    runtime_dependencies: Dict[str, List[str]] = {}

    for library_path in libraries:
        section_summary = summarize_sections(library_path, verbose=args.verbose)

        device_overview = section_summary.get("device_overview", {}) or {}
        if int(device_overview.get("image_bytes", 0)):
            device_kernel_summary = analyze_device_kernels(
                library_path, verbose=args.verbose
            )
            if device_kernel_summary:
                section_summary["sycl_device_kernels"] = device_kernel_summary
                write_json(
                    analysis_dir / f"device_kernels_{library_path.name}.json",
                    device_kernel_summary,
                )

        section_summaries[library_path.name] = section_summary
        write_json(analysis_dir / f"sections_{library_path.name}.json", section_summary)

        symbol_summary = collect_dynamic_symbols(library_path, verbose=args.verbose)
        symbol_maps[library_path.name] = symbol_summary
        write_json(analysis_dir / f"symbols_{library_path.name}.json", symbol_summary)

        static_summary = collect_static_symbol_stats(library_path, verbose=args.verbose)
        static_symbol_maps[library_path.name] = static_summary
        write_json(analysis_dir / f"static_symbols_{library_path.name}.json", static_summary)

        runtime_dependencies[library_path.name] = run_ldd(library_path, verbose=args.verbose)

    write_json(analysis_dir / "sections_summary.json", section_summaries)
    write_json(analysis_dir / "symbols_summary.json", symbol_maps)
    write_json(analysis_dir / "static_symbols_summary.json", static_symbol_maps)
    write_json(analysis_dir / "runtime_dependencies.json", runtime_dependencies)

    overlap = compute_symbol_overlap(symbol_maps)
    write_json(analysis_dir / "symbol_overlap.json", overlap)

    auditwheel_report = run_auditwheel(wheel_path, verbose=args.verbose)
    if auditwheel_report is not None:
        write_json(analysis_dir / "auditwheel_report.json", auditwheel_report)

    compact_payload = build_compact_summary(
        inventory,
        section_summaries,
        symbol_maps,
        static_symbol_maps,
        runtime_dependencies,
        overlap,
        auditwheel_report,
    )
    write_json(analysis_dir / "compact_summary.json", compact_payload)

    # Persist metadata files of interest for quick inspection without browsing the
    # extracted tree.
    metadata_root = next((extract_dir.glob("*.dist-info")), None)
    if metadata_root:
        for name in ["METADATA", "WHEEL", "LICENSE.txt", "RECORD"]:
            src = metadata_root / name
            if src.exists():
                shutil.copy2(src, analysis_dir / name)

    print(f"Analysis complete. Artefacts stored under {analysis_dir}")


if __name__ == "__main__":
    main()
