# agent/fashion/ml/metrics.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
import math


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _is_finite(x: Any) -> bool:
    try:
        v = float(x)
        return math.isfinite(v)
    except Exception:
        return False


def _group_by(items: Iterable[Any], key_fn) -> Dict[str, List[Any]]:
    out: Dict[str, List[Any]] = {}
    for it in items:
        k = key_fn(it)
        if k is None:
            continue
        out.setdefault(str(k), []).append(it)
    return out


def _argmax(values: List[float]) -> int:
    # deterministic argmax (first max)
    best_i = 0
    best_v = values[0]
    for i, v in enumerate(values[1:], 1):
        if v > best_v:
            best_v = v
            best_i = i
    return best_i


def _rank_of_index(scores: List[float], idx: int, descending: bool = True) -> int:
    """
    Returns 1-based rank position of item idx when sorting by scores.
    Ties: higher score first; stable by index.
    """
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i) if descending else (scores[i], i))
    for r, i in enumerate(order, 1):
        if i == idx:
            return r
    return len(scores)


def _entropy_from_probs(probs: List[float]) -> float:
    # Natural log entropy
    eps = 1e-12
    s = 0.0
    for p in probs:
        p = max(eps, min(1.0 - eps, _safe_float(p, 0.0)))
        s += -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)
    return s / max(1, len(probs))


@dataclass
class GroupRankingMetrics:
    groups: int
    rows: int
    top1_accuracy: Optional[float]
    mrr: Optional[float]


def compute_group_ranking_metrics(
    runs: List[Dict[str, Any]],
    pred_key: str,
    chosen_index_key: str = "chosen_index",
    group_key: str = "run_id",
    candidates_path: Tuple[str, str] = ("optimization", "candidates"),
) -> GroupRankingMetrics:
    """
    Group-aware metrics:
      - top1_accuracy: mean over groups of [argmax(pred) == chosen_index]
      - mrr: mean over groups of 1/rank(chosen_index) where rank computed by pred scores

    If a group has missing chosen_index or missing pred scores, it is skipped.
    """
    # Flatten into (group_id, chosen_index, pred_scores list)
    usable_groups = 0
    hits = 0
    mrr_sum = 0.0
    rows = 0

    for run in runs:
        gid = run.get(group_key)
        opt = run.get(candidates_path[0], {}) if isinstance(run, dict) else {}
        candidates = opt.get(candidates_path[1], []) if isinstance(opt, dict) else []
        if not isinstance(candidates, list) or not candidates:
            continue

        chosen_index = opt.get(chosen_index_key, None)
        if chosen_index is None:
            continue
        try:
            chosen_index = int(chosen_index)
        except Exception:
            continue
        if chosen_index < 0 or chosen_index >= len(candidates):
            continue

        preds: List[float] = []
        ok_pred = True
        for c in candidates:
            if not isinstance(c, dict) or pred_key not in c or not _is_finite(c.get(pred_key)):
                ok_pred = False
                break
            preds.append(float(c[pred_key]))

        if not ok_pred:
            continue

        usable_groups += 1
        rows += len(preds)

        top1 = _argmax(preds)
        if top1 == chosen_index:
            hits += 1

        rank = _rank_of_index(preds, chosen_index, descending=True)
        mrr_sum += 1.0 / float(rank)

    if usable_groups == 0:
        return GroupRankingMetrics(groups=0, rows=0, top1_accuracy=None, mrr=None)

    return GroupRankingMetrics(
        groups=usable_groups,
        rows=rows,
        top1_accuracy=hits / float(usable_groups),
        mrr=mrr_sum / float(usable_groups),
    )


@dataclass
class ChooserDiagnostics:
    groups: int
    mean_entropy: Optional[float]
    mean_margin_top1_top2: Optional[float]
    flat_rate: Optional[float]


def compute_chooser_diagnostics(
    runs: List[Dict[str, Any]],
    prob_key: str = "p_choose",
    group_key: str = "run_id",
    candidates_path: Tuple[str, str] = ("optimization", "candidates"),
    eps_flat: float = 1e-12,
) -> ChooserDiagnostics:
    """
    Computes chooser diagnostics over groups:
      - mean_entropy: mean over runs of mean Bernoulli entropy across candidates
      - mean_margin_top1_top2: mean over runs of (top1_prob - top2_prob) with probs sorted desc
      - flat_rate: fraction of runs where max(prob)-min(prob) < eps_flat
    Skips runs with missing probs.
    """
    ent_sum = 0.0
    marg_sum = 0.0
    flat_hits = 0
    usable = 0

    for run in runs:
        opt = run.get(candidates_path[0], {}) if isinstance(run, dict) else {}
        candidates = opt.get(candidates_path[1], []) if isinstance(opt, dict) else []
        if not isinstance(candidates, list) or not candidates:
            continue

        probs: List[float] = []
        ok = True
        for c in candidates:
            if not isinstance(c, dict) or prob_key not in c or not _is_finite(c.get(prob_key)):
                ok = False
                break
            probs.append(float(c[prob_key]))

        if not ok:
            continue

        usable += 1
        pmin, pmax = min(probs), max(probs)
        if (pmax - pmin) < eps_flat:
            flat_hits += 1

        ent_sum += _entropy_from_probs(probs)

        probs_sorted = sorted(probs, reverse=True)
        if len(probs_sorted) >= 2:
            marg_sum += (probs_sorted[0] - probs_sorted[1])
        else:
            marg_sum += 0.0

    if usable == 0:
        return ChooserDiagnostics(groups=0, mean_entropy=None, mean_margin_top1_top2=None, flat_rate=None)

    return ChooserDiagnostics(
        groups=usable,
        mean_entropy=ent_sum / float(usable),
        mean_margin_top1_top2=marg_sum / float(usable),
        flat_rate=flat_hits / float(usable),
    )
