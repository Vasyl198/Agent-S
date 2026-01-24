from pathlib import Path

def validate_dxf_structure(filepath: str, verbose: bool = True) -> dict:
    """
    Проверяет, что DXF:
    - существует
    - содержит SECTION ENTITIES
    - содержит геометрию (LINE / LWPOLYLINE / POLYLINE / SPLINE)
    """

    path = Path(filepath)
    result = {
        "exists": path.exists(),
        "has_entities_section": False,
        "geometry_count": 0,
        "geometry_types": set(),
        "is_valid": False,
        "errors": []
    }

    if not path.exists():
        result["errors"].append("File does not exist")
        return result

    text = path.read_text(errors="ignore")

    # Проверка ENTITIES
    if "SECTION" in text and "\n2\nENTITIES" in text:
        result["has_entities_section"] = True
    else:
        result["errors"].append("No ENTITIES section")

    # Поиск геометрии
    geometry_tokens = ["\n0\nLINE", "\n0\nLWPOLYLINE", "\n0\nPOLYLINE", "\n0\nSPLINE"]

    for token in geometry_tokens:
        count = text.count(token)
        if count > 0:
            result["geometry_count"] += count
            result["geometry_types"].add(token.strip())

    if result["geometry_count"] == 0:
        result["errors"].append("No geometry entities found")

    result["is_valid"] = (
        result["exists"]
        and result["has_entities_section"]
        and result["geometry_count"] > 0
    )

    if verbose:
        print("\n🧪 DXF STRUCTURE VALIDATION")
        print("=" * 40)
        print(f"📄 File: {filepath}")
        print(f"Exists: {result['exists']}")
        print(f"ENTITIES section: {result['has_entities_section']}")
        print(f"Geometry count: {result['geometry_count']}")
        print(f"Geometry types: {list(result['geometry_types'])}")
        print(f"VALID DXF: {result['is_valid']}")
        if result["errors"]:
            print("❌ Errors:")
            for e in result["errors"]:
                print("  -", e)

    return result
