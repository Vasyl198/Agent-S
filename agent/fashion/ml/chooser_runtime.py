from __future__ import annotations

import math
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from agent.fashion.ml.features import featurize_candidate


def _sigmoid(z: float) -> float:
    # stable sigmoid
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)

def _clip_prob(p: float, eps: float = 1e-6) -> float:
    """Clip probability to avoid exact 0/1"""
    return max(eps, min(1 - eps, p))

def _clamp(z: float, lo: float = -20.0, hi: float = 20.0) -> float:
    """Clamp value to range [lo, hi]"""
    return lo if z < lo else hi if z > hi else z

@dataclass
class ChooserRuntime:
    model_name: str
    vectorizer: Any
    model: Any
    model_path: str
    temperature: float = 1.0

    def predict_logits_and_probs(self, sample: Dict[str, Any], candidates: List[Dict[str, Any]]):
        X_dict = [featurize_candidate(sample, c) for c in candidates]
        X = self.vectorizer.transform(X_dict)

        # logits from model
        if hasattr(self.model, "predict_logits"):
            logits = [float(z) for z in self.model.predict_logits(X)]
        else:
            # fallback: derive from proba (not perfect)
            probs0 = [float(p) for p in self.model.predict_proba(X)]
            logits = [math.log(p / (1.0 - p)) for p in probs0]

        T = float(self.temperature) if self.temperature else 1.0
        logits_T = [_clamp(z / T) for z in logits]

        probs = [_clip_prob(_sigmoid(z)) for z in logits_T]
        return logits_T, probs

    def predict_probs(self, sample: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[float]:
        # Backward compatibility - just return probs
        _, probs = self.predict_logits_and_probs(sample, candidates)
        return probs


def load_chooser(path: str) -> ChooserRuntime:
    p = Path(path)
    with p.open("rb") as f:
        pack = pickle.load(f)

    art = pack.get("artifact") or {}
    if art.get("schema") != "agent-fashion-chooser@1":
        raise ValueError(f"Bad chooser artifact schema: {art.get('schema')}")

    return ChooserRuntime(
        model_name=str(pack.get("model_name") or "logreg"),
        vectorizer=pack["vectorizer"],
        model=pack["model"],
        model_path=str(p),
    )
