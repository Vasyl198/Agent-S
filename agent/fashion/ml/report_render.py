# agent/fashion/ml/report_render.py
"""Human-readable report rendering for dataset_report.py"""

from datetime import datetime
from typing import Dict, Any, Optional


def render_markdown(report: Dict[str, Any], title: str = "ML Dataset Report", json_link: Optional[str] = None) -> str:
    """Generate Markdown report from dataset report JSON"""
    
    lines = []
    
    # Header
    lines.append(f"# {title}")
    lines.append("")
    
    # Metadata
    if json_link:
        lines.append(f"**Full JSON:** [{json_link}]({json_link})")
        lines.append("")
    
    # CI Summary if available
    if "ci_summary" in report:
        ci = report["ci_summary"]
        status_emoji = "✅" if ci["ok"] else "❌"
        lines.append(f"**Status:** {status_emoji} {'OK' if ci['ok'] else 'FAIL'} (exit code: {ci['exit_code']})")
        lines.append(f"**Runs used:** {ci.get('runs_used', 'N/A')}")
        lines.append("")
    
    # Summary Section
    lines.append("## Summary")
    lines.append("")
    
    # Basic metrics table
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Runs used | {report.get('window', {}).get('used_runs', 'N/A')} |")
    lines.append(f"| Candidates (mean/min/max) | {report.get('candidates', {}).get('mean', 'N/A')} / {report.get('candidates', {}).get('min', 'N/A')} / {report.get('candidates', {}).get('max', 'N/A')} |")
    lines.append(f"| Evaluated (mean/min/max) | {report.get('evaluated', {}).get('mean', 'N/A')} / {report.get('evaluated', {}).get('min', 'N/A')} / {report.get('evaluated', {}).get('max', 'N/A')} |")
    
    # Pipeline distribution
    if "ci_summary" in report:
        ci = report["ci_summary"]
        if "pipelines" in ci:
            pipelines = ci["pipelines"]
            pipeline_str = ", ".join([f"{k}: {v}" for k, v in pipelines.items()])
            lines.append(f"| Pipelines | {pipeline_str} |")
    
    lines.append("")
    
    # Comparison Section (7.5.13)
    if "comparison" in report:
        lines.append("## Comparison")
        lines.append("")
        
        comparison = report["comparison"]
        
        # Baseline source
        baseline_source = comparison.get("baseline_source", {})
        if baseline_source:
            kind = baseline_source.get("kind", "unknown")
            path = baseline_source.get("path", "unknown")
            lines.append(f"**Baseline Source:** {kind} - `{path}`")
            lines.append("")
        
        # Comparison table
        lines.append("| Metric | Baseline | Current | Δ | Status |")
        lines.append("|--------|----------|---------|---|--------|")
        
        # Helper functions
        def format_delta(value):
            if value is None:
                return "—"
            if value > 0:
                return f"+{value:.3f}"
            elif value < 0:
                return f"{value:.3f}"
            else:
                return "0.000"
        
        def format_value(value):
            if value is None:
                return "—"
            return f"{value:.3f}"
        
        def status_emoji(status):
            if status == "improved":
                return "✅"
            elif status == "regressed":
                return "❌"
            elif status == "same":
                return "➖"
            elif status.startswith("missing"):
                return "❔"
            else:
                return "❓"
        
        def status_class(status):
            if status == "improved":
                return "metric-improved"
            elif status == "regressed":
                return "metric-regressed"
            elif status == "same":
                return "metric-same"
            elif status.startswith("missing"):
                return "metric-missing"
            else:
                return ""
        
        # Extract data
        baseline = comparison.get("baseline", {})
        current = comparison.get("current", {})
        delta = comparison.get("delta", {})
        status = comparison.get("status", {})
        
        # runs_used
        baseline_runs = baseline.get("runs_used")
        current_runs = current.get("runs_used")
        delta_runs = delta.get("runs_used")
        status_runs = status.get("runs_used", "unknown")
        status_runs_class = status_class(status_runs)
        
        lines.append(f"| runs_used | {baseline_runs if baseline_runs is not None else '—'} | {current_runs if current_runs is not None else '—'} | {format_delta(delta_runs)} | {status_emoji(status_runs)} {status_runs} |")
        
        # ranker.mrr
        baseline_mrr = baseline.get("ranker", {}).get("mrr")
        current_mrr = current.get("ranker", {}).get("mrr")
        delta_mrr = delta.get("ranker", {}).get("mrr")
        status_mrr = status.get("ranker_mrr", "unknown")
        
        lines.append(f"| ranker.mrr | {format_value(baseline_mrr)} | {format_value(current_mrr)} | {format_delta(delta_mrr)} | {status_emoji(status_mrr)} {status_mrr} |")
        
        # ranker.top1_accuracy
        baseline_top1 = baseline.get("ranker", {}).get("top1_accuracy")
        current_top1 = current.get("ranker", {}).get("top1_accuracy")
        delta_top1 = delta.get("ranker", {}).get("top1_accuracy")
        status_top1 = status.get("ranker_top1_accuracy", "unknown")
        
        lines.append(f"| ranker.top1_accuracy | {format_value(baseline_top1)} | {format_value(current_top1)} | {format_delta(delta_top1)} | {status_emoji(status_top1)} {status_top1} |")
        
        # chooser.flat_rate
        baseline_flat = baseline.get("chooser", {}).get("flat_rate")
        current_flat = current.get("chooser", {}).get("flat_rate")
        delta_flat = delta.get("chooser", {}).get("flat_rate")
        status_flat = status.get("chooser_flat_rate", "unknown")
        
        lines.append(f"| chooser.flat_rate | {format_value(baseline_flat)} | {format_value(current_flat)} | {format_delta(delta_flat)} | {status_emoji(status_flat)} {status_flat} |")
        
        lines.append("")
        
        # Overall status
        overall_status = status.get("overall", "unknown")
        lines.append(f"**Overall:** {status_emoji(overall_status)} {overall_status}")
        lines.append("")
    
    # Comparison (Scoped) Section (7.5.17)
    if "comparison_scoped" in report:
        lines.append("## Comparison (Scoped)")
        lines.append("")
        
        comparison_scoped = report["comparison_scoped"]
        regression_gates_scoped = report.get("regression_gates_scoped", {})
        
        # Sort scope keys for stable output
        scope_keys = sorted(comparison_scoped.keys())
        
        for scope_key in scope_keys:
            comparison = comparison_scoped[scope_key]
            
            # Scope header
            lines.append(f"### {scope_key}")
            lines.append("")
            
            # Baseline source
            baseline_source = comparison.get("baseline_source", {})
            if baseline_source:
                kind = baseline_source.get("kind", "unknown")
                path = baseline_source.get("path", "unknown")
                name = baseline_source.get("name", "unknown")
                scope = baseline_source.get("scope", "unknown")
                
                source_parts = [f"kind: {kind}", f"name: {name}", f"scope: {scope}"]
                
                # Add scope-specific details
                if "pipeline" in baseline_source:
                    source_parts.append(f"pipeline: {baseline_source['pipeline']}")
                elif "day" in baseline_source:
                    source_parts.append(f"day: {baseline_source['day']}")
                elif "window" in baseline_source:
                    source_parts.append(f"window: {baseline_source['window']}")
                
                source_str = ", ".join(source_parts)
                lines.append(f"**Baseline:** {source_str}")
                lines.append(f"**Path:** `{path}`")
                lines.append("")
            
            # Comparison table
            lines.append("| Metric | Baseline | Current | Δ | Status |")
            lines.append("|--------|----------|---------|---|--------|")
            lines.append("{: .comparison-table}")
            
            # Helper functions (reuse from above)
            def format_delta(value):
                if value is None:
                    return "—"
                if value > 0:
                    return f"+{value:.3f}"
                elif value < 0:
                    return f"{value:.3f}"
                else:
                    return "0.000"
            
            def format_value(value):
                if value is None:
                    return "—"
                return f"{value:.3f}"
            
            def status_emoji(status):
                if status == "improved":
                    return "✅"
                elif status == "regressed":
                    return "❌"
                elif status == "same":
                    return "➖"
                elif status.startswith("missing"):
                    return "❔"
                else:
                    return "❓"
            
            # Extract data
            baseline = comparison.get("baseline", {})
            current = comparison.get("current", {})
            delta = comparison.get("delta", {})
            status = comparison.get("status", {})
            
            # runs_used
            baseline_runs = baseline.get("runs_used")
            current_runs = current.get("runs_used")
            delta_runs = delta.get("runs_used")
            status_runs = status.get("runs_used", "unknown")
            
            lines.append(f"| runs_used | {baseline_runs if baseline_runs is not None else '—'} | {current_runs if current_runs is not None else '—'} | {format_delta(delta_runs)} | {status_emoji(status_runs)} {status_runs} |")
            
            # ranker.mrr
            baseline_mrr = baseline.get("ranker", {}).get("mrr")
            current_mrr = current.get("ranker", {}).get("mrr")
            delta_mrr = delta.get("ranker", {}).get("mrr")
            status_mrr = status.get("ranker_mrr", "unknown")
            
            lines.append(f"| ranker.mrr | {format_value(baseline_mrr)} | {format_value(current_mrr)} | {format_delta(delta_mrr)} | {status_emoji(status_mrr)} {status_mrr} |")
            
            # ranker.top1_accuracy
            baseline_top1 = baseline.get("ranker", {}).get("top1_accuracy")
            current_top1 = current.get("ranker", {}).get("top1_accuracy")
            delta_top1 = delta.get("ranker", {}).get("top1_accuracy")
            status_top1 = status.get("ranker_top1_accuracy", "unknown")
            
            lines.append(f"| ranker.top1_accuracy | {format_value(baseline_top1)} | {format_value(current_top1)} | {format_delta(delta_top1)} | {status_emoji(status_top1)} {status_top1} |")
            
            # chooser.flat_rate
            baseline_flat = baseline.get("chooser", {}).get("flat_rate")
            current_flat = current.get("chooser", {}).get("flat_rate")
            delta_flat = delta.get("chooser", {}).get("flat_rate")
            status_flat = status.get("chooser_flat_rate", "unknown")
            
            lines.append(f"| chooser.flat_rate | {format_value(baseline_flat)} | {format_value(current_flat)} | {format_delta(delta_flat)} | {status_emoji(status_flat)} {status_flat} |")
            
            lines.append("")
            
            # Regression gates for this scope
            scope_regression_gates = regression_gates_scoped.get(scope_key, {})
            if scope_regression_gates:
                lines.append("**Regression gates:** ")
                
                # Check if any gate failed
                any_failed = any(gate.get("failed", False) for gate in scope_regression_gates.values())
                
                if any_failed:
                    lines.append("❌ **FAIL**")
                    for gate_name, gate_info in scope_regression_gates.items():
                        if gate_info.get("failed", False):
                            threshold = gate_info.get("threshold", "N/A")
                            actual = gate_info.get("actual", "N/A")
                            lines.append(f"  - {gate_name}: threshold={threshold}, actual={actual}")
                else:
                    lines.append("✅ **OK**")
                    for gate_name, gate_info in scope_regression_gates.items():
                        threshold = gate_info.get("threshold", "N/A")
                        actual = gate_info.get("actual", "N/A")
                        lines.append(f"  - {gate_name}: threshold={threshold}, actual={actual}")
                
                lines.append("")
    
    # Gates Section
    lines.append("## Gates")
    lines.append("")
    
    # Try CI summary first, then legacy gates
    if "ci_summary" in report:
        ci = report["ci_summary"]
        gates = ci["gates"]
        status_emoji = "✅" if gates["overall_ok"] else "❌"
        lines.append(f"**Overall:** {status_emoji} {'OK' if gates['overall_ok'] else 'FAIL'}")
        lines.append(f"**Failures:** {gates['fails']}")
        lines.append(f"**Warnings:** {gates['warns']}")
        lines.append("")
        
        if gates["violations"]:
            lines.append("**Violations:**")
            for violation in gates["violations"][:20]:  # Limit to 20
                severity_emoji = "❌" if violation["severity"] == "fail" else "⚠️"
                scope_info = f" [{violation.get('scope', 'global')}]" if violation.get("scope") else ""
                lines.append(f"- {severity_emoji}{scope_info} **{violation['key']}**: {violation['message']}")
                lines.append(f"  - Actual: {violation['actual']}, Expected: {violation['expected']}")
            lines.append("")
    elif "gates" in report:
        gates = report["gates"]
        status_emoji = "✅" if gates["ok"] else "❌"
        lines.append(f"**Overall:** {status_emoji} {'OK' if gates['ok'] else 'FAIL'}")
        lines.append("")
        
        if gates.get("violations"):
            lines.append("**Violations:**")
            for violation in gates["violations"][:20]:
                severity_emoji = "❌" if violation["severity"] == "fail" else "⚠️"
                lines.append(f"- {severity_emoji} **{violation['key']}**: {violation['message']}")
                lines.append(f"  - Actual: {violation['actual']}, Expected: {violation['expected']}")
            lines.append("")
    
    # Scoped gates details
    if "checks" in report:
        checks = report["checks"]
        lines.append(f"**Check Mode:** {checks['mode']}")
        lines.append(f"**Scopes:** {', '.join(checks['scopes'])}")
        lines.append("")
        
        for scope_name, scope_result in checks["results"].items():
            status_emoji = "✅" if scope_result["ok"] else "❌"
            lines.append(f"### {scope_name.title()} Gates: {status_emoji} {'OK' if scope_result['ok'] else 'FAIL'}")
            
            if scope_result.get("violations"):
                for violation in scope_result["violations"][:10]:
                    severity_emoji = "❌" if violation["severity"] == "fail" else "⚠️"
                    lines.append(f"- {severity_emoji} **{violation['key']}**: {violation['message']}")
            lines.append("")
    
    # Ranker metrics
    if "ranker" in report and report["ranker"].get("groups", 0) > 0:
        lines.append("## Ranker Metrics")
        lines.append("")
        ranker = report["ranker"]
        lines.append(f"- **Groups:** {ranker.get('groups', 0)}")
        lines.append(f"- **Rows:** {ranker.get('rows', 0)}")
        lines.append(f"- **Top-1 Accuracy:** {ranker.get('top1_accuracy', 'N/A')}")
        lines.append(f"- **MRR:** {ranker.get('mrr', 'N/A')}")
        if ranker.get("pred_key"):
            lines.append(f"- **Prediction Key:** {ranker['pred_key']}")
        lines.append("")
    
    # Chooser diagnostics
    if "chooser" in report and report["chooser"].get("groups", 0) > 0:
        lines.append("## Chooser Diagnostics")
        lines.append("")
        chooser = report["chooser"]
        lines.append(f"- **Groups:** {chooser.get('groups', 0)}")
        lines.append(f"- **Mean Entropy:** {chooser.get('mean_entropy', 'N/A')}")
        lines.append(f"- **Mean Margin Top1-Top2:** {chooser.get('mean_margin_top1_top2', 'N/A')}")
        lines.append(f"- **Flat Rate:** {chooser.get('flat_rate', 'N/A')}")
        if chooser.get("prob_key"):
            lines.append(f"- **Probability Key:** {chooser['prob_key']}")
        lines.append("")
    
    # Hybrid info
    if "hybrid" in report and report["hybrid"].get("enabled_runs", 0) > 0:
        lines.append("## Hybrid")
        lines.append("")
        hybrid = report["hybrid"]
        lines.append(f"- **Enabled Runs:** {hybrid.get('enabled_runs', 0)}")
        lines.append(f"- **Chooser Flat True:** {hybrid.get('chooser_flat_true', 0)}")
        lines.append(f"- **Chooser Flat False:** {hybrid.get('chooser_flat_false', 0)}")
        lines.append("")
    
    # Trend section
    if "trend" in report:
        lines.append("## Trend")
        lines.append("")
        trend = report["trend"]
        lines.append(f"**Mode:** {trend.get('mode', 'N/A')}")
        if trend.get("last_days"):
            lines.append(f"**Last Days:** {trend['last_days']}")
        lines.append("")
        
        lines.append("| Day | Runs | Pipelines | Ranker MRR | Ranker Top1 | Chooser Flat Rate |")
        lines.append("|-----|------|-----------|------------|------------|-------------------|")
        
        for day_data in trend.get("days", []):
            pipelines_str = ", ".join([f"{k}: {v}" for k, v in day_data.get("pipelines", {}).items()])
            ranker_mrr = day_data.get("ranker", {}).get("mrr", "N/A")
            ranker_top1 = day_data.get("ranker", {}).get("top1_accuracy", "N/A")
            chooser_flat = day_data.get("chooser", {}).get("flat_rate", "N/A")
            
            lines.append(f"| {day_data.get('day', 'N/A')} | {day_data.get('runs', 0)} | {pipelines_str} | {ranker_mrr} | {ranker_top1} | {chooser_flat} |")
        
        lines.append("")
    
    # Pipeline breakdown
    if "pipelines_breakdown" in report:
        lines.append("## Pipelines Breakdown")
        lines.append("")
        
        for pipeline_name, pipeline_report in report["pipelines_breakdown"].items():
            lines.append(f"### {pipeline_name.title()}")
            lines.append("")
            lines.append(f"- **Runs:** {pipeline_report.get('runs', 0)}")
            
            # Ranker metrics for this pipeline
            if pipeline_report.get("ranker", {}).get("groups", 0) > 0:
                ranker = pipeline_report["ranker"]
                lines.append(f"- **Ranker MRR:** {ranker.get('mrr', 'N/A')}")
                lines.append(f"- **Ranker Top1:** {ranker.get('top1_accuracy', 'N/A')}")
            
            # Chooser metrics for this pipeline
            if pipeline_report.get("chooser", {}).get("groups", 0) > 0:
                chooser = pipeline_report["chooser"]
                lines.append(f"- **Chooser Flat Rate:** {chooser.get('flat_rate', 'N/A')}")
                lines.append(f"- **Chooser Mean Entropy:** {chooser.get('mean_entropy', 'N/A')}")
            
            lines.append("")
    
    # Footer
    lines.append("---")
    lines.append(f"*Report generated at {datetime.now().isoformat()}*")
    
    return "\n".join(lines)


def render_html(report: Dict[str, Any], title: str = "ML Dataset Report", json_link: Optional[str] = None) -> str:
    """Generate HTML report from dataset report JSON"""
    
    # Generate markdown first
    markdown_content = render_markdown(report, title, json_link)
    
    # Simple HTML template with embedded markdown
    html_template = f"""<!DOCTYPE html>
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
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        code {{
            background-color: #f1f3f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .status-ok {{ color: #28a745; font-weight: bold; }}
        .status-fail {{ color: #dc3545; font-weight: bold; }}
        .status-warn {{ color: #ffc107; font-weight: bold; }}
        .violation {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 5px 0;
        }}
        .violation.fail {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }}
        .comparison-table td.metric-improved {{ 
            background-color: #d4edda; 
            color: #155724; 
        }}
        .comparison-table td.metric-regressed {{ 
            background-color: #f8d7da; 
            color: #721c24; 
        }}
        .comparison-table td.metric-same {{ 
            background-color: #f8f9fa; 
        }}
        .comparison-table td.metric-missing {{ 
            background-color: #fff3cd; 
            color: #856404; 
        }}
        .baseline-source {{
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <pre>{markdown_content}</pre>
</body>
</html>"""
    
    return html_template
