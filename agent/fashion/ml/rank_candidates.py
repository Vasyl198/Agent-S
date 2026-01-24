from __future__ import annotations

from typing import Any, Dict, List

from agent.fashion.ml.features import featurize_candidate
from agent.fashion.ml.ranker_runtime import LoadedRanker


def rank_candidates(
    ranker: LoadedRanker,
    sample: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Ранжировать кандидатов с помощью ML ранкера
    
    Args:
        ranker: загруженный ML ранкер
        sample: sample с target
        candidates: список кандидатов
        
    Returns:
        список кандидатов с добавленными pred_score и rank_position
    """
    X_dict = [featurize_candidate(sample, c) for c in candidates]
    preds = ranker.predict_scores(X_dict)

    out = []
    for cand, pred in zip(candidates, preds):
        # Сохраняем все существующие поля кандидата и добавляем pred_score
        if isinstance(cand, dict):
            c2 = cand.copy()  # копируем все существующие поля
            c2["pred_score"] = float(pred)
        else:
            # Если cand не словарь, создаем новый
            c2 = {
                "proposal": cand,
                "pred_score": float(pred)
            }
        out.append(c2)

    # Сортируем по pred_score (убыванию)
    out.sort(key=lambda c: c.get("pred_score", 0.0), reverse=True)

    # Добавляем rank_position
    for i, c in enumerate(out):
        c["rank_position"] = i

    return out
