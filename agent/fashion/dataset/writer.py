# agent/fashion/dataset/writer.py
from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_makedirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_env_block() -> Dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
    }


def try_read_git_commit() -> Optional[str]:
    # Без зависимости от git: пробуем env/файл, иначе None
    commit = os.environ.get("GIT_COMMIT") or os.environ.get("CI_COMMIT_SHA")
    if commit:
        return commit[:12]
    return None


@dataclass(frozen=True)
class DatasetWriteConfig:
    dataset_dir: str
    fmt: str = "jsonl"  # "jsonl" or "json"
    write_mode: str = "append"  # "append" or "overwrite"


def write_dataset_sample(sample: Dict[str, Any], cfg: DatasetWriteConfig) -> str:
    safe_makedirs(cfg.dataset_dir)

    if cfg.fmt == "jsonl":
        path = os.path.join(cfg.dataset_dir, "runs.jsonl")
        mode = "a" if cfg.write_mode == "append" else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False))
            f.write("\n")
        return path

    if cfg.fmt == "json":
        run_id = sample.get("run_id") or "run"
        path = os.path.join(cfg.dataset_dir, f"{run_id}.json")
        mode = "w"
        with open(path, mode, encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2, sort_keys=True)
        return path

    raise ValueError(f"Unsupported dataset format: {cfg.fmt!r}")
