#!/usr/bin/env python3
"""Check for size regression in oneDAL wheel and binaries.

This script compares current binary sizes against established baselines
and fails if growth exceeds specified thresholds.

Usage:
    python3 check_size_regression.py [--max-growth 5%] [--baseline baseline.json]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis-dir",
        default="build/wheel_analysis/analysis",
        help="Directory containing current analysis"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Baseline JSON file to compare against"
    )
    parser.add_argument(
        "--max-growth",
        default="5%",
        help="Maximum allowed size growth (percentage or absolute bytes)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save comparison results to JSON file"
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current sizes as new baseline"
    )
    return parser.parse_args()


def load_current_sizes(analysis_dir: Path) -> Dict[str, int]:
    """Load current binary sizes from analysis."""
    sizes = {}
    
    # Load wheel size
    compact_path = analysis_dir / "compact_summary.json"
    if compact_path.exists():
        with open(compact_path, "r") as f:
            data = json.load(f)
            sizes["wheel_compressed"] = data.get("wheel_size_bytes", 0)
            sizes["wheel_uncompressed"] = data.get("total_uncompressed_bytes", 0)
            
            # Library sizes
            for lib in data.get("libraries", []):
                name = lib.get("name", "")
                size = lib.get("size_bytes", 0)
                if name and size:
                    sizes[f"library_{name}"] = size
                    
                # Track device payload separately
                device_overview = lib.get("device_overview", {})
                if device_overview:
                    total_device = device_overview.get("total_bytes", 0)
                    if total_device:
                        sizes[f"device_{name}"] = total_device
    
    # Load section sizes
    sections_path = analysis_dir / "sections_summary.json"
    if sections_path.exists():
        with open(sections_path, "r") as f:
            sections_data = json.load(f)
            for lib_name, lib_data in sections_data.items():
                aggregates = lib_data.get("aggregates", {})
                for section_type, size in aggregates.items():
                    sizes[f"section_{lib_name}_{section_type}"] = size
    
    return sizes


def parse_threshold(threshold_str: str) -> Tuple[bool, float]:
    """Parse threshold string into (is_percentage, value)."""
    if threshold_str.endswith("%"):
        return True, float(threshold_str.rstrip("%")) / 100.0
    else:
        # Assume bytes, allow suffixes
        multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}
        for suffix, mult in multipliers.items():
            if threshold_str.upper().endswith(suffix):
                return False, float(threshold_str[:-1]) * mult
        return False, float(threshold_str)


def check_regression(
    current: Dict[str, int], 
    baseline: Dict[str, int], 
    max_growth: str
) -> Tuple[bool, list]:
    """Check if any sizes exceed growth threshold."""
    is_pct, threshold = parse_threshold(max_growth)
    
    failures = []
    
    for key, current_size in current.items():
        if key not in baseline:
            # New component, not a regression
            print(f"NEW: {key} = {current_size / (1024**2):.2f} MiB")
            continue
            
        baseline_size = baseline[key]
        growth = current_size - baseline_size
        
        if growth <= 0:
            # Size decreased, good!
            continue
            
        if is_pct:
            growth_pct = growth / baseline_size if baseline_size > 0 else float('inf')
            if growth_pct > threshold:
                failures.append({
                    "component": key,
                    "baseline": baseline_size,
                    "current": current_size,
                    "growth": growth,
                    "growth_pct": growth_pct * 100
                })
        else:
            if growth > threshold:
                failures.append({
                    "component": key,
                    "baseline": baseline_size,
                    "current": current_size,
                    "growth": growth,
                    "growth_pct": (growth / baseline_size * 100) if baseline_size > 0 else 0
                })
    
    return len(failures) == 0, failures


def format_size(size_bytes: int) -> str:
    """Format bytes as human readable."""
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TiB"


def save_baseline(sizes: Dict[str, int], path: Path) -> None:
    """Save current sizes as baseline."""
    baseline = {
        "format_version": 1,
        "sizes": sizes,
        "metadata": {
            "component_count": len(sizes),
            "total_size": sum(sizes.values())
        }
    }
    
    with open(path, "w") as f:
        json.dump(baseline, f, indent=2)
    
    print(f"Baseline saved to {path}")


def main():
    args = parse_args()
    analysis_dir = Path(args.analysis_dir)
    
    # Load current sizes
    current_sizes = load_current_sizes(analysis_dir)
    if not current_sizes:
        print("ERROR: No size data found in analysis directory")
        sys.exit(1)
    
    print(f"Loaded {len(current_sizes)} size metrics")
    
    # Save baseline if requested
    if args.save_baseline:
        baseline_path = args.baseline or Path("size_baseline.json")
        save_baseline(current_sizes, baseline_path)
        return
    
    # Load baseline for comparison
    if not args.baseline:
        print("No baseline specified. Current sizes:")
        for name, size in sorted(current_sizes.items()):
            if size > 1024 * 1024:  # Only show > 1 MiB
                print(f"  {name}: {format_size(size)}")
        return
    
    if not args.baseline.exists():
        print(f"ERROR: Baseline file not found: {args.baseline}")
        sys.exit(1)
        
    with open(args.baseline, "r") as f:
        baseline_data = json.load(f)
        baseline_sizes = baseline_data.get("sizes", baseline_data)
    
    # Check for regression
    passed, failures = check_regression(current_sizes, baseline_sizes, args.max_growth)
    
    # Report results
    if passed:
        print(f"✓ Size check PASSED (threshold: {args.max_growth})")
        
        # Show improvements
        improvements = []
        for key in current_sizes:
            if key in baseline_sizes:
                reduction = baseline_sizes[key] - current_sizes[key]
                if reduction > 1024 * 1024:  # > 1 MiB reduction
                    improvements.append((key, reduction))
        
        if improvements:
            print("\nSize improvements:")
            for name, reduction in sorted(improvements, key=lambda x: x[1], reverse=True):
                print(f"  {name}: -{format_size(reduction)}")
    else:
        print(f"✗ Size check FAILED (threshold: {args.max_growth})")
        print(f"\n{len(failures)} components exceed growth threshold:")
        
        for failure in sorted(failures, key=lambda x: x["growth"], reverse=True):
            print(f"\n  {failure['component']}:")
            print(f"    Baseline: {format_size(failure['baseline'])}")
            print(f"    Current:  {format_size(failure['current'])}")
            print(f"    Growth:   {format_size(failure['growth'])} "
                  f"({failure['growth_pct']:.1f}%)")
    
    # Save comparison results if requested
    if args.output:
        results = {
            "passed": passed,
            "threshold": args.max_growth,
            "failures": failures,
            "current_sizes": current_sizes,
            "baseline_sizes": baseline_sizes
        }
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()