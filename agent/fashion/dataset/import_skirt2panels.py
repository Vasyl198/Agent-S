from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -------------------------
# Helpers
# -------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def safe_read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def find_samples(src: Path) -> List[str]:
    """
    Returns list of sample prefixes like 'skirt_2_panels_0AG3RA5IMQ'.
    We infer by scanning for 'specification.json' occurrences under each sample folder
    OR by scanning files and extracting prefix up to last underscore group.
    """
    prefixes = set()

    # Common case: each sample is a directory named skirt_2_panels_<ID>
    for p in src.iterdir():
        if p.is_dir() and p.name.startswith("skirt_2_panels_"):
            prefixes.add(p.name)

    # Fallback: flat layout
    if not prefixes:
        for f in src.glob("*.json"):
            # e.g. skirt_2_panels_XXXX_specification.json
            name = f.name
            if name.startswith("skirt_2_panels_") and "specification" in name:
                prefix = name.split("_specification")[0]
                prefixes.add(prefix)

    return sorted(prefixes)

def resolve_assets(sample_dir_or_root: Path, prefix: str) -> Dict[str, Optional[str]]:
    """
    Supports either:
    - src/<prefix>/specification.json + other files
    - src/<prefix>_specification.json etc in flat folder
    """
    assets = {
        "specification_json": None,
        "pattern_png": None,
        "pattern_svg": None,
        "camera_front_png": None,
        "camera_back_png": None,
        "sim_obj": None,
        "sim_segmentation": None,
        "scan_imitation_obj": None,
        "scan_imitation_segmentation": None,
    }

    # layout A: directory per sample
    dir_candidate = sample_dir_or_root / prefix
    if dir_candidate.is_dir():
        base = dir_candidate
        assets["specification_json"] = str((base / "specification.json").resolve()) if (base / "specification.json").exists() else None
        # files usually: <prefix>_pattern.png etc OR just pattern.png — handle both
        for key, suffixes in {
            "pattern_png": ["pattern.png", f"{prefix}_pattern.png"],
            "pattern_svg": ["pattern.svg", f"{prefix}_pattern.svg"],
            "camera_front_png": ["camera_front.png", f"{prefix}_camera_front.png"],
            "camera_back_png": ["camera_back.png", f"{prefix}_camera_back.png"],
            "sim_obj": ["sim.obj", f"{prefix}_sim.obj"],
            "sim_segmentation": ["sim_segmentation.txt", f"{prefix}_sim_segmentation.txt"],
            "scan_imitation_obj": ["scan_imitation.obj", f"{prefix}_scan_imitation.obj"],
            "scan_imitation_segmentation": ["scan_imitation_segmentation.txt", f"{prefix}_scan_imitation_segmentation.txt"],
        }.items():
            for s in suffixes:
                p = base / s
                if p.exists():
                    assets[key] = str(p.resolve())
                    break
        return assets

    # layout B: flat files in root
    base = sample_dir_or_root
    spec = base / f"{prefix}_specification.json"
    assets["specification_json"] = str(spec.resolve()) if spec.exists() else None
    for key, filename in {
        "pattern_png": f"{prefix}_pattern.png",
        "pattern_svg": f"{prefix}_pattern.svg",
        "camera_front_png": f"{prefix}_camera_front.png",
        "camera_back_png": f"{prefix}_camera_back.png",
        "sim_obj": f"{prefix}_sim.obj",
        "sim_segmentation": f"{prefix}_sim_segmentation.txt",
        "scan_imitation_obj": f"{prefix}_scan_imitation.obj",
        "scan_imitation_segmentation": f"{prefix}_scan_imitation_segmentation.txt",
    }.items():
        p = base / filename
        assets[key] = str(p.resolve()) if p.exists() else None

    return assets


# -------------------------
# Dataset sample schema@2
# -------------------------

@dataclass
class ImportConfig:
    src: Path
    out: Path
    limit: int = 0
    seed: int = 0
    candidate_count: int = 5
    write_mode: str = "append"  # append|overwrite


def build_target(rng: random.Random) -> Dict[str, Any]:
    goal = rng.choice(["reduce_seam_allowance", "increase_seam_allowance"])
    role = rng.choice(["HEM", "WAIST", "SIDE"])
    by = float(rng.randint(1, 5))
    return {"goal": goal, "role": role, "by": by, "mode": "delta", "constraints": {}}

