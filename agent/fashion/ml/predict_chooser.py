from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

from agent.fashion.ml.features import featurize_candidate


def load_chooser(path: Path) -> Dict[str, Any]:
    with path.open("rb") as f:
        pack = pickle.load(f)
    art = pack.get("artifact") or {}
    if art.get("schema") != "agent-fashion-chooser@1":
        raise ValueError(f"Bad chooser artifact schema: {art.get('schema')}")
    return pack


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agent.fashion.ml.predict_chooser")
    ap.add_argument("--model", required=True)
    ap.add_argument("--sample", required=True, help="Path to JSON sample (single run)")
    args = ap.parse_args(argv)

    pack = load_chooser(Path(args.model))
    vec = pack["vectorizer"]
    model = pack["model"]

    sample = json.load(open(args.sample, "r", encoding="utf-8"))
    candidates = (sample.get("optimization") or {}).get("candidates") or []

    X_dict = [featurize_candidate(sample, c) for c in candidates]
    X = vec.transform(X_dict)
    probs = model.predict_proba(X)

    ranked = []
    for i, (c, p) in enumerate(zip(candidates, probs)):
        ranked.append({"index": i, "p_choose": float(p), "candidate": c})

    ranked.sort(key=lambda r: r["p_choose"], reverse=True)
    pred_idx = ranked[0]["index"] if ranked else None

    print(json.dumps({"pred_chosen_index": pred_idx, "ranked": ranked}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
