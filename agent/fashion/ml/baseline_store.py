# agent/fashion/ml/baseline_store.py
"""Baseline snapshot manager for storing and loading CI summary baselines"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List


def sanitize_baseline_name(name: str) -> str:
    """Sanitize baseline name to be safe for filename"""
    # Remove/replace unsafe characters
    safe_name = re.sub(r'[^\w\-_.]', '_', name)
    # Ensure it doesn't start with dot or dash
    safe_name = safe_name.lstrip('._-')
    # Limit length
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    return safe_name or "default"


def make_scope_key(scope: str, pipeline: str | None = None, scope_params: dict | None = None) -> str:
    """Create scope key for baseline filename
    
    Args:
        scope: Scope type (all, by_pipeline, trend_day, window)
        pipeline: Pipeline name when scope is by_pipeline
        scope_params: Additional parameters for scope (e.g., {"last_n": 50, "day": "2026-01-23"})
        
    Returns:
        Scope key string
    """
    if scope == "all":
        return "all"
    elif scope == "by_pipeline" and pipeline:
        return f"by_pipeline__{pipeline}"
    elif scope == "trend_day":
        day = scope_params.get("day") if scope_params else None
        if day:
            return f"trend_day__{day}"
        else:
            return "trend_day"
    elif scope == "window":
        last_n = scope_params.get("last_n") if scope_params else None
        if last_n:
            return f"window__last_n_{last_n}"
        else:
            return "window__all"
    else:
        return "all"  # fallback


def resolve_baseline_path(store_dir: str, name: str, scope: str = "all", pipeline: str | None = None, scope_params: dict | None = None) -> str:
    """Resolve baseline file path from store directory, name, scope, and parameters
    
    Args:
        store_dir: Directory where baseline files are stored
        name: Baseline name (will be sanitized)
        scope: Scope type (all, by_pipeline, trend_day, window)
        pipeline: Pipeline name when scope is by_pipeline
        scope_params: Additional parameters for scope
        
    Returns:
        Full path to baseline file
    """
    safe_name = sanitize_baseline_name(name)
    scope_key = make_scope_key(scope, pipeline, scope_params)
    safe_scope_key = sanitize_baseline_name(scope_key)
    
    if scope_key == "all":
        filename = f"baseline_{safe_name}.json"
    else:
        filename = f"baseline_{safe_name}__{safe_scope_key}.json"
    
    return os.path.join(store_dir, filename)


def save_baseline(ci_summary: Dict[str, Any], path: str) -> None:
    """Save CI summary as baseline
    
    Args:
        ci_summary: CI summary dictionary
        path: Path where to save baseline file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Save as JSON without BOM (like publish_index)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ci_summary, f, indent=2, ensure_ascii=False)


def load_baseline(path: str) -> Dict[str, Any]:
    """Load baseline from file
    
    Args:
        path: Path to baseline file
        
    Returns:
        Baseline dictionary
        
    Raises:
        FileNotFoundError: If baseline file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path, "r", encoding="utf-8-sig") as f:  # Handle UTF-8 BOM
        return json.load(f)


def list_baselines(store_dir: str) -> List[str]:
    """List all available baselines in store directory
    
    Args:
        store_dir: Directory where baseline files are stored
        
    Returns:
        List of baseline names (without baseline_ prefix and .json extension)
    """
    if not os.path.exists(store_dir):
        return []
    
    baselines = []
    for filename in os.listdir(store_dir):
        if filename.startswith("baseline_") and filename.endswith(".json"):
            # Extract name: baseline_main.json -> main
            name = filename[9:-5]  # Remove "baseline_" prefix and ".json" extension
            baselines.append(name)
    
    return sorted(baselines)


def baseline_exists(store_dir: str, name: str) -> bool:
    """Check if baseline exists in store
    
    Args:
        store_dir: Directory where baseline files are stored
        name: Baseline name
        
    Returns:
        True if baseline exists, False otherwise
    """
    path = resolve_baseline_path(store_dir, name)
    return os.path.exists(path)


def delete_baseline(store_dir: str, name: str) -> bool:
    """Delete baseline from store
    
    Args:
        store_dir: Directory where baseline files are stored
        name: Baseline name
        
    Returns:
        True if deleted, False if didn't exist
    """
    path = resolve_baseline_path(store_dir, name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