def build_candidates(rng: random.Random, target: Dict[str, Any], n: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Make candidates with one guaranteed "near-best" candidate at chosen_index.
    """
    goal_t = target["goal"]
    role_t = target["role"]
    by_t = float(target["by"])

    candidates: List[Dict[str, Any]] = []

    # Perfect/near-perfect candidate
    best = {
        "proposal": {"type": "target", "goal": goal_t, "role": role_t, "by": by_t},
        "constraint_ok": True,
    }
    candidates.append(best)

    # Other candidates
    for _ in range(max(0, n - 1)):
        g = rng.choice([goal_t, "reduce_seam_allowance", "increase_seam_allowance"])
        r = rng.choice([role_t, "HEM", "WAIST", "SIDE"])
        b = float(max(1, min(5, int(by_t + rng.choice([-2, -1, 0, 1, 2])))))
        candidates.append({
            "proposal": {"type": "target", "goal": g, "role": r, "by": b},
            "constraint_ok": True,
        })

    # shuffle, remember chosen_index
    rng.shuffle(candidates)
    chosen_index = next(i for i, c in enumerate(candidates) if c["proposal"]["goal"] == goal_t and c["proposal"]["role"] == role_t and float(c["proposal"]["by"]) == by_t)
    return candidates, chosen_index

def proxy_score(target: Dict[str, Any], proposal: Dict[str, Any]) -> Tuple[float, float]:
    same_goal = 1.0 if proposal.get("goal") == target.get("goal") else 0.0
    same_role = 1.0 if proposal.get("role") == target.get("role") else 0.0
    by_t = float(target.get("by", 0.0))
    by_p = float(proposal.get("by", 0.0))
    by_diff = abs(by_p - by_t)

    score = 0.5 + 0.2 * same_role + 0.1 * same_goal - 0.02 * by_diff
    score = max(0.0, min(1.0, score))
    improvement = score - 0.5
    return score, improvement

def write_jsonl(path: Path, row: Dict[str, Any], mode: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "overwrite":
        with path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def make_sample(prefix: str, assets: Dict[str, Optional[str]], target: Dict[str, Any], candidates: List[Dict[str, Any]], chosen_index: int) -> Dict[str, Any]:
    spec_block: Optional[Dict[str, Any]] = None
    if assets.get("specification_json"):
        spec = safe_read_json(Path(assets["specification_json"]))
        # keep only what we need (panels, stitches, parameters)
        spec_block = {
            "pattern": spec.get("pattern", {}),
            "parameters": spec.get("parameters", {}),
            "properties": spec.get("properties", {}),
        }

    # fill scores
    scored_candidates: List[Dict[str, Any]] = []
    for c in candidates:
        proposal = c["proposal"]
        score, improvement = proxy_score(target, proposal)
        scored_candidates.append({
            **c,
            "score": score,
            "improvement": improvement,
        })

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{prefix}_seed0"

    return {
        "schema": "agent-fashion-dataset@2",
        "ts_utc": utc_now_iso(),
        "run_id": run_id,
        "input": {
            "pattern_dataset": {"name": "skirt-2-panels-1200", "sample_id": prefix},
            "assets": assets,
            "pattern_spec": spec_block,
            "target": target,
        },
        "optimization": {
            "candidates": scored_candidates,
            "chosen_index": chosen_index,
        },
        "exit": {"code": 0, "reason": "ok", "detail": None},
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="agent.fashion.dataset.import_skirt2panels")
    ap.add_argument("--src", required=True, help="Path to skirt_2_panels_1200 root directory")
    ap.add_argument("--out", default="output/dataset_skirt/runs.jsonl", help="Output JSONL path")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of samples (0=all)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--candidate-count", type=int, default=5)
    ap.add_argument("--write-mode", choices=["append", "overwrite"], default="append")
    args = ap.parse_args(argv)

    cfg = ImportConfig(
        src=Path(args.src),
        out=Path(args.out),
        limit=int(args.limit),
        seed=int(args.seed),
        candidate_count=int(args.candidate_count),
        write_mode=str(args.write_mode),
    )

    rng = random.Random(cfg.seed)

    prefixes = find_samples(cfg.src)
    if cfg.limit and cfg.limit > 0:
        prefixes = prefixes[: cfg.limit]

    if not prefixes:
        raise SystemExit(f"No skirt samples found in: {cfg.src}")

    # overwrite once at start if requested
    if cfg.write_mode == "overwrite" and cfg.out.exists():
        cfg.out.unlink(missing_ok=True)

    for prefix in prefixes:
        assets = resolve_assets(cfg.src, prefix)
        # require specification.json to be present (strongest signal)
        if not assets.get("specification_json"):
            # skip silently (dataset may have missing samples)
            continue

        target = build_target(rng)
        candidates, chosen_index = build_candidates(rng, target, cfg.candidate_count)
        sample = make_sample(prefix, assets, target, candidates, chosen_index)
        write_jsonl(cfg.out, sample, mode="append")

    print(json.dumps({"ok": True, "out": str(cfg.out), "rows_appended": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
