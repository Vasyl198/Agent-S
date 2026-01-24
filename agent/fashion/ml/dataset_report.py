# agent/fashion/ml/dataset_report.py
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from agent.fashion.ml.metrics import (
    compute_group_ranking_metrics,
    compute_chooser_diagnostics,
)
from agent.fashion.ml.ci_gates import GateConfig, decide_gates

EXIT_OK = 0
EXIT_GATE_FAIL = 20

def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except Exception:
                # skip broken line
                continue
    return runs

def _safe_get(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _summarize_pipeline(run: Dict[str, Any]) -> str:
    opt = run.get("optimization", {}) if isinstance(run, dict) else {}
    if not isinstance(opt, dict):
        return "unknown"
    if "hybrid" in opt:
        return "hybrid"
    if "chooser" in opt:
        return "chooser"
    if "ranker" in opt:
        return "ranker"
    return "baseline"

def build_dataset_report(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_runs = len(runs)

    # Basic counts
    candidate_counts: List[int] = []
    evaluated_counts: List[int] = []
    pipeline_counts: Dict[str, int] = {}

    # Hybrid specifics
    hybrid_enabled = 0
    chooser_flat_true = 0
    chooser_flat_false = 0

    for r in runs:
        pipeline = _summarize_pipeline(r)
        pipeline_counts[pipeline] = pipeline_counts.get(pipeline, 0) + 1

        cands = _safe_get(r, "optimization", "candidates", default=[])
        if isinstance(cands, list):
            candidate_counts.append(len(cands))
            evaluated = sum(1 for c in cands if isinstance(c, dict) and c.get("evaluated", False))
            evaluated_counts.append(evaluated)

        hy = _safe_get(r, "optimization", "hybrid", default=None)
        if isinstance(hy, dict) and hy.get("enabled") is True:
            hybrid_enabled += 1
            if hy.get("chooser_flat") is True:
                chooser_flat_true += 1
            elif hy.get("chooser_flat") is False:
                chooser_flat_false += 1

    def _mean(xs: List[int]) -> Optional[float]:
        if not xs:
            return None
        return sum(xs) / float(len(xs))

    def _min(xs: List[int]) -> Optional[int]:
        return min(xs) if xs else None

    def _max(xs: List[int]) -> Optional[int]:
        return max(xs) if xs else None

    # Ranker metrics (group-aware) for pred_score
    ranker_metrics = compute_group_ranking_metrics(runs, pred_key="pred_score")

    # Chooser diagnostics (group-aware) for p_choose
    chooser_diag = compute_chooser_diagnostics(runs, prob_key="p_choose")

    report: Dict[str, Any] = {
        "ok": True,
        "runs": n_runs,
        "pipelines": pipeline_counts,
        "candidates": {
            "mean": _mean(candidate_counts),
            "min": _min(candidate_counts),
            "max": _max(candidate_counts),
        },
        "evaluated": {
            "mean": _mean(evaluated_counts),
            "min": _min(evaluated_counts),
            "max": _max(evaluated_counts),
        },
        "ranker": {
            "groups": ranker_metrics.groups,
            "rows": ranker_metrics.rows,
            "top1_accuracy": ranker_metrics.top1_accuracy,
            "mrr": ranker_metrics.mrr,
            "pred_key": "pred_score",
        },
        "chooser": {
            "groups": chooser_diag.groups,
            "mean_entropy": chooser_diag.mean_entropy,
            "mean_margin_top1_top2": chooser_diag.mean_margin_top1_top2,
            "flat_rate": chooser_diag.flat_rate,
            "prob_key": "p_choose",
        },
        "hybrid": {
            "enabled_runs": hybrid_enabled,
            "chooser_flat_true": chooser_flat_true,
            "chooser_flat_false": chooser_flat_false,
        },
    }

    return report

def detect_pipeline(run: dict) -> str:
    """Детерминированное определение pipeline для run"""
    opt = run.get("optimization") or {}
    if (opt.get("hybrid") or {}).get("enabled") is True:
        return "hybrid"
    if "ranker" in opt and opt["ranker"] is not None:
        return "ranker"
    if "chooser" in opt and opt["chooser"] is not None:
        return "chooser"
    return "baseline"

def build_report_for_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Внутренняя функция для построения отчета по списку runs"""
    n_runs = len(runs)

    # Basic counts
    candidate_counts: List[int] = []
    evaluated_counts: List[int] = []
    pipeline_counts: Dict[str, int] = {}

    # Hybrid specifics
    hybrid_enabled = 0
    chooser_flat_true = 0
    chooser_flat_false = 0

    for r in runs:
        pipeline = detect_pipeline(r)
        pipeline_counts[pipeline] = pipeline_counts.get(pipeline, 0) + 1

        cands = _safe_get(r, "optimization", "candidates", default=[])
        if isinstance(cands, list):
            candidate_counts.append(len(cands))
            evaluated = sum(1 for c in cands if isinstance(c, dict) and c.get("evaluated", False))
            evaluated_counts.append(evaluated)

        hy = _safe_get(r, "optimization", "hybrid", default=None)
        if isinstance(hy, dict) and hy.get("enabled") is True:
            hybrid_enabled += 1
            if hy.get("chooser_flat") is True:
                chooser_flat_true += 1
            elif hy.get("chooser_flat") is False:
                chooser_flat_false += 1

    def _mean(xs: List[int]) -> Optional[float]:
        if not xs:
            return None
        return sum(xs) / float(len(xs))

    def _min(xs: List[int]) -> Optional[int]:
        return min(xs) if xs else None

    def _max(xs: List[int]) -> Optional[int]:
        return max(xs) if xs else None

    # Ranker metrics (group-aware) for pred_score
    ranker_metrics = compute_group_ranking_metrics(runs, pred_key="pred_score")

    # Chooser diagnostics (group-aware) for p_choose
    chooser_diag = compute_chooser_diagnostics(runs, prob_key="p_choose")

    report: Dict[str, Any] = {
        "ok": True,
        "runs": n_runs,
        "pipelines": pipeline_counts,
        "candidates": {
            "mean": _mean(candidate_counts),
            "min": _min(candidate_counts),
            "max": _max(candidate_counts),
        },
        "evaluated": {
            "mean": _mean(evaluated_counts),
            "min": _min(evaluated_counts),
            "max": _max(evaluated_counts),
        },
        "ranker": {
            "groups": ranker_metrics.groups,
            "rows": ranker_metrics.rows,
            "top1_accuracy": ranker_metrics.top1_accuracy,
            "mrr": ranker_metrics.mrr,
            "pred_key": "pred_score",
        },
        "chooser": {
            "groups": chooser_diag.groups,
            "mean_entropy": chooser_diag.mean_entropy,
            "mean_margin_top1_top2": chooser_diag.mean_margin_top1_top2,
            "flat_rate": chooser_diag.flat_rate,
            "prob_key": "p_choose",
        },
        "hybrid": {
            "enabled_runs": hybrid_enabled,
            "chooser_flat_true": chooser_flat_true,
            "chooser_flat_false": chooser_flat_false,
        },
    }

    return report

def extract_day_key(ts_utc: str) -> str:
    """Извлекает день из ts_utc строки"""
    if not ts_utc:
        return "unknown"
    
    # Формат YYYYMMDDT...Z -> первые 8 символов
    if len(ts_utc) >= 8 and ts_utc[4] == '0' and ts_utc[6] == '0':
        return ts_utc[:8]
    
    # Формат YYYY-MM-DD... -> первые 10 символов
    if len(ts_utc) >= 10 and ts_utc[4] == '-':
        return ts_utc[:10]
    
    # Fallback
    return "unknown"

def build_trend_report(runs: List[Dict[str, Any]], trend_last_days: Optional[int] = None, trend_by_pipeline: bool = False) -> Dict[str, Any]:
    """Строит trend report по дням"""
    # Группируем по дням
    day_groups: Dict[str, List[Dict[str, Any]]] = {}
    for run in runs:
        day = extract_day_key(run.get("ts_utc", ""))
        day_groups.setdefault(day, []).append(run)
    
    # Сортируем дни
    sorted_days = sorted(day_groups.keys())
    
    # Ограничиваем количество дней если нужно
    if trend_last_days is not None:
        sorted_days = sorted_days[-trend_last_days:]
    
    # Строим отчет для каждого дня
    days_data = []
    for day in sorted_days:
        day_runs = day_groups[day]
        day_report = build_report_for_runs(day_runs)
        
        # Формируем структуру дня
        day_data = {
            "day": day,
            "runs": len(day_runs),
            "pipelines": day_report.get("pipelines", {}),
            "ranker": {
                "mrr": day_report.get("ranker", {}).get("mrr"),
                "top1_accuracy": day_report.get("ranker", {}).get("top1_accuracy"),
                "rows": day_report.get("ranker", {}).get("rows"),
                "groups": day_report.get("ranker", {}).get("groups"),
            },
            "chooser": {
                "flat_rate": day_report.get("chooser", {}).get("flat_rate"),
                "mean_entropy": day_report.get("chooser", {}).get("mean_entropy"),
                "mean_margin_top1_top2": day_report.get("chooser", {}).get("mean_margin_top1_top2"),
                "groups": day_report.get("chooser", {}).get("groups"),
            },
            "evaluated": day_report.get("evaluated", {}),
            "candidates": day_report.get("candidates", {}),
        }
        
        # Добавляем breakdown по pipeline если нужно
        if trend_by_pipeline:
            pipeline_groups = {}
            for run in day_runs:
                pipeline = detect_pipeline(run)
                pipeline_groups.setdefault(pipeline, []).append(run)
            
            by_pipeline = {}
            for pipeline, pipeline_runs in pipeline_groups.items():
                pipeline_report = build_report_for_runs(pipeline_runs)
                by_pipeline[pipeline] = {
                    "runs": len(pipeline_runs),
                    "ranker": {
                        "mrr": pipeline_report.get("ranker", {}).get("mrr"),
                        "top1_accuracy": pipeline_report.get("ranker", {}).get("top1_accuracy"),
                        "rows": pipeline_report.get("ranker", {}).get("rows"),
                        "groups": pipeline_report.get("ranker", {}).get("groups"),
                    },
                    "chooser": {
                        "flat_rate": pipeline_report.get("chooser", {}).get("flat_rate"),
                        "mean_entropy": pipeline_report.get("chooser", {}).get("mean_entropy"),
                        "mean_margin_top1_top2": pipeline_report.get("chooser", {}).get("mean_margin_top1_top2"),
                        "groups": pipeline_report.get("chooser", {}).get("groups"),
                    },
                    "evaluated": pipeline_report.get("evaluated", {}),
                    "candidates": pipeline_report.get("candidates", {}),
                }
            
            day_data["by_pipeline"] = by_pipeline
        
        days_data.append(day_data)
    
    return {
        "mode": "day",
        "days": days_data,
        "last_days": trend_last_days if trend_last_days is not None else len(sorted_days)
    }

def apply_gates_to_report(report: Dict[str, Any], cfg: GateConfig) -> Dict[str, Any]:
    """Применяет gates к отчету и добавляет gates информацию"""
    from agent.fashion.ml.ci_gates import decide_gates
    
    gr = decide_gates(report, cfg)
    gates_info = {
        "ok": gr.ok,
        "config": {
            "min_runs": cfg.min_runs,
            "min_ranker_mrr": cfg.min_ranker_mrr,
            "min_ranker_top1": cfg.min_ranker_top1,
            "max_chooser_flat_rate": cfg.max_chooser_flat_rate,
            "fail_on_warn": cfg.fail_on_warn,
        },
        "violations": [
            {
                "key": v.key,
                "severity": v.severity,
                "message": v.message,
                "actual": v.actual,
                "expected": v.expected,
            }
            for v in gr.violations
        ],
    }
    return gates_info

def gate_applicability_for_pipeline(pipeline: str) -> dict:
    """Возвращает требования к метрикам для каждого pipeline типа"""
    return {
        "require_ranker": pipeline in ("ranker", "hybrid"),
        "require_chooser": pipeline in ("chooser", "hybrid"),
    }

def apply_pipeline_gates(pipelines_breakdown: Dict[str, Any], cfg: GateConfig) -> Dict[str, Any]:
    """Применяет gates к каждому pipeline с учетом applicability"""
    gates_by_pipeline = {}
    overall_ok = True
    
    for pipeline, pipeline_report in pipelines_breakdown.items():
        # Получаем требования для этого pipeline
        applicability = gate_applicability_for_pipeline(pipeline)
        
        # Создаем config с учетом applicability
        pipeline_cfg = GateConfig(
            min_runs=cfg.min_runs,
            min_ranker_mrr=cfg.min_ranker_mrr,
            min_ranker_top1=cfg.min_ranker_top1,
            max_chooser_flat_rate=cfg.max_chooser_flat_rate,
            fail_on_warn=cfg.fail_on_warn,
            require_ranker=applicability["require_ranker"],
            require_chooser=applicability["require_chooser"],
        )
        
        gates_info = apply_gates_to_report(pipeline_report, pipeline_cfg)
        gates_by_pipeline[pipeline] = gates_info
        if not gates_info["ok"]:
            overall_ok = False
    
    return {
        "by_pipeline": gates_by_pipeline,
        "overall_ok": overall_ok
    }

def apply_trend_day_gates(trend_report: Dict[str, Any], cfg: GateConfig) -> Dict[str, Any]:
    """Применяет gates к последнему дню в тренде"""
    if not trend_report.get("days"):
        return {
            "ok": False,
            "error": "No trend days available",
            "violations": []
        }
    
    # Берем последний день
    last_day = trend_report["days"][-1]
    
    # Создаем отчет в формате, понятном для decide_gates
    day_report_for_gates = {
        "runs": last_day["runs"],
        "ranker": last_day["ranker"],
        "chooser": last_day["chooser"],
    }
    
    gates_info = apply_gates_to_report(day_report_for_gates, cfg)
    gates_info["day"] = last_day["day"]
    gates_info["day_runs"] = last_day["runs"]
    
    return gates_info

def build_ci_summary(report: dict, exit_code: int, check_context: dict) -> dict:
    """Строит компактный CI summary для машинного чтения"""
    
    # Базовая информация
    summary = {
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "scope_mode": "scoped" if check_context.get("scopes") else "default",
        "scopes": check_context.get("scopes", []),
        "runs_used": report.get("window", {}).get("used_runs", 0),
        "pipelines": report.get("pipelines", {}),
    }
    
    # Раннер метрики
    ranker_data = report.get("ranker", {})
    summary["ranker"] = {
        "mrr": ranker_data.get("mrr"),
        "top1_accuracy": ranker_data.get("top1_accuracy"),
        "groups": ranker_data.get("groups", 0),
    }
    
    # Chooser метрики
    chooser_data = report.get("chooser", {})
    summary["chooser"] = {
        "flat_rate": chooser_data.get("flat_rate"),
        "mean_entropy": chooser_data.get("mean_entropy"),
        "groups": chooser_data.get("groups", 0),
    }
    
    # Gates информация
    gates_info = {
        "overall_ok": exit_code == 0,
        "fails": 0,
        "warns": 0,
        "violations": []
    }
    
    # Собираем violations из разных источников
    all_violations = []
    
    # Scoped gates
    if "checks" in report:
        checks = report["checks"]
        for scope_name, scope_result in checks.get("results", {}).items():
            for violation in scope_result.get("violations", []):
                all_violations.append({
                    "scope": scope_name,
                    **violation
                })
    
    # Legacy gates
    elif "gates" in report:
        all_violations.extend(report["gates"].get("violations", []))
    
    # Pipeline gates
    if "gates_by_pipeline" in report:
        for pipeline, pipeline_gates in report["gates_by_pipeline"].get("by_pipeline", {}).items():
            for violation in pipeline_gates.get("violations", []):
                all_violations.append({
                    "scope": f"pipeline_{pipeline}",
                    **violation
                })
    
    # Trend day gates
    if "trend_day_gates" in report:
        for violation in report["trend_day_gates"].get("violations", []):
            all_violations.append({
                "scope": "trend_day",
                **violation
            })
    
    # Считаем fails/warns и обрезаем violations
    for violation in all_violations:
        if violation.get("severity") == "fail":
            gates_info["fails"] += 1
        elif violation.get("severity") == "warn":
            gates_info["warns"] += 1
    
    # Обрезаем до 20 violations чтобы не раздувать summary
    gates_info["violations"] = all_violations[:20]
    
    summary["gates"] = gates_info
    
    return summary

def _add_ci_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--check", action="store_true", help="Enable CI gates; non-zero exit if fail")
    p.add_argument("--min-runs", type=int, default=50)
    p.add_argument("--min-ranker-mrr", type=float, default=0.4)
    p.add_argument("--min-ranker-top1", type=float, default=0.2)
    p.add_argument("--max-chooser-flat-rate", type=float, default=None)
    p.add_argument("--fail-on-warn", action="store_true")
    # 7.5.2: pipeline breakdown flags
    p.add_argument("--by-pipeline", action="store_true", help="Break down metrics by pipeline type")
    p.add_argument("--last-n", type=int, default=None, help="Use only last N runs (sorted by ts_utc or file order)")
    # 7.5.3: trend report flags
    p.add_argument("--trend-day", action="store_true", help="Enable day-bucket trend report")
    p.add_argument("--trend-last-days", type=int, default=None, help="Use only last N days in trend report")
    p.add_argument("--trend-by-pipeline", action="store_true", help="Break down trend by pipeline type")
    # 7.5.4: extended CI gates flags
    p.add_argument("--check-by-pipeline", action="store_true", help="Apply CI gates per pipeline type")
    p.add_argument("--check-trend-day", action="store_true", help="Apply CI gates to last trend day")
    # 7.5.5: scoped gates flags
    p.add_argument("--check-scope", action="append", choices=["all", "window", "trend_day", "by_pipeline"], 
                   help="Check scope(s). Can be repeated. Default: all")
    p.add_argument("--check-mode", choices=["and", "or"], default="and", 
                   help="How to combine multiple check scopes. Default: and")
    # 7.5.7: CI summary flags
    p.add_argument("--ci-summary", action="store_true", help="Add compact CI summary to report")
    p.add_argument("--ci-summary-out", type=str, default=None, help="Write CI summary to separate file")
    # 7.5.8: Human-readable report flags
    p.add_argument("--md-out", type=str, default=None, help="Write Markdown report to file")
    p.add_argument("--html-out", type=str, default=None, help="Write HTML report to file")
    p.add_argument("--report-title", type=str, default="ML Dataset Report", help="Report title")
    p.add_argument("--report-include-json-link", type=str, default=None, help="Add link to full JSON in report")
    # 7.5.9: CI badge flags
    p.add_argument("--ci-badges", action="store_true", help="Add CI badges to report")
    p.add_argument("--ci-badges-out", type=str, default=None, help="Write CI badges to separate file")
    p.add_argument("--ci-badges-prefix", type=str, default=None, help="Prefix for badge keys")
    p.add_argument("--ci-badges-compact", action="store_true", help="Only include gates badge")
    p.add_argument("--ci-badges-split-out", type=str, default=None, help="Split badges into separate files in directory")
    # 7.5.10: Artifacts layout flags
    p.add_argument("--out-dir", type=str, default=None, help="Base directory for all output files")
    # 7.5.11: Publish index flags
    p.add_argument("--publish-index", action="store_true", help="Generate publish index")
    p.add_argument("--publish-index-out", type=str, default=None, help="Publish index JSON output path")
    p.add_argument("--publish-index-html-out", type=str, default=None, help="Publish index HTML output path")
    p.add_argument("--publish-index-base-url", type=str, default=None, help="Base URL for absolute links in HTML")
    # 7.5.12: Comparison flags
    p.add_argument("--compare-ci-summary", type=str, default=None, help="Compare with previous CI summary JSON")
    p.add_argument("--compare-report-json", type=str, default=None, help="Compare with previous report JSON")
    p.add_argument("--compare-emit", action="store_true", help="Emit comparison in output JSON")
    # 7.5.12: Regression gate flags
    p.add_argument("--fail-on-regression", action="store_true", help="Fail if regression detected")
    p.add_argument("--max-regress-ranker-mrr", type=float, default=None, help="Maximum allowed MRR regression")
    p.add_argument("--max-regress-ranker-top1", type=float, default=None, help="Maximum allowed Top1 regression")
    p.add_argument("--max-regress-chooser-flat-rate", type=float, default=None, help="Maximum allowed flat rate increase")
    # 7.5.13: Delta badges flags
    p.add_argument("--ci-badges-delta", action="store_true", help="Generate delta comparison badges")
    p.add_argument("--ci-badges-delta-compact", action="store_true", help="Generate only regression badge")
    # 7.5.14: Baseline store flags
    p.add_argument("--baseline-store", type=str, default=None, help="Directory where baseline files are stored")
    p.add_argument("--baseline-name", type=str, default=None, help="Baseline name (e.g., main, dev, prod)")
    p.add_argument("--baseline-save", action="store_true", help="Save current CI summary as baseline")
    p.add_argument("--baseline-save-if-ok", action="store_true", help="Save baseline only if final status is OK")
    p.add_argument("--compare-baseline", action="store_true", help="Compare with baseline from store")
    # 7.5.15: Scoped baseline flags
    p.add_argument("--baseline-scope", action="append", choices=["all", "by_pipeline", "trend_day", "window"], 
                   help="Baseline scope type (can be specified multiple times)")
    p.add_argument("--baseline-pipeline", choices=["baseline", "ranker", "chooser", "hybrid"], 
                   help="Pipeline name for by_pipeline scope")
    # 7.5.18: Bundle flags
    p.add_argument("--bundle", action="store_true", help="Generate standard bundle of artifacts in --out-dir")
    p.add_argument("--bundle-no-split-badges", action="store_true", help="Disable split badges in bundle mode")
    p.add_argument("--bundle-title", type=str, default=None, help="Report title for bundle mode")

def _resolve_output_path(args, path: str) -> str:
    """Resolve output path with --out-dir prefix"""
    if args.out_dir and not os.path.isabs(path):
        # Normalize path to avoid duplication
        return os.path.normpath(os.path.join(args.out_dir, path))
    return path


def apply_bundle_defaults(args):
    """Apply bundle mode defaults to args"""
    # 7.5.18: Validate bundle requires out-dir
    if args.bundle and not args.out_dir:
        raise ValueError("--bundle requires --out-dir")
    
    if not args.bundle:
        return args
    
    # Apply defaults only if not explicitly set by user
    
    # CI summary
    if not args.ci_summary:
        args.ci_summary = True
    if not args.ci_summary_out:
        args.ci_summary_out = "ci_summary.json"
    
    # CI badges
    if not args.ci_badges:
        args.ci_badges = True
    if not args.ci_badges_out:
        args.ci_badges_out = "ci_badges.json"
    if not args.ci_badges_split_out and not args.bundle_no_split_badges:
        args.ci_badges_split_out = "badges"
    
    # Reports
    if not args.md_out:
        args.md_out = "report.md"
    if not args.html_out:
        args.html_out = "report.html"
    
    # Report title
    if args.bundle_title:
        args.report_title = args.bundle_title
    
    # Publish index
    if not args.publish_index:
        args.publish_index = True
    if not args.publish_index_out:
        args.publish_index_out = "index.json"
    if not args.publish_index_html_out:
        args.publish_index_html_out = "index.html"
    
    return args


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="agent.fashion.ml.dataset_report")
    ap.add_argument("--dataset", required=True, help="Path to runs.jsonl")
    ap.add_argument("--out", required=False, default=None, help="Output JSON path (optional)")
    ap.add_argument("--stdout", action="store_true", help="Print report JSON to stdout")
    _add_ci_flags(ap)
    args = ap.parse_args(argv)
    
    # 7.5.18: Apply bundle defaults
    try:
        args = apply_bundle_defaults(args)
    except ValueError as e:
        ap.error(str(e))
    
    # 7.5.11: Validate publish index requires out-dir
    if args.publish_index and not args.out_dir:
        ap.error("--publish-index requires --out-dir to be specified")
    
    # 7.5.12: Validate comparison flags
    if args.compare_ci_summary and args.compare_report_json:
        ap.error("Cannot specify both --compare-ci-summary and --compare-report-json")
    
    if (args.fail_on_regression or args.max_regress_ranker_mrr is not None or 
        args.max_regress_ranker_top1 is not None or args.max_regress_chooser_flat_rate is not None):
        if not args.compare_ci_summary and not args.compare_report_json and not args.compare_baseline:
            ap.error("Regression gates require comparison (--compare-ci-summary, --compare-report-json, or --compare-baseline)")
    
    # 7.5.14: Validate baseline store flags
    if args.compare_baseline:
        if not args.baseline_store:
            ap.error("--compare-baseline requires --baseline-store")
        if not args.baseline_name:
            ap.error("--compare-baseline requires --baseline-name")
        if args.compare_ci_summary or args.compare_report_json:
            ap.error("--compare-baseline cannot be used with --compare-ci-summary or --compare-report-json")
    
    if args.baseline_save or args.baseline_save_if_ok:
        if not args.baseline_store:
            ap.error("--baseline-save/--baseline-save-if-ok requires --baseline-store")
        if not args.baseline_name:
            ap.error("--baseline-save/--baseline-save-if-ok requires --baseline-name")
        if args.baseline_save and args.baseline_save_if_ok:
            ap.error("Cannot specify both --baseline-save and --baseline-save-if-ok")
    
    # 7.5.15: Validate scoped baseline flags
    if args.baseline_pipeline and not args.baseline_scope:
        ap.error("--baseline-pipeline requires --baseline-scope by_pipeline")
    
    if args.baseline_scope:
        if "by_pipeline" in args.baseline_scope and not args.baseline_pipeline:
            ap.error("--baseline-scope by_pipeline requires --baseline-pipeline")
        if "trend_day" in args.baseline_scope and not args.trend_day:
            ap.error("--baseline-scope trend_day requires --trend-day")
    
    runs = _read_jsonl(args.dataset)
    
    # 7.5.2: Window slicing
    if args.last_n is not None:
        # Сортируем по ts_utc если есть, иначе оставляем как есть
        def get_ts(run):
            return run.get("ts_utc", "")
        
        runs.sort(key=get_ts)
        original_len = len(runs)
        runs = runs[-args.last_n:]
        window_info = {
            "mode": "last_n",
            "last_n": args.last_n,
            "used_runs": len(runs)
        }
    else:
        window_info = {
            "mode": "all",
            "last_n": None,
            "used_runs": len(runs)
        }
    
    # 7.5.3: Trend report
    if args.trend_day:
        # Для trend report используем все runs (window slicing уже применен выше)
        trend_report = build_trend_report(runs, args.trend_last_days, args.trend_by_pipeline)
        
        # Если это только trend report (без by-pipeline)
        if not args.by_pipeline:
            report = {
                "ok": True,
                "runs": len(runs),
                "window": window_info,
                "trend": trend_report
            }
        # Если combined с by-pipeline, trend будет добавлен ниже
    
    # 7.5.2: Pipeline breakdown
    if args.by_pipeline:
        # Считаем общий отчет
        report = build_report_for_runs(runs)
        
        # Добавляем window информацию
        report["window"] = window_info
        
        # Если есть trend report, добавляем его
        if args.trend_day and 'trend_report' in locals():
            report["trend"] = trend_report
        
        # Группируем по pipeline и считаем breakdown
        pipeline_groups = {}
        for run in runs:
            pipeline = detect_pipeline(run)
            pipeline_groups.setdefault(pipeline, []).append(run)
        
        pipelines_breakdown = {}
        for pipeline, pipeline_runs in pipeline_groups.items():
            pipelines_breakdown[pipeline] = build_report_for_runs(pipeline_runs)
        
        report["pipelines_breakdown"] = pipelines_breakdown
    elif not args.trend_day:
        # Обычный отчет (используем старую функцию для совместимости)
        report = build_dataset_report(runs)
        report["window"] = window_info

    # --- NEW: scoped gates ---
    cfg = GateConfig(
        min_runs=int(args.min_runs),
        min_ranker_mrr=float(args.min_ranker_mrr),
        min_ranker_top1=float(args.min_ranker_top1),
        max_chooser_flat_rate=(None if args.max_chooser_flat_rate is None else float(args.max_chooser_flat_rate)),
        fail_on_warn=bool(args.fail_on_warn),
    )
    
    # Determine scopes based on flags
    if args.check_scope:
        scopes = args.check_scope
    elif args.check or args.check_by_pipeline or args.check_trend_day:
        # Backward compatibility
        scopes = []
        if args.check:
            scopes.append("all")
        if args.check_by_pipeline:
            scopes.append("by_pipeline")
        if args.check_trend_day:
            scopes.append("trend_day")
    else:
        scopes = []
    
    # Apply scoped gates
    check_results = {}
    final_gates_ok = True
    
    for scope in scopes:
        if scope == "all":
            gates_info = apply_gates_to_report(report, cfg)
            check_results["all"] = gates_info
            final_gates_ok = final_gates_ok and gates_info["ok"]
            report["gates"] = gates_info  # backward compatibility
            
        elif scope == "window":
            # Window gates use the main report (already windowed)
            gates_info = apply_gates_to_report(report, cfg)
            check_results["window"] = gates_info
            final_gates_ok = final_gates_ok and gates_info["ok"]
            report["window_gates"] = gates_info
            
        elif scope == "trend_day" and "trend" in report:
            trend_gates = apply_trend_day_gates(report["trend"], cfg)
            check_results["trend_day"] = trend_gates
            final_gates_ok = final_gates_ok and trend_gates["ok"]
            report["trend_day_gates"] = trend_gates  # backward compatibility
            
        elif scope == "by_pipeline" and "pipelines_breakdown" in report:
            pipeline_gates = apply_pipeline_gates(report["pipelines_breakdown"], cfg)
            check_results["by_pipeline"] = pipeline_gates
            final_gates_ok = final_gates_ok and pipeline_gates["overall_ok"]
            report["gates_by_pipeline"] = pipeline_gates  # backward compatibility
    
    # Add scoped results if multiple scopes
    if len(scopes) > 1:
        report["checks"] = {
            "mode": args.check_mode,
            "scopes": scopes,
            "results": check_results,
            "overall_ok": final_gates_ok if args.check_mode == "and" else any(r["ok"] for r in check_results.values())
        }
        
        # Recalculate final result based on mode
        if args.check_mode == "or":
            final_gates_ok = any(r["ok"] for r in check_results.values())
    
    # Backward compatibility: add missing gates if not in scopes
    if "gates" not in report and scopes:
        report["gates"] = check_results.get(scopes[0], {"ok": True, "violations": []})

    # 7.5.7: CI summary
    exit_code = EXIT_OK if final_gates_ok else EXIT_GATE_FAIL
    if args.check or args.check_by_pipeline or args.check_trend_day or args.check_scope:
        exit_code = EXIT_OK if final_gates_ok else EXIT_GATE_FAIL
    else:
        exit_code = EXIT_OK
    
    # Build CI summary if requested
    if args.ci_summary:
        check_context = {
            "scopes": scopes,
            "check_mode": args.check_mode if scopes else None,
        }
        ci_summary = build_ci_summary(report, exit_code, check_context)
        report["ci_summary"] = ci_summary
        
        # Write separate file if requested
        if args.ci_summary_out:
            ci_summary_path = _resolve_output_path(args, args.ci_summary_out)
            import os
            os.makedirs(os.path.dirname(ci_summary_path), exist_ok=True)
            with open(ci_summary_path, "w", encoding="utf-8") as f:
                json.dump(ci_summary, f, indent=2, ensure_ascii=False)

    # 7.5.9: CI badges
    if args.ci_badges or args.ci_badges_out:
        from agent.fashion.ml.ci_badge import build_badges, write_text
        import os
        
        # Build badges
        badges = build_badges(report, title=args.ci_badges_prefix)
        
        # Apply compact mode if requested
        if args.ci_badges_compact:
            prefix = f"{args.ci_badges_prefix}_" if args.ci_badges_prefix else ""
            gates_key = f"{prefix}gates"
            badges = {gates_key: badges[gates_key]} if gates_key in badges else {}
        
        # Add to report if requested
        if args.ci_badges:
            report["ci_badges"] = badges
        
        # Write separate file if requested
        if args.ci_badges_out:
            badges_path = _resolve_output_path(args, args.ci_badges_out)
            os.makedirs(os.path.dirname(badges_path), exist_ok=True)
            with open(badges_path, "w", encoding="utf-8") as f:
                json.dump(badges, f, indent=2, ensure_ascii=False)
        
        # Write split badges if requested
        if args.ci_badges_split_out:
            split_dir = _resolve_output_path(args, args.ci_badges_split_out)
            os.makedirs(split_dir, exist_ok=True)
            
            for badge_name, badge_content in badges.items():
                badge_file = os.path.join(split_dir, f"{badge_name}.json")
                with open(badge_file, "w", encoding="utf-8") as f:
                    json.dump(badge_content, f, indent=2, ensure_ascii=False)

    # 7.5.15: Scoped baseline comparison
    scoped_regression_failed = False
    scoped_regression_gates = {}
    scoped_comparisons = {}
    comparison = None
    regression_failed = False
    regression_gates = None
    
    if args.compare_baseline and args.baseline_scope:
        from agent.fashion.ml.compare import (
            extract_compact_metrics, extract_compact_metrics_from_ci_summary,
            build_comparison, apply_regression_gates, ComparisonConfig
        )
        from agent.fashion.ml.baseline_store import resolve_baseline_path, load_baseline, make_scope_key
        
        for scope in args.baseline_scope:
            if scope == "by_pipeline" and args.baseline_pipeline:
                # Get current pipeline data
                if not args.by_pipeline:
                    ap.error("--baseline-scope by_pipeline requires --by-pipeline to be enabled")
                
                pipeline_name = args.baseline_pipeline
                if pipeline_name not in report.get("pipelines_breakdown", {}):
                    ap.error(f"Pipeline '{pipeline_name}' not found in report. Available: {list(report.get('pipelines_breakdown', {}).keys())}")
                
                # Extract compact metrics from pipeline data
                pipeline_report = report["pipelines_breakdown"][pipeline_name]
                current_compact = extract_compact_metrics(pipeline_report)
                
                # Load scoped baseline
                scope_params = {}
                baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, pipeline_name, scope_params)
                baseline = load_baseline(baseline_path)
                baseline_compact = extract_compact_metrics_from_ci_summary(baseline)
                
                source_info = {
                    "kind": "baseline_store",
                    "path": baseline_path,
                    "name": args.baseline_name,
                    "scope": scope,
                    "pipeline": pipeline_name
                }
                
                # Build comparison
                comparison = build_comparison(current_compact, baseline_compact, source_info)
                scoped_comparisons[f"{scope}:{pipeline_name}"] = comparison
                
                # Apply regression gates if configured
                regression_config = ComparisonConfig(
                    fail_on_regression=args.fail_on_regression,
                    max_regress_ranker_mrr=args.max_regress_ranker_mrr,
                    max_regress_ranker_top1=args.max_regress_ranker_top1,
                    max_regress_chooser_flat_rate=args.max_regress_chooser_flat_rate
                )
                
                scope_regression_failed, scope_regression_gates = apply_regression_gates(comparison, regression_config)
                scoped_regression_gates[f"{scope}:{pipeline_name}"] = scope_regression_gates
                
                if scope_regression_failed:
                    scoped_regression_failed = True
                    
            elif scope == "trend_day":
                # Get current trend day data
                if not args.trend_day:
                    ap.error("--baseline-scope trend_day requires --trend-day to be enabled")
                
                trend_data = report.get("trend", {})
                days = trend_data.get("days", [])
                if not days:
                    ap.error("No trend days available for comparison")
                
                # Use the last day
                current_day = days[-1]
                current_compact = extract_compact_metrics(current_day)
                
                # Load scoped baseline
                day_key = current_day.get("day", "unknown")
                scope_params = {"day": day_key}
                baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, None, scope_params)
                baseline = load_baseline(baseline_path)
                baseline_compact = extract_compact_metrics_from_ci_summary(baseline)
                
                source_info = {
                    "kind": "baseline_store",
                    "path": baseline_path,
                    "name": args.baseline_name,
                    "scope": scope,
                    "day": day_key
                }
                
                # Build comparison
                comparison = build_comparison(current_compact, baseline_compact, source_info)
                scoped_comparisons[f"{scope}:{day_key}"] = comparison
                
                # Apply regression gates if configured
                regression_config = ComparisonConfig(
                    fail_on_regression=args.fail_on_regression,
                    max_regress_ranker_mrr=args.max_regress_ranker_mrr,
                    max_regress_ranker_top1=args.max_regress_ranker_top1,
                    max_regress_chooser_flat_rate=args.max_regress_chooser_flat_rate
                )
                
                scope_regression_failed, scope_regression_gates = apply_regression_gates(comparison, regression_config)
                scoped_regression_gates[f"{scope}:{day_key}"] = scope_regression_gates
                
                if scope_regression_failed:
                    scoped_regression_failed = True
                    
            elif scope == "window":
                # Get current window data (entire report)
                current_compact = extract_compact_metrics(report)
                
                # Load scoped baseline
                scope_params = {}
                if args.last_n is not None:
                    scope_params["last_n"] = args.last_n
                
                baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, None, scope_params)
                baseline = load_baseline(baseline_path)
                baseline_compact = extract_compact_metrics_from_ci_summary(baseline)
                
                # Determine the window key for display
                if args.last_n is not None:
                    window_key = f"last_n_{args.last_n}"
                else:
                    window_key = "all"
                
                source_info = {
                    "kind": "baseline_store",
                    "path": baseline_path,
                    "name": args.baseline_name,
                    "scope": scope,
                    "window": window_key
                }
                
                # Build comparison
                comparison = build_comparison(current_compact, baseline_compact, source_info)
                scoped_comparisons[f"{scope}:{window_key}"] = comparison
                
                # Apply regression gates if configured
                regression_config = ComparisonConfig(
                    fail_on_regression=args.fail_on_regression,
                    max_regress_ranker_mrr=args.max_regress_ranker_mrr,
                    max_regress_ranker_top1=args.max_regress_ranker_top1,
                    max_regress_chooser_flat_rate=args.max_regress_chooser_flat_rate
                )
                
                scope_regression_failed, scope_regression_gates = apply_regression_gates(comparison, regression_config)
                scoped_regression_gates[f"{scope}:{window_key}"] = scope_regression_gates
                
                if scope_regression_failed:
                    scoped_regression_failed = True
        
        # Add scoped comparisons to report
        if scoped_comparisons:
            report["comparison_scoped"] = scoped_comparisons
        
        # Add scoped regression gates to report
        if scoped_regression_gates:
            report["regression_gates_scoped"] = scoped_regression_gates
    elif args.compare_baseline or args.compare_ci_summary or args.compare_report_json:
        # Regular baseline comparison (only if not scoped)
        from agent.fashion.ml.compare import (
            load_baseline_from_ci_summary, load_baseline_from_report_json,
            extract_compact_metrics, extract_compact_metrics_from_ci_summary,
            extract_compact_metrics_from_report, build_comparison, apply_regression_gates,
            ComparisonConfig
        )
        
        # Extract current compact metrics
        current_compact = extract_compact_metrics(report)
        
        # Load baseline
        if args.compare_ci_summary:
            baseline = load_baseline_from_ci_summary(args.compare_ci_summary)
            baseline_compact = extract_compact_metrics_from_ci_summary(baseline)
            source_info = {
                "kind": "ci_summary",
                "path": args.compare_ci_summary
            }
        elif args.compare_report_json:
            baseline = load_baseline_from_report_json(args.compare_report_json)
            baseline_compact = extract_compact_metrics_from_report(baseline)
            source_info = {
                "kind": "report_json",
                "path": args.compare_report_json
            }
        elif args.compare_baseline:
            from agent.fashion.ml.baseline_store import resolve_baseline_path, load_baseline
            baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name)
            baseline = load_baseline(baseline_path)
            baseline_compact = extract_compact_metrics_from_ci_summary(baseline)
            source_info = {
                "kind": "baseline_store",
                "path": baseline_path,
                "name": args.baseline_name
            }
        
        # Build comparison
        comparison = build_comparison(current_compact, baseline_compact, source_info)
        
        # Apply regression gates if configured
        regression_config = ComparisonConfig(
            fail_on_regression=args.fail_on_regression,
            max_regress_ranker_mrr=args.max_regress_ranker_mrr,
            max_regress_ranker_top1=args.max_regress_ranker_top1,
            max_regress_chooser_flat_rate=args.max_regress_chooser_flat_rate
        )
        
        regression_failed, regression_gates = apply_regression_gates(comparison, regression_config)
        
        # Add comparison to report if emit is enabled or if any comparison flag is used
        if args.compare_emit or args.compare_ci_summary or args.compare_report_json or args.compare_baseline:
            report["comparison"] = comparison
        
        # Add regression gates to report if any were applied
        if regression_gates:
            report["regression_gates"] = regression_gates
        
        # 7.5.13: Delta badges (after comparison is built)
        if args.ci_badges_delta or args.ci_badges_delta_compact:
            from agent.fashion.ml.ci_badge import build_delta_badges, write_text
            import os
            
            # Build delta badges
            delta_badges = build_delta_badges(report, title=args.ci_badges_prefix, compact=args.ci_badges_delta_compact)
            
            # Add to report if requested (only if comparison exists)
            if args.ci_badges_delta and delta_badges:
                report["ci_badges_delta"] = delta_badges
            
            # Write split badges if requested
            if args.ci_badges_split_out and delta_badges:
                split_dir = _resolve_output_path(args, args.ci_badges_split_out)
                os.makedirs(split_dir, exist_ok=True)
                
                for badge_name, badge_content in delta_badges.items():
                    badge_file = os.path.join(split_dir, f"{badge_name}.json")
                    with open(badge_file, "w", encoding="utf-8") as f:
                        json.dump(badge_content, f, indent=2, ensure_ascii=False)

    # 7.5.8: Human-readable reports (moved after comparison)
    if args.md_out or args.html_out:
        from agent.fashion.ml.report_render import render_markdown, render_html
        import os
        
        # Prepare JSON link for report
        json_link = args.report_include_json_link
        if not json_link and args.out:
            json_link = args.out
        
        # Generate Markdown
        if args.md_out:
            md_path = _resolve_output_path(args, args.md_out)
            markdown_content = render_markdown(report, args.report_title, json_link)
            os.makedirs(os.path.dirname(md_path), exist_ok=True)
            with open(md_path, "w", encoding="utf-8-sig") as f:
                f.write(markdown_content)
        
        # Generate HTML
        if args.html_out:
            html_path = _resolve_output_path(args, args.html_out)
            html_content = render_html(report, args.report_title, json_link)
            os.makedirs(os.path.dirname(html_path), exist_ok=True)
            with open(html_path, "w", encoding="utf-8-sig") as f:
                f.write(html_content)

    payload = json.dumps(report, indent=2 if not args.stdout else None, ensure_ascii=False)
    if args.stdout or not args.out:
        sys.stdout.write(payload + ("\n" if args.stdout else "\n"))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload + "\n")

    # 7.5.11: Publish index (generate after all other files)
    if args.publish_index:
        from agent.fashion.ml.publish_index import build_publish_index, render_index_html, write_text
        
        # Get data for index
        ci_summary = report.get("ci_summary")
        badges = report.get("ci_badges")
        
        # Build index
        index = build_publish_index(args.out_dir, report, ci_summary, badges)
        
        # Write JSON index
        index_json_path = _resolve_output_path(args, args.publish_index_out or "index.json")
        write_text(index_json_path, json.dumps(index, indent=2, ensure_ascii=False), is_json=True)
        
        # Write HTML index if requested
        if args.publish_index_html_out or True:  # Default to generating HTML
            index_html_path = _resolve_output_path(args, args.publish_index_html_out or "index.html")
            html_content = render_index_html(index, title="ML Report Index", base_url=args.publish_index_base_url)
            write_text(index_html_path, html_content)

    # 7.5.14: Baseline save logic (after all processing but before exit)
    if args.baseline_save or args.baseline_save_if_ok:
        from agent.fashion.ml.baseline_store import resolve_baseline_path, save_baseline
        
        # Check if we should save (only if OK for --baseline-save-if-ok)
        should_save = args.baseline_save  # Always save for --baseline-save
        if args.baseline_save_if_ok:
            # Calculate final exit code to determine if we should save
            if args.check or args.check_by_pipeline or args.check_trend_day or args.check_scope:
                final_exit_code = exit_code
                if regression_failed or scoped_regression_failed:
                    final_exit_code = EXIT_GATE_FAIL
                should_save = (final_exit_code == EXIT_OK)
            elif regression_failed or scoped_regression_failed:
                should_save = False
            else:
                should_save = (exit_code == EXIT_OK)
        
        if should_save:
            ci_summary = report.get("ci_summary")
            if ci_summary:
                if args.baseline_scope:
                    # Save scoped baselines
                    from agent.fashion.ml.baseline_store import resolve_baseline_path, save_baseline, make_scope_key
                    
                    for scope in args.baseline_scope:
                        if scope == "by_pipeline" and args.baseline_pipeline:
                            # Create scoped CI summary from pipeline data
                            pipeline_name = args.baseline_pipeline
                            if pipeline_name in report.get("pipelines_breakdown", {}):
                                pipeline_report = report["pipelines_breakdown"][pipeline_name]
                                # Build CI summary from pipeline data
                                scoped_ci_summary = {
                                    "ok": ci_summary.get("ok", True),
                                    "exit_code": ci_summary.get("exit_code", 0),
                                    "scope_mode": "by_pipeline",
                                    "scopes": [f"by_pipeline:{pipeline_name}"],
                                    "runs_used": pipeline_report.get("runs", 0),
                                    "ranker": pipeline_report.get("ranker", {}),
                                    "chooser": pipeline_report.get("chooser", {}),
                                    "gates": {"overall_ok": True, "fails": 0, "warns": 0, "violations": []}
                                }
                                
                                scope_params = {}
                                baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, pipeline_name, scope_params)
                                save_baseline(scoped_ci_summary, baseline_path)
                                
                        elif scope == "trend_day":
                            # Create scoped CI summary from trend day data
                            trend_data = report.get("trend", {})
                            days = trend_data.get("days", [])
                            if days:
                                current_day = days[-1]
                                day_key = current_day.get("day", "unknown")
                                # Build CI summary from trend day data
                                scoped_ci_summary = {
                                    "ok": ci_summary.get("ok", True),
                                    "exit_code": ci_summary.get("exit_code", 0),
                                    "scope_mode": "trend_day",
                                    "scopes": [f"trend_day:{day_key}"],
                                    "runs_used": current_day.get("runs", 0),
                                    "ranker": current_day.get("ranker", {}),
                                    "chooser": current_day.get("chooser", {}),
                                    "gates": {"overall_ok": True, "fails": 0, "warns": 0, "violations": []}
                                }
                                
                                scope_params = {"day": day_key}
                                baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, None, scope_params)
                                save_baseline(scoped_ci_summary, baseline_path)
                                
                        elif scope == "window":
                            # Create scoped CI summary from window data (entire report)
                            scope_params = {}
                            if args.last_n is not None:
                                scope_params["last_n"] = args.last_n
                            
                            # Build CI summary from window data
                            window_key = scope_params.get('last_n', 'all')
                            if window_key != 'all':
                                window_key = f"last_n_{window_key}"
                            
                            scoped_ci_summary = {
                                "ok": ci_summary.get("ok", True),
                                "exit_code": ci_summary.get("exit_code", 0),
                                "scope_mode": "window",
                                "scopes": [f"window:{window_key}"],
                                "runs_used": ci_summary.get("runs_used", 0),
                                "ranker": ci_summary.get("ranker", {}),
                                "chooser": ci_summary.get("chooser", {}),
                                "gates": ci_summary.get("gates", {})
                            }
                            
                            baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name, scope, None, scope_params)
                            save_baseline(scoped_ci_summary, baseline_path)
                else:
                    # Save regular baseline
                    baseline_path = resolve_baseline_path(args.baseline_store, args.baseline_name)
                    save_baseline(ci_summary, baseline_path)
                # Note: We don't add baseline info to the main report to keep it clean

    # 7.5.12: Update exit code to include regression failures
    if args.check or args.check_by_pipeline or args.check_trend_day or args.check_scope:
        # Combine gates failure and regression failure
        final_exit_code = exit_code
        if regression_failed or scoped_regression_failed:
            final_exit_code = EXIT_GATE_FAIL
        return final_exit_code
    elif regression_failed or scoped_regression_failed:
        return EXIT_GATE_FAIL
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
