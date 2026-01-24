# agent/fashion/cli/exit_codes.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ExitCode:
    OK = 0
    CLI_USAGE_ERROR = 2

    INVALID_TARGET = 10
    INVALID_INPUT = 11

    CONSTRAINT_VIOLATION = 20
    NO_IMPROVEMENT_STRICT = 21

    INTERNAL_ERROR = 30


@dataclass(frozen=True)
class ExitDecision:
    code: int
    reason: str
    detail: Optional[str] = None


def decide_exit_code(report: dict, *, strict: bool) -> ExitDecision:
    """
    report: optimization_report dict (тот что ты печатаешь в JSON)
    strict: включает строгие проверки
    """
    # Минимальная защита от неожиданных форматов
    result = report.get("result") or {}
    success = bool(result.get("success", False))

    if not success:
        # Если неуспех, но нет более точной причины
        return ExitDecision(ExitCode.CONSTRAINT_VIOLATION if strict else ExitCode.INTERNAL_ERROR,
                            "optimization_failed")

    # Constraint violations — зависит от того, как ты их кладёшь в report.
    # Ниже — универсальные варианты; подстроим под твою структуру.
    violations = None
    # варианты расположения
    if isinstance(report.get("constraints"), dict):
        violations = report["constraints"].get("violations")
    if violations is None and isinstance(report.get("constraint_violations"), list):
        violations = report.get("constraint_violations")

    has_violations = bool(violations)

    if strict and has_violations:
        return ExitDecision(ExitCode.CONSTRAINT_VIOLATION, "constraint_violation")

    improvement = report.get("improvement")
    try:
        improvement_val = float(improvement) if improvement is not None else 0.0
    except Exception:
        improvement_val = 0.0

    if strict and improvement_val <= 0.0:
        return ExitDecision(ExitCode.NO_IMPROVEMENT_STRICT, "no_improvement_strict")

    return ExitDecision(ExitCode.OK, "ok")
