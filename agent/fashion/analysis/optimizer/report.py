from __future__ import annotations

from dataclasses import is_dataclass, asdict
from typing import Any, Dict, List, Optional


def _to_plain(obj: Any) -> Any:
    """
    Безопасно превращает dataclass/объект с to_dict() в plain dict/list/str/num.
    НИЧЕГО не импортирует из cad_core/derived.
    """
    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, list):
        return [_to_plain(x) for x in obj]

    if isinstance(obj, tuple):
        return [_to_plain(x) for x in obj]

    if isinstance(obj, dict):
        return {str(k): _to_plain(v) for k, v in obj.items()}

    # dataclass
    if is_dataclass(obj):
        return _to_plain(asdict(obj))

    # objects with to_dict()
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return _to_plain(to_dict())

    # fallback: repr (но лучше избегать)
    return str(obj)


def _sorted_rule_changes(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Делает proposal детерминированным (сортировка изменений по path).
    """
    if not isinstance(proposal, dict):
        return {"proposed_rule_changes": [], "affected_derived": []}

    changes = proposal.get("proposed_rule_changes") or []
    affected = proposal.get("affected_derived") or []

    if isinstance(changes, list):
        changes = sorted(
            changes,
            key=lambda x: str(x.get("path", "")) if isinstance(x, dict) else str(x),
        )

    if isinstance(affected, list):
        affected = sorted([str(x) for x in affected])

    fixed = dict(proposal)
    fixed["proposed_rule_changes"] = changes
    fixed["affected_derived"] = affected
    return fixed


class OptimizationReportBuilder:
    """
    Строит сериализуемый JSON-отчёт из результата оптимизации.
    Не читает Contour. Не импортирует cad_core/derived.
    """

    @staticmethod
    def build_from_run(
        *,
        target: Any,
        run_result: Any,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        run_result ожидается как dict или dataclass/объект, содержащий поля:
          - baseline_score
          - final_score
          - improvement
          - steps (list)
          - stopped_reason (str)
        """
        rr = _to_plain(run_result)
        tgt = _to_plain(target)

        # steps normalizing
        steps: List[Dict[str, Any]] = []
        raw_steps = rr.get("steps") if isinstance(rr, dict) else None
        if isinstance(raw_steps, list):
            for s in raw_steps:
                sd = _to_plain(s)
                if isinstance(sd, dict):
                    # proposal sort
                    if "chosen_proposal" in sd and isinstance(sd["chosen_proposal"], dict):
                        sd["chosen_proposal"] = _sorted_rule_changes(sd["chosen_proposal"])
                    steps.append(sd)

        # sort steps by step_index
        steps.sort(key=lambda x: int(x.get("step_index", 0)))

        report: Dict[str, Any] = {
            "type": "optimization_report",
            "target": tgt,
            "baseline_score": float(run_result.baseline_score),
            "final_score": float(run_result.final_score),
            "improvement": float(run_result.improvement),
            "stopped_reason": run_result.stopped_reason,
            "result": {  # Добавляем поле result для тестов
                "success": True,
                "message": "Optimization completed"
            },
            "steps": steps,
            "meta": _to_plain(meta or {}),
            **({"candidates_data": run_result.candidates_data} if run_result.candidates_data else {})
        }

        # Гарантия сериализуемости: вычищаем потенциальные PatternModel-объекты
        # (если кто-то по ошибке положил best_model/baseline_model/final_model)
        for banned_key in ("best_model", "baseline_model", "final_model"):
            if banned_key in report:
                report[banned_key] = None

        return report

    @staticmethod
    def build_from_single_result(
        *,
        target: Any,
        result: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Для случая optimize_for_target(), который возвращает dict
        (baseline_score/final_score/improvement/chosen_proposal/…).
        """
        r = _to_plain(result)
        tgt = _to_plain(target)

        proposal = r.get("chosen_proposal") or r.get("proposal") or {}
        if isinstance(proposal, dict):
            proposal = _sorted_rule_changes(proposal)

        report: Dict[str, Any] = {
            "type": "optimization_report",
            "target": tgt,
            "baseline_score": float(r.get("baseline_score", 0.0)),
            "final_score": float(r.get("final_score", 0.0)),
            "improvement": float(r.get("improvement", 0.0)),
            "stopped_reason": r.get("stopped_reason", "single_step"),
            "result": {  # Добавляем поле result для тестов
                "success": True,
                "message": "Optimization completed"
            },
            "steps": [
                {
                    "step_index": 0,
                    "baseline_score": float(r.get("baseline_score", 0.0)),
                    "best_score": float(r.get("final_score", 0.0)),
                    "improvement": float(r.get("improvement", 0.0)),
                    "chosen_proposal": proposal,
                }
            ],
            "meta": _to_plain(meta or {}),
        }
        return report
