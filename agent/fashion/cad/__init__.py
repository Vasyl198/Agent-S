"""
agent.fashion.cad
=================

Public CAD API.

Design goals:
- Importing this package must be side-effect free (no prints).
- Keep imports lightweight: use lazy exports so CLI/core tests don't pay full CAD cost.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple


# Map public names -> (module, attribute)
_EXPORTS: Dict[str, Tuple[str, str]] = {
    "Point": ("agent.fashion.cad.core.geometry", "Point"),
    "Segment": ("agent.fashion.cad.core.geometry", "Segment"),
    "Arc": ("agent.fashion.cad.core.geometry", "Arc"),
    "Contour": ("agent.fashion.cad.core.geometry", "Contour"),
    "ContourBuilder": ("agent.fashion.cad.core.contour", "ContourBuilder"),
    "GeometryValidator": ("agent.fashion.cad.core.validation", "GeometryValidator"),
    "CurveProcessor": ("agent.fashion.cad.core.curves", "CurveProcessor"),
}


def __getattr__(name: str) -> Any:
    """
    Lazy attribute resolver for `from agent.fashion.cad import Point` etc.
    """
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod_name, attr_name = _EXPORTS[name]
    mod = import_module(mod_name)
    value = getattr(mod, attr_name)
    # Cache resolved attribute to make next access fast/deterministic.
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_EXPORTS.keys()))


__all__ = [
    "Point",
    "Segment", 
    "Arc",
    "Contour",
    "ContourBuilder",
    "GeometryValidator",
    "CurveProcessor",
]
