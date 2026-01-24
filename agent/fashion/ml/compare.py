# agent/fashion/ml/compare.py
"""Comparison functionality for dataset reports"""

import json
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ComparisonConfig:
    """Configuration for regression gates"""
    fail_on_regression: bool = False
    max_regress_ranker_mrr: Optional[float] = None
    max_regress_ranker_top1: Optional[float] = None
    max_regress_chooser_flat_rate: Optional[float] = None


def load_baseline_from_ci_summary(path: str) -> Dict[str, Any]:
    """Load baseline from CI summary JSON file
    
    Args:
        path: Path to ci_summary.json file
        
    Returns:
        Baseline data dictionary
    """
    with open(path, "r", encoding="utf-8-sig") as f:  # Handle UTF-8 BOM
        return json.load(f)


def load_baseline_from_report_json(path: str) -> Dict[str, Any]:
    """Load baseline from full report JSON file
    
    Args:
        path: Path to report.json file
        
    Returns:
        Baseline data dictionary
    """
    with open(path, "r", encoding="utf-8-sig") as f:  # Handle UTF-8 BOM
        return json.load(f)


def extract_compact_metrics(report_or_ci_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Extract compact metrics from report or CI summary
    
    Args:
        report_or_ci_summary: Full report or CI summary dictionary
        
    Returns:
        Compact metrics dictionary
    """
    # Try to extract from CI summary first
    ci_summary = report_or_ci_summary.get("ci_summary")
    if ci_summary:
        return extract_compact_metrics_from_ci_summary(ci_summary)
    
    # Fall back to extracting from full report
    return extract_compact_metrics_from_report(report_or_ci_summary)


def extract_compact_metrics_from_ci_summary(ci_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Extract compact metrics from CI summary
    
    Args:
        ci_summary: CI summary dictionary
        
    Returns:
        Compact metrics dictionary
    """
    return {
        "runs_used": ci_summary.get("runs_used", 0),
        "ranker": {
            "mrr": ci_summary.get("ranker", {}).get("mrr"),
            "top1_accuracy": ci_summary.get("ranker", {}).get("top1_accuracy"),
            "groups": ci_summary.get("ranker", {}).get("groups", 0)
        },
        "chooser": {
            "flat_rate": ci_summary.get("chooser", {}).get("flat_rate"),
            "groups": ci_summary.get("chooser", {}).get("groups", 0)
        },
        "gates": {
            "overall_ok": ci_summary.get("gates", {}).get("overall_ok", True),
            "fails": ci_summary.get("gates", {}).get("fails", 0),
            "warns": ci_summary.get("gates", {}).get("warns", 0)
        }
    }


def _extract_runs_used(d: dict) -> int:
    """Extract runs_used from report or sub-report with proper priority
    
    Args:
        d: Report or sub-report dictionary
        
    Returns:
        Number of runs used
    """
    w = d.get("window") or {}
    if isinstance(w, dict) and isinstance(w.get("used_runs"), int):
        return w["used_runs"]
    if isinstance(d.get("runs_used"), int):
        return d["runs_used"]
    if isinstance(d.get("runs"), int):
        return d["runs"]
    return 0


def extract_compact_metrics_from_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Extract compact metrics from full report
    
    Args:
        report: Full report dictionary
        
    Returns:
        Compact metrics dictionary
    """
    return {
        "runs_used": _extract_runs_used(report),
        "ranker": {
            "mrr": report.get("ranker", {}).get("mrr"),
            "top1_accuracy": report.get("ranker", {}).get("top1_accuracy"),
            "groups": report.get("ranker", {}).get("groups", 0)
        },
        "chooser": {
            "flat_rate": report.get("chooser", {}).get("flat_rate"),
            "groups": report.get("chooser", {}).get("groups", 0)
        },
        "gates": {
            "overall_ok": report.get("gates", {}).get("ok", True),
            "fails": 0,  # Not available in full report
            "warns": 0   # Not available in full report
        }
    }


def calculate_delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate delta between current and baseline metrics
    
    Args:
        current: Current metrics
        baseline: Baseline metrics
        
    Returns:
        Delta metrics dictionary
    """
    delta = {}
    
    # runs_used delta
    curr_runs = current.get("runs_used", 0)
    base_runs = baseline.get("runs_used", 0)
    if curr_runs is not None and base_runs is not None:
        delta["runs_used"] = curr_runs - base_runs
    
    # ranker deltas
    curr_ranker = current.get("ranker", {})
    base_ranker = baseline.get("ranker", {})
    delta_ranker = {}
    
    for metric in ["mrr", "top1_accuracy"]:
        curr_val = curr_ranker.get(metric)
        base_val = base_ranker.get(metric)
        if curr_val is not None and base_val is not None:
            delta_ranker[metric] = curr_val - base_val
    
    if delta_ranker:
        delta["ranker"] = delta_ranker
    
    # chooser deltas
    curr_chooser = current.get("chooser", {})
    base_chooser = baseline.get("chooser", {})
    delta_chooser = {}
    
    curr_flat = curr_chooser.get("flat_rate")
    base_flat = base_chooser.get("flat_rate")
    if curr_flat is not None and base_flat is not None:
        delta_chooser["flat_rate"] = curr_flat - base_flat
    
    if delta_chooser:
        delta["chooser"] = delta_chooser
    
    return delta


def get_metric_status(current_val: Optional[float], baseline_val: Optional[float], 
                     delta_val: Optional[float], is_regression_bad: bool = True) -> str:
    """Get status for a single metric comparison
    
    Args:
        current_val: Current metric value
        baseline_val: Baseline metric value
        delta_val: Delta value (current - baseline)
        is_regression_bad: Whether regression (negative delta) is bad
        
    Returns:
        Status string: "improved", "regressed", "same", "missing_baseline", "missing_current"
    """
    if baseline_val is None:
        return "missing_baseline"
    if current_val is None:
        return "missing_current"
    if delta_val is None:
        return "missing_current"
    
    if abs(delta_val) < 1e-9:  # Essentially zero
        return "same"
    
    if is_regression_bad:
        # For metrics where lower is worse (MRR, Top1)
        if delta_val > 0:
            return "improved"
        else:
            return "regressed"
    else:
        # For metrics where lower is better (flat_rate)
        if delta_val < 0:
            return "improved"
        else:
            return "regressed"


def build_comparison(current_compact: Dict[str, Any], baseline_compact: Dict[str, Any], 
                   source_info: Dict[str, Any]) -> Dict[str, Any]:
    """Build comparison structure
    
    Args:
        current_compact: Current compact metrics
        baseline_compact: Baseline compact metrics
        source_info: Information about baseline source
        
    Returns:
        Comparison dictionary
    """
    # Calculate delta
    delta = calculate_delta(current_compact, baseline_compact)
    
    # Calculate status for each metric
    status = {}
    
    # runs_used status (more runs is better, so regression is bad)
    curr_runs = current_compact.get("runs_used")
    base_runs = baseline_compact.get("runs_used")
    delta_runs = delta.get("runs_used")
    status["runs_used"] = get_metric_status(curr_runs, base_runs, delta_runs, is_regression_bad=True)
    
    # ranker metrics (higher is better)
    curr_ranker = current_compact.get("ranker", {})
    base_ranker = baseline_compact.get("ranker", {})
    delta_ranker = delta.get("ranker", {})
    
    for metric in ["mrr", "top1_accuracy"]:
        curr_val = curr_ranker.get(metric)
        base_val = base_ranker.get(metric)
        delta_val = delta_ranker.get(metric)
        status[f"ranker_{metric}"] = get_metric_status(curr_val, base_val, delta_val, is_regression_bad=True)
    
    # chooser flat_rate (lower is better)
    curr_flat = current_compact.get("chooser", {}).get("flat_rate")
    base_flat = baseline_compact.get("chooser", {}).get("flat_rate")
    delta_flat = delta.get("chooser", {}).get("flat_rate")
    status["chooser_flat_rate"] = get_metric_status(curr_flat, base_flat, delta_flat, is_regression_bad=False)
    
    # Determine overall status
    # Overall is regressed if any key metric regressed
    key_metrics = ["ranker_mrr", "ranker_top1_accuracy", "chooser_flat_rate"]
    regressed_count = sum(1 for metric in key_metrics if status.get(metric) == "regressed")
    improved_count = sum(1 for metric in key_metrics if status.get(metric) == "improved")
    
    if regressed_count > 0:
        overall_status = "regressed"
    elif improved_count > 0:
        overall_status = "improved"
    else:
        overall_status = "same"
    
    # Check for missing data
    missing_count = sum(1 for metric in key_metrics if status.get(metric) in ["missing_baseline", "missing_current"])
    if missing_count > 0:
        overall_status = "unknown"
    
    status["overall"] = overall_status
    
    return {
        "baseline_source": source_info,
        "baseline": baseline_compact,
        "current": current_compact,
        "delta": delta,
        "status": status
    }


def apply_regression_gates(comparison: Dict[str, Any], config: ComparisonConfig) -> Tuple[bool, Dict[str, Any]]:
    """Apply regression gates to comparison
    
    Args:
        comparison: Comparison dictionary
        config: Regression gate configuration
        
    Returns:
        Tuple of (failed, gate_results)
    """
    if not config.fail_on_regression:
        return False, {}
    
    gate_results = {}
    failed = False
    
    delta = comparison.get("delta", {})
    status = comparison.get("status", {})
    
    # Check ranker MRR regression
    if config.max_regress_ranker_mrr is not None:
        mrr_delta = delta.get("ranker", {}).get("mrr")
        if mrr_delta is not None and mrr_delta < -config.max_regress_ranker_mrr:
            gate_results["ranker_mrr"] = {
                "failed": True,
                "threshold": config.max_regress_ranker_mrr,
                "actual": mrr_delta,
                "message": f"MRR regressed by {abs(mrr_delta):.3f} (threshold: {config.max_regress_ranker_mrr})"
            }
            failed = True
        else:
            gate_results["ranker_mrr"] = {
                "failed": False,
                "threshold": config.max_regress_ranker_mrr,
                "actual": mrr_delta,
                "message": "MRR within acceptable range"
            }
    
    # Check ranker Top1 regression
    if config.max_regress_ranker_top1 is not None:
        top1_delta = delta.get("ranker", {}).get("top1_accuracy")
        if top1_delta is not None and top1_delta < -config.max_regress_ranker_top1:
            gate_results["ranker_top1"] = {
                "failed": True,
                "threshold": config.max_regress_ranker_top1,
                "actual": top1_delta,
                "message": f"Top1 regressed by {abs(top1_delta):.3f} (threshold: {config.max_regress_ranker_top1})"
            }
            failed = True
        else:
            gate_results["ranker_top1"] = {
                "failed": False,
                "threshold": config.max_regress_ranker_top1,
                "actual": top1_delta,
                "message": "Top1 within acceptable range"
            }
    
    # Check chooser flat_rate regression (increase is bad)
    if config.max_regress_chooser_flat_rate is not None:
        flat_delta = delta.get("chooser", {}).get("flat_rate")
        if flat_delta is not None and flat_delta > config.max_regress_chooser_flat_rate:
            gate_results["chooser_flat_rate"] = {
                "failed": True,
                "threshold": config.max_regress_chooser_flat_rate,
                "actual": flat_delta,
                "message": f"Flat rate increased by {flat_delta:.3f} (threshold: {config.max_regress_chooser_flat_rate})"
            }
            failed = True
        else:
            gate_results["chooser_flat_rate"] = {
                "failed": False,
                "threshold": config.max_regress_chooser_flat_rate,
                "actual": flat_delta,
                "message": "Flat rate within acceptable range"
            }
    
    return failed, gate_results
