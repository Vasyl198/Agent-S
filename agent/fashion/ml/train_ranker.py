from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Import ML model classes from models.py
from .models import (
    SimpleDictVectorizer,
    SimpleRidge,
    SimpleRandomForestRegressor,
    SimpleDecisionTreeRegressor,
)


def mean_squared_error(y_true, y_pred):
    import numpy as np
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return float(np.mean((y_true - y_pred) ** 2))


def train_test_split(X, y, test_size=0.2, random_state=0):
    import numpy as np
    X = np.array(X)
    y = np.array(y)
    n = len(X)
    
    if random_state is not None:
        np.random.seed(random_state)
    
    indices = np.random.permutation(n)
    split_idx = int(n * (1 - test_size))
    
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def compute_top1_accuracy_grouped(X_dict, y_is_chosen, groups, vec, model) -> float:
    """
    Вычислить top1 accuracy по группам (run_id)
    """
    import numpy as np
    X = vec.transform(X_dict)
    preds = model.predict(X)

    # group -> list of row indices
    buckets = {}
    for i, g in enumerate(groups):
        buckets.setdefault(g, []).append(i)

    correct = 0
    total = 0
    for g, idxs in buckets.items():
        # если в группе вообще нет chosen — пропускаем (или считаем как 0)
        chosen_positions = [i for i in idxs if y_is_chosen[i] == 1]
        if not chosen_positions:
            continue

        pred_best = idxs[int(np.argmax([preds[i] for i in idxs]))]
        true_best = chosen_positions[0]  # там должен быть ровно один
        correct += 1 if pred_best == true_best else 0
        total += 1

    return float(correct / total) if total else 0.0


from agent.fashion.ml.features import extract_rows_from_sample, vectorize


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    samples: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="Path to runs.jsonl")
    ap.add_argument("--out", default="output/ml/ranker.joblib", help="Output model path")
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--model", default="ridge", choices=["ridge", "rf"], help="Model type")
    ap.add_argument("--rf-trees", type=int, default=80, help="RandomForest: number of trees")
    ap.add_argument("--rf-depth", type=int, default=5, help="RandomForest: max depth")
    ap.add_argument("--rf-sample-ratio", type=float, default=0.8, help="RandomForest: bootstrap sample ratio")
    args = ap.parse_args()

    samples = read_jsonl(args.dataset)

    rows = []
    for s in samples:
        rows.extend(extract_rows_from_sample(s))

    if not rows:
        raise SystemExit("No rows extracted from dataset (need optimization.candidates).")

    X_dict, y_score, y_is_chosen, groups = vectorize(rows)

    vec = SimpleDictVectorizer()
    X = vec.fit_transform(X_dict)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_score, test_size=args.test_size, random_state=args.seed
    )

    # Выбор модели
    if args.model == "ridge":
        model = SimpleRidge(alpha=1.0)
        model_params = {"alpha": 1.0}
    elif args.model == "rf":
        model = SimpleRandomForestRegressor(
            n_estimators=args.rf_trees,
            max_depth=args.rf_depth,
            sample_ratio=args.rf_sample_ratio,
            random_state=args.seed,
        )
        model_params = {
            "n_estimators": args.rf_trees,
            "max_depth": args.rf_depth,
            "sample_ratio": args.rf_sample_ratio,
            "random_state": args.seed
        }
    else:
        raise ValueError(f"Unknown model: {args.model}")

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    
    # 7.0.2: считаем group-aware top1 accuracy
    top1_acc = compute_top1_accuracy_grouped(X_dict, y_is_chosen, groups, vec, model)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "wb") as f:
        import pickle
        pickle.dump({
            "vectorizer": vec, 
            "model": model, 
            "rmse": rmse,
            "model_name": args.model,
            "model_params": model_params,
            "artifact": {
                "schema": "agent-fashion-ranker@1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "code_ref": "agent.fashion.ml.models",
            }
        }, f)

    print(json.dumps({
        "ok": True, 
        "rmse": rmse, 
        "top1_accuracy": top1_acc, 
        "rows": len(rows), 
        "out": args.out,
        "model": args.model,
        "model_params": model_params
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
