from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _bbox(points: List[List[float]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _dist(a: List[float], b: List[float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def _edge_lengths_from_edges(vertices: List[List[float]], edges: List[Dict[str, Any]]) -> List[float]:
    out: List[float] = []
    n = len(vertices)
    for e in edges:
        endpoints = e.get("endpoints")
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            continue
        i, j = endpoints
        if not isinstance(i, int) or not isinstance(j, int):
            continue
        if i < 0 or j < 0 or i >= n or j >= n:
            continue
        out.append(_dist(vertices[i], vertices[j]))
    return out


def _edge_lengths_fallback_loop(vertices: List[List[float]]) -> List[float]:
    # If edges are missing: connect consecutive vertices in order, close the loop
    out: List[float] = []
    n = len(vertices)
    if n < 2:
        return out
    for i in range(n):
        j = (i + 1) % n
        out.append(_dist(vertices[i], vertices[j]))
    return out


def _stats(vals: List[float]) -> Dict[str, float]:
    if not vals:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "sum": 0.0}
    s = sum(vals)
    mn = min(vals)
    mx = max(vals)
    mean = s / len(vals)
    return {"min": mn, "max": mx, "mean": mean, "sum": s}


def extract_pattern_features(sample: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract lightweight geometry + complexity features from:
      sample["input"]["pattern_spec"]  (schema@2)
    Expected structure (as in skirt_2_panels_1200 specification.json):
      pattern_spec.pattern.panels.{front,back}.vertices : [[x,y],...]
      pattern_spec.pattern.panels.*.edges[*].endpoints : [i,j]
      pattern_spec.pattern.stitches : list of edge-pairs
    """
    out: Dict[str, float] = {}

    inp = sample.get("input") or {}
    spec = inp.get("pattern_spec") or {}
    pattern = spec.get("pattern") or {}
    panels = pattern.get("panels") or {}
    stitches = pattern.get("stitches") or []

    # global counts
    out["n_panels"] = float(len(panels)) if isinstance(panels, dict) else 0.0
    out["stitches_count"] = float(len(stitches)) if isinstance(stitches, list) else 0.0

    # stitches panel coverage
    stitch_panels = set()
    if isinstance(stitches, list):
        for s in stitches:
            if isinstance(s, list) and len(s) == 2:
                for side in s:
                    if isinstance(side, dict) and isinstance(side.get("panel"), str):
                        stitch_panels.add(side["panel"])
    out["stitches_unique_panels"] = float(len(stitch_panels))

    # per-panel features for known panel names (front/back) + also aggregate
    panel_names = []
    if isinstance(panels, dict):
        panel_names = list(panels.keys())

    # aggregate accumulators
    total_vertices = 0
    total_edges = 0
    total_curved_edges = 0
    total_edge_len_sum = 0.0

    for name in panel_names:
        p = panels.get(name) or {}
        vertices = p.get("vertices") or []
        edges = p.get("edges") or []

        if not isinstance(vertices, list):
            vertices = []
        if not isinstance(edges, list):
            edges = []

        # basic
        n_v = len(vertices)
        n_e = len(edges)
        out[f"panel.{name}.n_vertices"] = float(n_v)
        out[f"panel.{name}.n_edges"] = float(n_e)

        total_vertices += n_v
        total_edges += n_e

        # bbox
        pts = [v for v in vertices if isinstance(v, list) and len(v) >= 2]
        if pts:
            x0, y0, x1, y1 = _bbox(pts)
            w = x1 - x0
            h = y1 - y0
            out[f"panel.{name}.bbox_w"] = _safe_float(w)
            out[f"panel.{name}.bbox_h"] = _safe_float(h)
            out[f"panel.{name}.bbox_area"] = _safe_float(w * h)
        else:
            out[f"panel.{name}.bbox_w"] = 0.0
            out[f"panel.{name}.bbox_h"] = 0.0
            out[f"panel.{name}.bbox_area"] = 0.0

        # curvature complexity
        curved = 0
        for e in edges:
            if isinstance(e, dict) and "curvature" in e:
                curved += 1
        out[f"panel.{name}.curved_edges"] = float(curved)
        total_curved_edges += curved

        # edge lengths
        lens = []
        pts2 = [v for v in vertices if isinstance(v, list) and len(v) >= 2]
        if pts2:
            lens = _edge_lengths_from_edges(pts2, edges)
            if not lens:
                lens = _edge_lengths_fallback_loop(pts2)

        st = _stats(lens)
        out[f"panel.{name}.edge_len_sum"] = st["sum"]
        out[f"panel.{name}.edge_len_mean"] = st["mean"]
        out[f"panel.{name}.edge_len_min"] = st["min"]
        out[f"panel.{name}.edge_len_max"] = st["max"]

        total_edge_len_sum += st["sum"]

    out["total_vertices"] = float(total_vertices)
    out["total_edges"] = float(total_edges)
    out["total_curved_edges"] = float(total_curved_edges)
    out["total_edge_len_sum"] = float(total_edge_len_sum)

    # parameters (optional)
    params = spec.get("parameters") or {}
    if isinstance(params, dict):
        out["n_parameters"] = float(len(params))
        # a few numeric summaries if available
        numeric_vals = []
        for v in params.values():
            try:
                numeric_vals.append(float(v))
            except Exception:
                pass
        out["parameters_numeric_count"] = float(len(numeric_vals))
        out["parameters_numeric_sum"] = float(sum(numeric_vals)) if numeric_vals else 0.0
    else:
        out["n_parameters"] = 0.0
        out["parameters_numeric_count"] = 0.0
        out["parameters_numeric_sum"] = 0.0

    return out
