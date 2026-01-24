# agent/fashion/ml/ci_badge.py
"""CI badge generation for Shields.io and similar badge systems"""

from typing import Dict, Any, Optional


def badge_color_for_status(ok: bool) -> str:
    """Return Shields.io color for status"""
    return "brightgreen" if ok else "red"


def fmt_float(x: Optional[float], digits: int = 3) -> str:
    """Format float for badge display"""
    if x is None:
        return "n/a"
    return f"{x:.{digits}f}"


def build_badges(report: Dict[str, Any], *, title: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Build CI badges JSON for Shields.io
    
    Args:
        report: Dataset report JSON
        title: Optional prefix for badge keys
        
    Returns:
        Dict of badge JSON objects
    """
    prefix = f"{title}_" if title else ""
    
    # Get data from ci_summary if available, otherwise from top level
    source = report.get("ci_summary", report)
    
    badges = {}
    
    # Gates badge (always present)
    gates_ok = source.get("ok", True) if "ci_summary" in report else report.get("ok", True)
    badges[f"{prefix}gates"] = {
        "schemaVersion": 1,
        "label": f"{title} gates" if title else "ml gates",
        "message": "OK" if gates_ok else "FAIL",
        "color": badge_color_for_status(gates_ok)
    }
    
    # Ranker MRR badge
    ranker_data = source.get("ranker", {})
    ranker_mrr = ranker_data.get("mrr")
    if ranker_mrr is not None:
        badges[f"{prefix}ranker_mrr"] = {
            "schemaVersion": 1,
            "label": f"{title} ranker mrr" if title else "ranker mrr",
            "message": f"mrr {fmt_float(ranker_mrr)}",
            "color": "brightgreen" if ranker_mrr >= 0.5 else "orange" if ranker_mrr >= 0.3 else "red"
        }
    
    # Ranker Top1 badge
    ranker_top1 = ranker_data.get("top1_accuracy")
    if ranker_top1 is not None:
        badges[f"{prefix}ranker_top1"] = {
            "schemaVersion": 1,
            "label": f"{title} ranker top1" if title else "ranker top1",
            "message": f"top1 {fmt_float(ranker_top1)}",
            "color": "brightgreen" if ranker_top1 >= 0.8 else "orange" if ranker_top1 >= 0.6 else "red"
        }
    
    # Chooser flat rate badge
    chooser_data = source.get("chooser", {})
    chooser_flat = chooser_data.get("flat_rate")
    if chooser_flat is not None:
        badges[f"{prefix}chooser_flat"] = {
            "schemaVersion": 1,
            "label": f"{title} chooser flat" if title else "chooser flat",
            "message": f"flat {fmt_float(chooser_flat)}",
            "color": "brightgreen" if chooser_flat <= 0.1 else "orange" if chooser_flat <= 0.3 else "red"
        }
    
    return badges


def build_delta_badges(report: Dict[str, Any], *, title: Optional[str] = None, compact: bool = False) -> Dict[str, Dict[str, Any]]:
    """Build delta comparison badges JSON for Shields.io
    
    Args:
        report: Dataset report JSON with comparison data
        title: Optional prefix for badge keys
        compact: If True, only generate regression badge
        
    Returns:
        Dict of badge JSON objects
    """
    prefix = f"{title}_" if title else ""
    badges = {}
    
    # Only generate if comparison exists
    if "comparison" not in report:
        return badges
    
    comparison = report["comparison"]
    delta = comparison.get("delta", {})
    status = comparison.get("status", {})
    regression_gates = report.get("regression_gates", {})
    
    # Regression badge (always present if comparison exists)
    regression_failed = False
    if regression_gates:
        # Check if any gate failed
        regression_failed = any(gate.get("failed", False) for gate in regression_gates.values())
    
    badges[f"{prefix}regression"] = {
        "schemaVersion": 1,
        "label": f"{title} regression" if title else "regression",
        "message": "FAIL" if regression_failed else "OK",
        "color": "red" if regression_failed else "brightgreen"
    }
    
    if compact:
        return badges
    
    # Delta badges
    
    # MRR delta
    delta_mrr = delta.get("ranker", {}).get("mrr")
    if delta_mrr is not None:
        badges[f"{prefix}delta_mrr"] = {
            "schemaVersion": 1,
            "label": f"{title} delta_mrr" if title else "delta_mrr",
            "message": f"delta_mrr {fmt_float(delta_mrr)}",
            "color": "brightgreen" if delta_mrr >= 0 else "red"
        }
    
    # Top1 delta
    delta_top1 = delta.get("ranker", {}).get("top1_accuracy")
    if delta_top1 is not None:
        badges[f"{prefix}delta_top1"] = {
            "schemaVersion": 1,
            "label": f"{title} delta_top1" if title else "delta_top1",
            "message": f"delta_top1 {fmt_float(delta_top1)}",
            "color": "brightgreen" if delta_top1 >= 0 else "red"
        }
    
    # Flat rate delta
    delta_flat = delta.get("chooser", {}).get("flat_rate")
    if delta_flat is not None:
        badges[f"{prefix}delta_flat"] = {
            "schemaVersion": 1,
            "label": f"{title} delta_flat" if title else "delta_flat",
            "message": f"delta_flat {fmt_float(delta_flat)}",
            "color": "brightgreen" if delta_flat <= 0 else "red"  # flat rate growth is bad
        }
    
    return badges


def write_text(path: str, content: str, *, encoding: str = "utf-8-sig") -> None:
    """Write text file with UTF-8 BOM for Windows compatibility"""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)
