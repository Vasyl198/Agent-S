from __future__ import annotations

import argparse
import json
import pickle
from typing import Any, Dict, List

from agent.fashion.ml.features import featurize_candidate
from agent.fashion.ml.train_ranker import SimpleDictVectorizer, SimpleRidge, SimpleRandomForestRegressor, SimpleDecisionTreeRegressor


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="Path to ranker.joblib")
    ap.add_argument("--sample", required=True, help="Path to dataset sample JSON (single object) OR '-' for stdin")
    args = ap.parse_args()

    with open(args.model, "rb") as f:
        pack = pickle.load(f)
    vec = pack["vectorizer"]
    model = pack["model"]

    if args.sample == "-":
        sample = json.loads(input())
    else:
        with open(args.sample, "r", encoding="utf-8") as f:
            sample = json.load(f)

    candidates = (sample.get("optimization") or {}).get("candidates") or []
    scored: List[Dict[str, Any]] = []
    for cand in candidates:
        x = featurize_candidate(sample, cand)
        X = vec.transform([x])
        pred = float(model.predict(X)[0])
        scored.append({"pred_score": pred, "candidate": cand})

    scored.sort(key=lambda d: d["pred_score"], reverse=True)
    print(json.dumps({"predictions": scored}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
