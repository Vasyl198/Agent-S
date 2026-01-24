from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent.fashion.ml.features import featurize_candidate
from agent.fashion.ml.models import SimpleDictVectorizer, SimpleLogisticRegression


@dataclass
class Row:
    group_id: str
    x: Dict[str, float]
    y: int
    cand_index: int


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def extract_rows(samples: List[Dict[str, Any]], neg_per_pos: int, seed: int) -> Tuple[List[Row], int]:
    rng = random.Random(seed)
    rows: List[Row] = []
    groups = 0

    for s in samples:
        opt = s.get("optimization") or {}
        candidates = opt.get("candidates") or []
        chosen_index = opt.get("chosen_index")
        run_id = s.get("run_id") or "unknown"
        if chosen_index is None or not isinstance(candidates, list) or not candidates:
            continue
        if not (0 <= int(chosen_index) < len(candidates)):
            continue

        groups += 1
        chosen_index = int(chosen_index)

        # positive row
        pos_c = candidates[chosen_index]
        x_pos = featurize_candidate(s, pos_c)
        rows.append(Row(group_id=run_id, x=x_pos, y=1, cand_index=chosen_index))

        # sample negatives
        neg_indices = [i for i in range(len(candidates)) if i != chosen_index]
        rng.shuffle(neg_indices)
        neg_indices = neg_indices[: max(1, neg_per_pos)]
        for i in neg_indices:
            x_neg = featurize_candidate(s, candidates[i])
            rows.append(Row(group_id=run_id, x=x_neg, y=0, cand_index=i))

    return rows, groups


def grouped_top1_accuracy(groups: Dict[str, List[Tuple[int, float]]], chosen: Dict[str, int]) -> float:
    # groups[run_id] = [(cand_index, prob), ...]
    if not groups:
        return 0.0
    correct = 0
    total = 0
    for gid, items in groups.items():
        if gid not in chosen:
            continue
        pred = max(items, key=lambda t: t[1])[0]
        if pred == chosen[gid]:
            correct += 1
        total += 1
    return correct / total if total else 0.0


def grouped_mrr(groups: Dict[str, List[Tuple[int, float]]], chosen: Dict[str, int]) -> float:
    if not groups:
        return 0.0
    rs = []
    for gid, items in groups.items():
        if gid not in chosen:
            continue
        items_sorted = sorted(items, key=lambda t: t[1], reverse=True)
        target = chosen[gid]
        rank = None
        for r, (idx, _) in enumerate(items_sorted, start=1):
            if idx == target:
                rank = r
                break
        rs.append(1.0 / rank if rank else 0.0)
    return sum(rs) / len(rs) if rs else 0.0


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agent.fashion.ml.train_chooser")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--neg-per-pos", type=int, default=4)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--l2", type=float, default=1e-4)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    dataset_path = Path(args.dataset)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    samples = read_jsonl(dataset_path)
    rows, groups_n = extract_rows(samples, neg_per_pos=args.neg_per_pos, seed=args.seed)

    X_dict = [r.x for r in rows]
    y = [r.y for r in rows]

    vec = SimpleDictVectorizer()
    X = vec.fit_transform(X_dict)

    # class weights for imbalance: weight positives higher
    pos = sum(y)
    neg = len(y) - pos
    pos_weight = (neg / pos) if pos > 0 else 1.0

    model = SimpleLogisticRegression(
        lr=float(args.lr),
        l2=float(args.l2),
        epochs=int(args.epochs),
        seed=int(args.seed),
        pos_weight=float(pos_weight),
        neg_weight=1.0,
    )
    model.fit(X, y)

    # Evaluate grouped metrics on training set (baseline)
    # Build prob per (run_id, cand_index). Note: we only trained on sampled negatives, but it's ok for sanity.
    probs = model.predict_proba(X)
    group_map: Dict[str, List[Tuple[int, float]]] = {}
    chosen_map: Dict[str, int] = {}
    for r, p in zip(rows, probs):
        group_map.setdefault(r.group_id, []).append((r.cand_index, float(p)))
        if r.y == 1:
            chosen_map[r.group_id] = r.cand_index

    top1 = grouped_top1_accuracy(group_map, chosen_map)
    mrr = grouped_mrr(group_map, chosen_map)

    pack = {
        "artifact": {"schema": "agent-fashion-chooser@1"},
        "vectorizer": vec,
        "model": model,
        "model_name": "logreg",
        "model_params": {
            "epochs": int(args.epochs),
            "lr": float(args.lr),
            "l2": float(args.l2),
            "neg_per_pos": int(args.neg_per_pos),
            "pos_weight": float(pos_weight),
        },
    }

    import pickle
    with out_path.open("wb") as f:
        pickle.dump(pack, f)

    print(json.dumps(
        {
            "ok": True,
            "rows": len(rows),
            "groups": groups_n,
            "pos": pos,
            "neg": neg,
            "top1_accuracy": top1,
            "mrr": mrr,
            "out": str(out_path),
        },
        ensure_ascii=False
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
