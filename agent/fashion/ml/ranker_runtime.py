from __future__ import annotations

import pickle
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Import custom classes needed for pickle
from .models import SimpleDictVectorizer, SimpleRidge, SimpleRandomForestRegressor, SimpleDecisionTreeRegressor


@dataclass
class LoadedRanker:
    """Загруженный ML ранкер для предсказаний"""
    vectorizer: Any
    model: Any
    model_name: str = "unknown"
    model_params: Dict[str, Any] | None = None

    def predict_scores(self, X_dict: List[Dict[str, float]]) -> List[float]:
        """Предсказать scores для списка кандидатов"""
        X = self.vectorizer.transform(X_dict)
        preds = self.model.predict(X)
        return [float(x) for x in preds]


def load_ranker(path: str) -> LoadedRanker:
    """Загрузить ранкер из файла"""
    with open(path, "rb") as f:
        pack = pickle.load(f)
    
    # Check artifact schema
    artifact = pack.get("artifact", {})
    schema = artifact.get("schema")
    if schema and schema != "agent-fashion-ranker@1":
        raise ValueError(f"Unsupported ranker schema: {schema}. Expected: agent-fashion-ranker@1")
    
    return LoadedRanker(
        vectorizer=pack["vectorizer"],
        model=pack["model"],
        model_name=pack.get("model_name", "unknown"),
        model_params=pack.get("model_params") or pack.get("params"),
    )
