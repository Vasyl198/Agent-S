from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from agent.fashion.ml.pattern_features import extract_pattern_features


@dataclass(frozen=True)
class Row:
    group_id: str
    x: Dict[str, Any]
    y_score: float
    y_is_chosen: int


def _one_hot(prefix: str, value: Any) -> Dict[str, float]:
    if value is None:
        return {}
    return {f"{prefix}={value}": 1.0}


def _num(prefix: str, value: Any) -> Dict[str, float]:
    try:
        return {prefix: float(value)}
    except Exception:
        return {prefix: 0.0}


def featurize_candidate(sample: Dict[str, Any], cand: Dict[str, Any]) -> Dict[str, float]:
    """
    Простые признаки:
    - goal/role (one-hot)
    - by (float)
    - proposal.type (one-hot)
    - proposal.role/goal/by если присутствуют
    - длины/структуры (кол-во изменений)
    - 7.0.2: новые признаки для лучшего ранжирования
    """
    target = (sample.get("input") or {}).get("target") or {}
    proposal = cand.get("proposal") or {}

    x: Dict[str, float] = {}
    x.update(_one_hot("goal", target.get("goal")))
    x.update(_one_hot("role", target.get("role")))
    x.update(_num("by", target.get("by")))

    x.update(_one_hot("proposal_type", proposal.get("type")))

    # если proposal дублирует goal/role/by — тоже полезно
    x.update(_one_hot("p_goal", proposal.get("goal")))
    x.update(_one_hot("p_role", proposal.get("role")))
    x.update(_num("p_by", proposal.get("by")))

    # rule changes (если появятся в будущем)
    prc = proposal.get("proposed_rule_changes")
    if isinstance(prc, list):
        x["p_rule_changes_count"] = float(len(prc))
    else:
        x["p_rule_changes_count"] = 0.0

    # constraint_ok
    x["constraint_ok"] = 1.0 if cand.get("constraint_ok", True) else 0.0

    # 7.0.2: новые признаки для лучшего ранжирования
    t_goal = target.get("goal")
    t_role = target.get("role")
    t_by = float(target.get("by") or 0.0)

    p_goal = proposal.get("goal")
    p_role = proposal.get("role")
    p_by = float(proposal.get("by") or 0.0)

    # Совпадение goal/role
    x["same_goal"] = 1.0 if (p_goal is not None and p_goal == t_goal) else 0.0
    x["same_role"] = 1.0 if (p_role is not None and p_role == t_role) else 0.0

    # Разница в by
    diff = abs(p_by - t_by)
    x["by_diff"] = diff
    x["by_signed"] = p_by - t_by

    # Пара goal|role
    if t_goal is not None and t_role is not None:
        x[f"goal_role={t_goal}|{t_role}"] = 1.0

    # 7.2.3: Добавляем pattern features
    pf = extract_pattern_features(sample)
    for k, v in pf.items():
        x[f"pf.{k}"] = v

    return x


def extract_rows_from_sample(sample: Dict[str, Any]) -> List[Row]:
    run_id = sample.get("run_id") or "unknown"
    opt = (sample.get("optimization") or {})
    candidates = opt.get("candidates") or []
    chosen_index = opt.get("chosen_index")

    rows: List[Row] = []
    for idx, cand in enumerate(candidates):
        if not isinstance(cand, dict):
            continue
        score = cand.get("score", 0.0)
        try:
            y_score = float(score)
        except Exception:
            y_score = 0.0
        y_is_chosen = 1 if (chosen_index is not None and idx == int(chosen_index)) else 0
        x = featurize_candidate(sample, cand)
        rows.append(Row(
            group_id=run_id,
            x=x,
            y_score=y_score,
            y_is_chosen=y_is_chosen
        ))
    return rows


def vectorize(rows: List[Row]) -> Tuple[List[Dict[str, float]], List[float], List[int], List[str]]:
    X = [r.x for r in rows]
    y_score = [r.y_score for r in rows]
    y_is_chosen = [r.y_is_chosen for r in rows]
    groups = [r.group_id for r in rows]
    return X, y_score, y_is_chosen, groups
