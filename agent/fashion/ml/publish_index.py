# agent/fashion/ml/publish_index.py
"""Publish index generation for GitHub Pages navigation"""

import os
from datetime import datetime
from typing import Dict, Any, Optional


def build_publish_index(out_dir: str, report: Dict[str, Any], ci_summary: Optional[Dict[str, Any]] = None, badges: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build publish index for GitHub Pages
    
    Args:
        out_dir: Output directory path
        report: Main report JSON
        ci_summary: CI summary if available
        badges: CI badges if available
        
    Returns:
        Index dictionary with file metadata and status
    """
    # Normalize out_dir
    out_dir = os.path.normpath(out_dir)
    
    # Check file existence
    files = {}
    
    # Report JSON (main report)
    report_json_path = os.path.join(out_dir, "report.json")
    files["report_json"] = {
        "path": "report.json",
        "exists": os.path.exists(report_json_path)
    }
    
    # CI Summary
    ci_summary_path = os.path.join(out_dir, "ci_summary.json")
    files["ci_summary"] = {
        "path": "ci_summary.json",
        "exists": os.path.exists(ci_summary_path)
    }
    
    # CI Badges
    ci_badges_path = os.path.join(out_dir, "ci_badges.json")
    files["ci_badges"] = {
        "path": "ci_badges.json",
        "exists": os.path.exists(ci_badges_path)
    }
    
    # Badges directory
    badges_dir = os.path.join(out_dir, "badges")
    badges_info = {"path": "badges/", "exists": os.path.exists(badges_dir)}
    if badges_info["exists"]:
        badges_info["items"] = {}
        for filename in os.listdir(badges_dir):
            if filename.endswith(".json"):
                badges_info["items"][filename] = {
                    "path": f"badges/{filename}",
                    "exists": True
                }
    files["badges_dir"] = badges_info
    
    # Report MD
    report_md_path = os.path.join(out_dir, "report.md")
    files["report_md"] = {
        "path": "report.md",
        "exists": os.path.exists(report_md_path)
    }
    
    # Report HTML
    report_html_path = os.path.join(out_dir, "report.html")
    files["report_html"] = {
        "path": "report.html",
        "exists": os.path.exists(report_html_path)
    }
    
    # Status information
    status = {
        "ok": ci_summary.get("ok", report.get("ok", True)) if ci_summary else report.get("ok", True),
        "exit_code": ci_summary.get("exit_code", 0) if ci_summary else 0,
        "runs_used": report.get("window", {}).get("used_runs", 0)
    }
    
    # Add CI status if available
    if ci_summary:
        status["ci_ok"] = ci_summary.get("ok", True)
        status["ci_fails"] = ci_summary.get("gates", {}).get("fails", 0)
        status["ci_warns"] = ci_summary.get("gates", {}).get("warns", 0)
    
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "out_dir": out_dir,
        "files": files,
        "status": status
    }


def render_index_html(index: Dict[str, Any], title: str = "ML Report Index", base_url: Optional[str] = None) -> str:
    """Render HTML index page
    
    Args:
        index: Index dictionary from build_publish_index
        title: Page title
        base_url: Optional base URL for absolute links
        
    Returns:
        HTML content string
    """
    def make_url(path: str) -> str:
        if base_url:
            return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        return path
    
    status = index["status"]
    files = index["files"]
    
    # Status emoji and color
    status_emoji = "✅" if status.get("ok", True) else "❌"
    status_text = "OK" if status.get("ok", True) else "FAIL"
    
    lines = []
    lines.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        .status {{
            font-size: 1.2em;
            font-weight: bold;
            margin: 20px 0;
        }}
        .status.ok {{ color: #28a745; }}
        .status.fail {{ color: #dc3545; }}
        .metrics {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-list li {{
            margin: 8px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 3px;
        }}
        .file-list a {{
            text-decoration: none;
            color: #007bff;
        }}
        .file-list a:hover {{
            text-decoration: underline;
        }}
        .exists {{ color: #28a745; }}
        .missing {{ color: #dc3545; }}
        .badges-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }}
        .badge-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="status {'ok' if status.get('ok', True) else 'fail'}">
        {status_emoji} Overall Status: {status_text}
    </div>
    
    <div class="metrics">
        <h3>📊 Key Metrics</h3>
        <p><strong>Runs Used:</strong> {status.get('runs_used', 'N/A')}</p>
        <p><strong>Exit Code:</strong> {status.get('exit_code', 'N/A')}</p>
        {f'<p><strong>CI Fails:</strong> {status.get("ci_fails", 0)}</p>' if 'ci_fails' in status else ''}
        {f'<p><strong>CI Warns:</strong> {status.get("ci_warns", 0)}</p>' if 'ci_warns' in status else ''}
    </div>
    
    <h3>📁 Available Files</h3>
    <ul class="file-list">""")
    
    # Add files
    for file_key, file_info in files.items():
        if file_key == "badges_dir":
            continue  # Handle separately
        
        status_icon = "✅" if file_info["exists"] else "❌"
        status_class = "exists" if file_info["exists"] else "missing"
        
        if file_info["exists"]:
            lines.append(f"""        <li>
            {status_icon} <a href="{make_url(file_info['path'])}">{file_info['path']}</a>
            <span class="{status_class}"> (available)</span>
        </li>""")
        else:
            lines.append(f"""        <li>
            {status_icon} {file_info['path']}
            <span class="{status_class}"> (not generated)</span>
        </li>""")
    
    lines.append("""    </ul>
    
    <h3>🏷️ Badge Endpoints</h3>
    <div class="badges-grid">""")
    
    # Add badge endpoints
    badges_dir = files.get("badges_dir", {})
    if badges_dir.get("exists") and badges_dir.get("items"):
        for badge_name, badge_info in badges_dir["items"].items():
            lines.append(f"""        <div class="badge-item">
            <a href="{make_url(badge_info['path'])}">{badge_name}</a>
        </div>""")
    else:
        lines.append("""        <div class="badge-item">
            <span style="color: #666;">No badge endpoints available</span>
        </div>""")
    
    lines.append(f"""    </div>
    
    <div class="timestamp">
        <p><strong>Generated:</strong> {index['generated_at_utc']}</p>
        <p><strong>Output Directory:</strong> {index['out_dir']}</p>
    </div>
</body>
</html>""")
    
    return "\n".join(lines)


def write_text(path: str, content: str, *, encoding: str = "utf-8-sig", is_json: bool = False) -> None:
    """Write text file with UTF-8 BOM for Windows compatibility"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # JSON files should not have BOM
    file_encoding = "utf-8" if is_json else encoding
    with open(path, "w", encoding=file_encoding) as f:
        f.write(content)
