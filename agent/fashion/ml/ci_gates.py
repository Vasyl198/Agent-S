# agent/fashion/ml/ci_gates.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GateConfig:
    # Hard minimums
    min_runs: int = 50

    # Ranker quality
    min_ranker_mrr: float = 0.4
    min_ranker_top1: float = 0.2

    # Chooser diagnostics (optional; set to None to disable)
    max_chooser_flat_rate: Optional[float] = None

    # If True, treat warnings like failures
    fail_on_warn: bool = False
    
    # 7.5.5: Applicability requirements
    require_ranker: bool = False
    require_chooser: bool = False


@dataclass(frozen=True)
class GateViolation:
    key: str
    message: str
    actual: Any = None
    expected: Any = None
    severity: str = "fail"  # "fail" | "warn"


@dataclass(frozen=True)
class GateResult:
    ok: bool
    violations: List[GateViolation]


def _get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def decide_gates(report: Dict[str, Any], cfg: GateConfig) -> GateResult:
    v: List[GateViolation] = []

    runs = _get(report, "runs", 0)
    if not isinstance(runs, int):
        runs = 0

    if runs < cfg.min_runs:
        v.append(GateViolation(
            key="runs.min",
            message="Too few runs for reliable metrics",
            actual=runs,
            expected=f">= {cfg.min_runs}",
            severity="fail",
        ))

    # Ranker metrics may be absent if dataset has no pred_score
    ranker_mrr = _get(report, "ranker.mrr", None)
    ranker_top1 = _get(report, "ranker.top1_accuracy", None)
    ranker_groups = _get(report, "ranker.groups", 0)
    
    # Check if ranker metrics are actually missing
    ranker_missing = (ranker_mrr is None or ranker_top1 is None or ranker_groups == 0)

    if ranker_missing:
        if cfg.require_ranker:
            v.append(GateViolation(
                key="ranker.present",
                message="Ranker metrics missing (required for this pipeline/scope)",
                actual={"mrr": ranker_mrr, "top1": ranker_top1, "groups": ranker_groups},
                expected="ranker.mrr and ranker.top1_accuracy present",
                severity="fail",
            ))
        # If not required, skip (no violation)
    else:
        if float(ranker_mrr) < cfg.min_ranker_mrr:
            v.append(GateViolation(
                key="ranker.mrr",
                message="Ranker MRR below threshold",
                actual=float(ranker_mrr),
                expected=f">= {cfg.min_ranker_mrr}",
                severity="fail",
            ))
        if float(ranker_top1) < cfg.min_ranker_top1:
            v.append(GateViolation(
                key="ranker.top1_accuracy",
                message="Ranker top1_accuracy below threshold",
                actual=float(ranker_top1),
                expected=f">= {cfg.min_ranker_top1}",
                severity="fail",
            ))

    # Chooser flat-rate gate (optional)
    if cfg.max_chooser_flat_rate is not None:
        flat_rate = _get(report, "chooser.flat_rate", None)
        chooser_groups = _get(report, "chooser.groups", 0)
        chooser_missing = (flat_rate is None or chooser_groups == 0)
        
        if chooser_missing:
            if cfg.require_chooser:
                v.append(GateViolation(
                    key="chooser.flat_rate",
                    message="Chooser flat_rate missing (required for this pipeline/scope)",
                    actual={"flat_rate": flat_rate, "groups": chooser_groups},
                    expected=f"<= {cfg.max_chooser_flat_rate}",
                    severity="warn",
                ))
            # If not required, skip (no violation)
        else:
            sev = "fail" if cfg.fail_on_warn else "warn"
            if float(flat_rate) > cfg.max_chooser_flat_rate:
                v.append(GateViolation(
                    key="chooser.flat_rate",
                    message="Chooser appears too flat too often",
                    actual=float(flat_rate),
                    expected=f"<= {cfg.max_chooser_flat_rate}",
                    severity=sev,
                ))

    ok = all(x.severity != "fail" for x in v)
    return GateResult(ok=ok, violations=v)
