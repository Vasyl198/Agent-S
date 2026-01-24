# agent/fashion/cli/optimize.py
# CLI команда для оптимизации PatternModel

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _utc_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _safe_write_json(path: Path, data: Dict[str, Any], *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2 if pretty else None), encoding="utf-8")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m agent.fashion.cli optimize",
        description="Optimize PatternModel for a given TargetSpec and produce OptimizationReport JSON."
    )

    p.add_argument("--goal", required=True, help="Target goal, e.g. reduce_seam_allowance / increase_seam_allowance / reduce_notches / increase_notches / grading_shift ...")
    p.add_argument("--role", required=True, help="Semantic role for the target, e.g. HEM, WAIST, WAIST_CENTER, etc.")
    p.add_argument("--by", required=True, type=float, help="Magnitude for the target (mm or count depending on goal).")

    # Common knobs
    p.add_argument("--seed", type=int, default=0, help="Deterministic seed (affects candidate generation).")
    p.add_argument("--candidate-count", type=int, default=5, help="How many candidates to evaluate per step.")
    p.add_argument("--max-steps", type=int, default=1, help="How many optimization steps to run (1 = single step).")

    # 6.5.0.4: stdout JSON mode (for pipes/tests)
    p.add_argument(
        "--stdout",
        action="store_true",
        help="Print OptimizationReport JSON to stdout (no extra text).",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (indent=2).",
    )

    # 6.5.0.6: quiet and warnings control
    p.add_argument(
        "--quiet",
        action="store_true",
        help="No logs or warnings. stderr must be empty. Suitable for CI."
    )
    p.add_argument(
        "--warnings",
        choices=["off", "default", "strict"],
        default="default",
        help="Warnings policy: off=ignore, default=python default, strict=warnings as errors."
    )

    # 6.5.0.7: strict and CI mode
    p.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: non-zero exit on constraint violations and no improvement."
    )
    p.add_argument(
        "--ci",
        action="store_true",
        help="CI profile: implies strict checks (and may default to --stdout)."
    )

    # 6.6.0: dataset logging
    p.add_argument(
        "--dataset-dir", 
        default=None, 
        help="Write dataset samples to this directory (jsonl/json)."
    )
    p.add_argument(
        "--dataset-format", 
        choices=["jsonl", "json"], 
        default="jsonl"
    )
    p.add_argument(
        "--dataset-write-mode", 
        choices=["append", "overwrite"], 
        default="append"
    )

    # 7.1.0: ML ranker integration
    p.add_argument(
        "--ranker-model",
        help="Path to trained ML ranker model (.joblib)"
    )
    p.add_argument(
        "--ranker-top-k",
        type=int,
        default=5,
        help="Evaluate only top-K candidates with ranker (default: 5)"
    )
    p.add_argument(
        "--ranker-fallback",
        choices=["none", "baseline"],
        default="baseline",
        help="Fallback if ranker model fails to load (none|baseline)"
    )
    p.add_argument(
        "--ranker-only",
        action="store_true",
        help="Use ranker scores only, skip real evaluation (evaluated_count=0)"
    )
    p.add_argument(
        "--chooser-model",
        type=str,
        help="Path to chooser model for candidate selection"
    )
    p.add_argument(
        "--chooser-top-k",
        type=int,
        default=5,
        help="Number of top candidates to evaluate when using chooser (default: 5)"
    )
    p.add_argument(
        "--chooser-only",
        action="store_true",
        help="Use chooser probabilities only, skip real evaluation (evaluated_count=0)"
    )
    p.add_argument(
        "--chooser-temperature",
        type=float,
        default=1.0,
        help="Temperature for chooser probability scaling (default: 1.0)"
    )
    p.add_argument(
        "--hybrid",
        action="store_true",
        help="Enable hybrid policy: chooser filters, then ranker ranks top-M, then top-K evaluated"
    )
    p.add_argument(
        "--chooser-top-m",
        type=int,
        default=10,
        help="Number of top candidates to pass to ranker in hybrid mode (default: 10)"
    )
    p.add_argument(
        "--hybrid-top-k",
        type=int,
        default=None,
        help="Final number of candidates to evaluate in hybrid mode (default: ranker_top_k or 5)"
    )

    # Input sources (mutually exclusive)
    input_group = p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--use-demo-model", action="store_true", help="Use a small demo PatternModel (for smoke tests).")
    input_group.add_argument("--in-intent", type=Path, help="Path to pattern_intent.json file with meta/dimensions/grading/manufacturing.")

    # Output
    p.add_argument("--out-dir", default="output/reports", help="Directory for OptimizationReport JSON output.")
    p.add_argument("--out", type=Path, help="Exact output path for OptimizationReport JSON (overrides --out-dir timestamp naming).")

    return p.parse_args(argv)


def _make_target_spec(goal: str, role: str, by: float):
    """
    Создаем TargetSpec строго через TargetLibrary фабрики.
    Не допускаем ручных path.
    """
    from agent.fashion.analysis.targets.library import TargetLibrary
    from agent.fashion.cli.exit_codes import ExitCode, ExitDecision

    # Нормализуем goal → фабрика
    # Подстрой под реальные имена goals в твоем TARGET_PATH_MAPPINGS.
    # Ниже — самый частый набор, остальное можно расширять.
    if goal == "reduce_seam_allowance":
        return TargetLibrary.create_seam_allowance_target(role=role, by=float(by), increase=False)
    if goal == "increase_seam_allowance":
        return TargetLibrary.create_seam_allowance_target(role=role, by=float(by), increase=True)
    if goal == "reduce_notches":
        return TargetLibrary.create_notches_target(role=role, by=int(by), increase=False)
    if goal == "increase_notches":
        return TargetLibrary.create_notches_target(role=role, by=int(by), increase=True)

    # Пример для grading (если у тебя есть фабрика)
    # if goal == "shift_grading":
    #     return TargetLibrary.create_grading_target(role=role, by=float(by), increase=True/False)

    # Если goal неизвестен — возвращаем специальный exit code
    raise ExitDecision(ExitCode.INVALID_TARGET, f"Unknown --goal '{goal}'. Supported goals: reduce_seam_allowance, increase_seam_allowance, reduce_notches, increase_notches")


def build_pattern_model_from_intent(intent_data: Dict[str, Any]):
    """
    Создать PatternModel из intent данных (Путь 2: demo contour + intent поверх).
    
    Args:
        intent_data: нормализованные данные из pattern_intent.json
        
    Returns:
        PatternModel с demo contour + intent meta/grading/manufacturing
    """
    # CAD Core (единый источник геометрии)
    from agent.fashion.cad.core.geometry import Point, Segment
    from agent.fashion.pattern.metadata import PatternMeta
    from agent.fashion.pattern.model import PatternModel
    from agent.fashion.pattern.semantics import PatternSemantics

    # Создаем простой demo contour (как в build_simple_demo_model)
    pts = [
        Point(0, 0, role="WAIST_CENTER"),
        Point(50, 2.5, role="WAIST_SIDE"),
        Point(100, 0, role="WAIST_SIDE"),
        Point(105, 100, role="HIP_SIDE"),
        Point(100, 300, role="HEM_SIDE"),
        Point(50, 305, role="HEM_CENTER"),
        Point(0, 300, role="HEM_CENTER"),
        Point(0, 100, role="CENTER_LINE"),
    ]

    segs = [
        Segment(pts[0], pts[1]),
        Segment(pts[1], pts[2]),
        Segment(pts[2], pts[3]),
        Segment(pts[3], pts[4]),
        Segment(pts[4], pts[5]),
        Segment(pts[5], pts[6]),
        Segment(pts[6], pts[7]),
        Segment(pts[7], pts[0]),
    ]

    # Создаем контур напрямую через CAD классы
    from agent.fashion.cad.core.contour import Contour
    contour = Contour(segments=segs, closed=True)

    # Валидные семантики (как в build_simple_demo_model)
    semantics = PatternSemantics(
        point_roles={
            0: "WAIST_CENTER",
            1: "WAIST_SIDE",
            2: "WAIST_SIDE",
            3: "HIP_SIDE",
            4: "HEM_SIDE",
            5: "HEM_CENTER",
            6: "HEM_CENTER",
            7: "CENTER_LINE",
        },
        segment_roles={
            0: "WAIST",
            1: "WAIST",
            2: "SIDE",
            3: "SIDE",
            4: "HEM",
            5: "HEM",
            6: "CENTER",
            7: "CENTER",
        },
        region_map={},
        invariants={},
    )

    # Meta из intent
    meta_dict = intent_data.get("meta", {})
    meta = PatternMeta(
        name=meta_dict.get("name", "Pattern from Intent"),
        size=meta_dict.get("size", "M"),
        version=meta_dict.get("version", "v1.0"),
        author=meta_dict.get("author", "intent-user")
    )

    # Создаем PatternManufacturing объект с defaults
    from agent.fashion.pattern.manufacturing import PatternManufacturing
    from agent.fashion.pattern.grading import PatternGrading
    manufacturing_data = intent_data.get("manufacturing", {})
    manufacturing = PatternManufacturing(
        seam_allowances=manufacturing_data.get("seam_allowances", {
            "WAIST": 10.0,
            "SIDE": 10.0, 
            "HEM": 15.0
        }),
        notches=manufacturing_data.get("notches", {
            "WAIST": 2,
            "HEM": 1
        }),
        stitch_lines=manufacturing_data.get("stitch_lines", {}),
        grainline=manufacturing_data.get("grainline", "CENTER")
    )
    
    # Создаем PatternGrading объект с defaults
    grading_data = intent_data.get("grading", {})
    grading = PatternGrading(
        size_from=grading_data.get("size_from", "M"),
        size_to=grading_data.get("size_to", "L"),
        point_rules=grading_data.get("point_rules", {
            "WAIST_SIDE": (5.0, 2.5),
            "HIP_SIDE": (5.0, 5.0),
            "HEM_SIDE": (5.0, 0.0)
        })
    )
    
    # Создаем PatternModel напрямую, минуя валидацию
    model = object.__new__(PatternModel)
    object.__setattr__(model, 'meta', meta)
    object.__setattr__(model, 'contour', contour)
    object.__setattr__(model, 'semantics', semantics)
    object.__setattr__(model, 'grading', grading)
    object.__setattr__(model, 'manufacturing', None)  # Начинаем с None, как в demo
    object.__setattr__(model, 'derived_geometry', intent_data.get("derived", {}))
    
    return model


def build_simple_demo_model():
    """
    Минимальная демо-модель для smoke-теста CLI.
    НЕ для продакшена. В проде подставишь загрузку PatternModel из файла.
    """
    # CAD Core (единый источник геометрии)
    from agent.fashion.cad.core.geometry import Point, Segment
    from agent.fashion.pattern.metadata import PatternMeta
    from agent.fashion.pattern.model import PatternModel
    from agent.fashion.pattern.semantics import PatternSemantics

    # Создаем простой контур без валидации для demo
    pts = [
        Point(0, 0, role="WAIST_CENTER"),
        Point(50, 2.5, role="WAIST_SIDE"),
        Point(100, 0, role="WAIST_SIDE"),
        Point(105, 100, role="HIP_SIDE"),
        Point(100, 300, role="HEM_SIDE"),
        Point(50, 305, role="HEM_CENTER"),
        Point(0, 300, role="HEM_CENTER"),
        Point(0, 100, role="CENTER_LINE"),
    ]

    segs = [
        Segment(pts[0], pts[1]),
        Segment(pts[1], pts[2]),
        Segment(pts[2], pts[3]),
        Segment(pts[3], pts[4]),
        Segment(pts[4], pts[5]),
        Segment(pts[5], pts[6]),
        Segment(pts[6], pts[7]),
        Segment(pts[7], pts[0]),
    ]

    # Создаем контур напрямую через CAD классы
    from agent.fashion.cad.core.contour import Contour
    contour = Contour(segments=segs, closed=True)

    # Семантика — индексами (как у тебя в 3.1)
    semantics = PatternSemantics(
        point_roles={
            0: "WAIST_CENTER",
            1: "WAIST_SIDE",
            2: "WAIST_SIDE",
            3: "HIP_SIDE",
            4: "HEM_SIDE",
            5: "HEM_CENTER",
            6: "HEM_CENTER",
            7: "CENTER_LINE",
        },
        segment_roles={
            0: "WAIST",
            1: "WAIST",
            2: "SIDE",
            3: "SIDE",
            4: "HEM",
            5: "HEM",
            6: "CENTER",
            7: "CENTER",
        },
        region_map={},
        invariants={},
    )

    meta = PatternMeta(name="Skirt Front", size="M", version="v1.0", author="cli-demo")
    
    # Добавляем простое manufacturing для генерации кандидатов
    from agent.fashion.pattern.manufacturing import PatternManufacturing
    manufacturing = PatternManufacturing(
        seam_allowances={
            "WAIST": 15.0,
            "HEM": 20.0,
            "SIDE": 10.0
        },
        notches={},  # пустой dict
        stitch_lines=[],
        grainline="0"  # простая строка
    )
    
    # Создаем PatternModel напрямую, минуя валидацию
    model = object.__new__(PatternModel)
    object.__setattr__(model, 'meta', meta)
    object.__setattr__(model, 'contour', contour)
    object.__setattr__(model, 'semantics', semantics)
    object.__setattr__(model, 'grading', None)
    object.__setattr__(model, 'manufacturing', manufacturing)
    object.__setattr__(model, 'derived_geometry', None)
    
    return model


def _extract_candidates_from_optimization(optimizer, pattern_model, target, args):
    """
    Извлечь кандидатов из оптимизации для dataset logging.
    Временная функция - в идеале loop должен возвращать кандидатов.
    """
    candidates_data = []
    
    # Запускаем многошаговую оптимизацию с модификацией для извлечения кандидатов
    try:
        # Создаем временную версию оптимизатора для извлечения кандидатов
        from agent.fashion.analysis.optimizer.generator import CandidateGenerator
        from agent.fashion.analysis.optimizer.loop import OptimizationStepResult
        
        local_generator = CandidateGenerator(seed=int(args.seed))
        current_model = pattern_model
        baseline_score = optimizer._evaluate_model(pattern_model)
        
        # Делаем один шаг для извлечения кандидатов
        candidates = local_generator.generate_candidates(current_model, int(args.candidate_count))
        
        # Оцениваем каждого кандидата
        evaluated_candidates = []
        for proposal in candidates:
            try:
                new_model = optimizer._apply_proposal(current_model, proposal)
                constraint_result = optimizer._validate_constraints(new_model)
                
                if not constraint_result.ok:
                    continue  # пропускаем невалидных
                    
                score = optimizer._evaluate_model(new_model)
                improvement = score - baseline_score
                
                evaluated_candidates.append({
                    "score": score,
                    "improvement": improvement,
                    "proposal": proposal,
                    "constraint_ok": True
                })
            except Exception:
                continue
        
        # Находим лучшего для chosen_index
        if evaluated_candidates:
            best_idx = max(range(len(evaluated_candidates)), 
                          key=lambda i: evaluated_candidates[i]["score"])
            candidates_data = evaluated_candidates
        else:
            best_idx = -1
            
        return {
            "candidates": candidates_data,
            "chosen_index": best_idx
        }
        
    except Exception as e:
        logger.warning(f"Failed to extract candidates: {e}")
        return None


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    # 6.5.0.7: CI profile - применяем до runtime setup
    if getattr(args, "ci", False):
        args.strict = True
        # обычно в CI почти всегда нужен JSON:
        if not getattr(args, "stdout", False):
            args.stdout = True

    # 6.5.0.6: CLI runtime setup - обновляем с учетом --stdout
    from agent.fashion.cli.runtime import setup_cli_runtime
    setup_cli_runtime(
        quiet=getattr(args, "quiet", False),
        warnings_mode=getattr(args, "warnings", "default"),
        stdout_json=bool(getattr(args, "stdout", False)),
    )

    # 1) Создаем TargetSpec строго через TargetLibrary
    try:
        target = _make_target_spec(args.goal, args.role, args.by)
    except Exception as e:
        # Обработка ExitDecision и других ошибок
        from agent.fashion.cli.exit_codes import ExitDecision, ExitCode
        if isinstance(e, ExitDecision):
            return e.code
        return ExitCode.INVALID_TARGET

    # 2) Получаем PatternModel (demo или intent)
    try:
        if args.use_demo_model:
            pattern_model = build_simple_demo_model()
        elif args.in_intent:
            from .io_intent import load_intent
            intent_data = load_intent(args.in_intent)
            pattern_model = build_pattern_model_from_intent(intent_data)
        else:
            raise SystemExit(
                "No PatternModel source provided.\n"
                "Use --use-demo-model for smoke test, or --in-intent to load from pattern_intent.json.\n"
                "Planned in 6.5.0.2/6.5.0.3."
            )
    except (FileNotFoundError, ValueError) as e:
        from agent.fashion.cli.exit_codes import ExitCode
        return ExitCode.INVALID_INPUT
    except Exception as e:
        from agent.fashion.cli.exit_codes import ExitCode
        return ExitCode.INTERNAL_ERROR

    # 3) Запускаем оптимизацию
    from agent.fashion.analysis.optimizer.loop import OptimizationLoop

    # Конвертируем target в dict для передачи в loop
    target_dict = target.to_dict() if hasattr(target, 'to_dict') else target
    
    # 7.1.0: ranker параметры
    optimizer = OptimizationLoop(target=target_dict)

    # 7.4.0: валидация hybrid режима
    if getattr(args, 'hybrid', False) and not getattr(args, 'ranker_model', None):
        raise ValueError("--hybrid requires --ranker-model to be specified")

    # Если max_steps=1 — один шаг через run_steps для правильной генерации target-предложений
    run = None
    if int(args.max_steps) <= 1:
        # 7.1.0: используем run_steps даже для одного шага чтобы получить target-предложения
        run = optimizer.run_steps(
            pattern_model=pattern_model,
            target=target_dict,
            max_steps=int(args.max_steps),
            epsilon=float(getattr(args, 'epsilon', 0.01)),
            strict=args.strict,
            seed=int(args.seed),
            max_candidates_per_step=int(args.candidate_count),
            ranker_model=getattr(args, 'ranker_model', None),
            ranker_top_k=getattr(args, 'ranker_top_k', 5),
            ranker_fallback=getattr(args, 'ranker_fallback', 'baseline'),
            ranker_only=getattr(args, 'ranker_only', False),
            chooser_model=getattr(args, 'chooser_model', None),
            chooser_top_k=getattr(args, 'chooser_top_k', 5),
            chooser_only=getattr(args, 'chooser_only', False),
            chooser_temperature=float(getattr(args, 'chooser_temperature', 1.0)),
            # 7.4.0: hybrid параметры
            hybrid=getattr(args, 'hybrid', False),
            chooser_top_m=getattr(args, 'chooser_top_m', 10),
            hybrid_top_k=getattr(args, 'hybrid_top_k', None),
        )
        # 4) Строим report
        from agent.fashion.analysis.optimizer.report import OptimizationReportBuilder
        report = OptimizationReportBuilder.build_from_run(
            target=target,
            run_result=run,
            meta={"seed": int(args.seed), "candidate_count": int(args.candidate_count), "max_steps": int(args.max_steps)},
        )
    else:
        run = optimizer.run_steps(
            pattern_model=pattern_model,
            target=target_dict,
            max_steps=int(args.max_steps),
            max_candidates_per_step=int(args.candidate_count),
            seed=int(args.seed),
            ranker_model=getattr(args, 'ranker_model', None),
            ranker_top_k=getattr(args, 'ranker_top_k', 5),
            ranker_fallback=getattr(args, 'ranker_fallback', 'baseline'),
            ranker_only=getattr(args, 'ranker_only', False),
            chooser_model=getattr(args, 'chooser_model', None),
            chooser_top_k=getattr(args, 'chooser_top_k', 5),
            chooser_only=getattr(args, 'chooser_only', False),
            chooser_temperature=float(getattr(args, 'chooser_temperature', 1.0)),
            # 7.4.0: hybrid параметры
            hybrid=getattr(args, 'hybrid', False),
            chooser_top_m=getattr(args, 'chooser_top_m', 10),
            hybrid_top_k=getattr(args, 'hybrid_top_k', None),
        )
        from agent.fashion.analysis.optimizer.report import OptimizationReportBuilder
        report = OptimizationReportBuilder.build_from_run(
            target=target,
            run_result=run,
            meta={"seed": int(args.seed), "candidate_count": int(args.candidate_count), "max_steps": int(args.max_steps)},
        )

    # 5) Подготовка вывода
    # 6.5.0.6: функция для гарантированного вывода JSON
    def emit_report(report: dict, *, pretty: bool, stdout: bool) -> None:
        if pretty:
            text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        else:
            text = json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

        if stdout:
            sys.stdout.write(text)
            sys.stdout.write("\n")
            sys.stdout.flush()
        else:
            # если не stdout — у тебя может быть --out / --out-dir
            # (оставь как есть)
            pass

    # determine output path
    out_path: Optional[Path] = None
    if args.out:
        out_path = args.out
    else:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{ts}_{args.goal}_{args.role}.json"

    # Если просят stdout — печатаем JSON (без лишнего текста)
    if args.stdout:
        emit_report(report, pretty=args.pretty, stdout=True)

    # Если нужно записать файл — записываем
    if out_path is not None:
        _safe_write_json(out_path, report, pretty=args.pretty)
        # НЕ печатаем в stdout, чтобы не ломать пайпы
        # Можно залогировать в stderr через logging (не обязательно)
        logger.info("Wrote optimization report -> %s", out_path.as_posix())

    # 6.5.0.7: Решаем exit code на основе strict режима
    from agent.fashion.cli.exit_codes import decide_exit_code
    decision = decide_exit_code(report, strict=bool(getattr(args, "strict", False)))

    # 6.6.0: Dataset logging
    dataset_dir = getattr(args, "dataset_dir", None)
    candidates_data = None  # для dataset
    
    if dataset_dir and run is not None:
        # 5) Извлекаем candidates_data из run (для dataset)
        candidates_data = run.candidates_data if run else None

        # 7.1.0: добавляем ranker информацию
        ranker_info = None
        if getattr(args, 'ranker_model', None) and run and hasattr(run, 'candidates_data') and run.candidates_data:
            # Проверяем, был ли ranker действительно загружен
            candidates = run.candidates_data.get("candidates", [])
            evaluated_count = len([c for c in candidates if c.get("evaluated", False)])
            skipped_count = len([c for c in candidates if not c.get("evaluated", True)])
            
            # Если есть pred_score и rank_position - ranker был загружен
            has_ranker_data = any(c.get("pred_score") is not None and c.get("rank_position") is not None for c in candidates)
            
            if has_ranker_data:
                ranker_info = {
                    "model": getattr(args, 'ranker_model'),
                    "top_k": getattr(args, 'ranker_top_k', 5),
                    "fallback": "none",  # ranker loaded successfully
                    "evaluated_count": evaluated_count,
                    "skipped_count": skipped_count,
                    "ranker_only": getattr(args, 'ranker_only', False)
                }
            else:
                ranker_info = {
                    "model": getattr(args, 'ranker_model'),
                    "top_k": getattr(args, 'ranker_top_k', 5),
                    "fallback": getattr(args, 'ranker_fallback', 'baseline'),
                    "evaluated_count": evaluated_count,
                    "skipped_count": skipped_count,
                    "ranker_only": getattr(args, 'ranker_only', False)
                }
        
        # 7.3.1: добавляем chooser информацию
        chooser_info = None
        chooser_model = getattr(args, 'chooser_model', None)
        
        if chooser_model:
            # Всегда добавляем chooser информацию если указана модель
            if run and hasattr(run, 'candidates_data') and run.candidates_data:
                candidates = run.candidates_data.get("candidates", [])
                evaluated_count = len([c for c in candidates if c.get("evaluated", False)])
                skipped_count = len([c for c in candidates if not c.get("evaluated", True)])
                
                # Проверяем, есть ли p_choose у кандидатов
                has_chooser_data = any(c.get("p_choose") is not None for c in candidates)
                
                if has_chooser_data:
                    # 7.3.2: получаем chooser метрики
                    chooser_metrics_data = run.candidates_data.get("chooser_metrics", {})
                    
                    chooser_info = {
                        "model": chooser_model,
                        "top_k": getattr(args, 'chooser_top_k', 5),
                        "fallback": "none",  # chooser loaded successfully
                        "evaluated_count": evaluated_count,
                        "skipped_count": skipped_count,
                        "chooser_only": getattr(args, 'chooser_only', False),
                        # 7.3.2: добавляем метрики
                        "temperature": chooser_metrics_data.get("temperature", 1.0),
                        "mean_entropy": chooser_metrics_data.get("mean_entropy", 0.0),
                        "mean_margin": chooser_metrics_data.get("mean_margin", 0.0)
                    }
                else:
                    chooser_info = {
                        "model": chooser_model,
                        "top_k": getattr(args, 'chooser_top_k', 5),
                        "fallback": "load_failed",
                        "evaluated_count": evaluated_count,
                        "skipped_count": skipped_count,
                        "chooser_only": getattr(args, 'chooser_only', False),
                        # 7.3.2: базовые метрики при ошибке
                        "temperature": float(getattr(args, 'chooser_temperature', 1.0)),
                        "mean_entropy": 0.0,
                        "mean_margin": 0.0
                    }
            else:
                # Если нет candidates_data, все равно добавляем базовую информацию
                chooser_info = {
                    "model": chooser_model,
                    "top_k": getattr(args, 'chooser_top_k', 5),
                    "fallback": "no_candidates_data",
                    "evaluated_count": 0,
                    "skipped_count": 0,
                    "chooser_only": getattr(args, 'chooser_only', False),
                    # 7.3.2: базовые метрики
                    "temperature": float(getattr(args, 'chooser_temperature', 1.0)),
                    "mean_entropy": 0.0,
                    "mean_margin": 0.0
                }
        
        # 7.4.0: добавляем hybrid информацию если есть
        print(f"[DEBUG OPTIMIZE] candidates_data type: {type(candidates_data)}")
        print(f"[DEBUG OPTIMIZE] candidates_data keys: {candidates_data.keys() if candidates_data else 'None'}")
        print(f"[DEBUG OPTIMIZE] candidates_data.get('hybrid_metrics'): {candidates_data.get('hybrid_metrics') if candidates_data else 'None'}")
        hybrid_data = {"hybrid": candidates_data.get("hybrid_metrics")} if candidates_data and candidates_data.get("hybrid_metrics") else {}
        
        optimization_data = {
            "report": report,
            # добавляем кандидатов если есть
            **({"candidates": candidates_data.get("candidates"), "chosen_index": candidates_data.get("chosen_index")} if candidates_data else {}),
            # добавляем ranker информацию если есть
            **({"ranker": ranker_info} if ranker_info else {}),
            # добавляем chooser информацию если есть
            **({"chooser": chooser_info} if chooser_info else {}),
            # добавляем hybrid информацию
            **hybrid_data
        }   

    if dataset_dir:
        from agent.fashion.dataset import (
            DatasetWriteConfig,
            build_env_block,
            try_read_git_commit,
            utc_now_iso,
            write_dataset_sample,
        )

        def build_run_id(report: dict) -> str:
            # можно использовать то, что уже используешь для имени файла отчёта
            target = report.get("target") or {}
            goal = target.get("goal", "goal")
            role = target.get("role", "role")
            seed = (report.get("meta") or {}).get("seed", 0)
            ts = utc_now_iso().replace(":", "").replace("-", "")
            return f"{ts}_{goal}_{role}_seed{seed}"

        sample = {
            "schema": "agent-fashion-dataset@1",
            "ts_utc": utc_now_iso(),
            "run_id": build_run_id(report),
            "cli": {
                "command": "agent.fashion.cli optimize",
                "args": vars(args),
            },
            "env": build_env_block(),
            "build": {
                "agent_version": "6.6.0",
                "git_commit": try_read_git_commit(),
            },
            "input": {
                "target": report.get("target"),
                "intent_path": getattr(args, "in_intent", None),
                # если у тебя есть explain() baseline — положи сюда
                "pattern_explain": None,
            },
            "optimization": {
                "report": report,
                # добавляем кандидатов если есть
                **({"candidates": candidates_data.get("candidates"), "chosen_index": candidates_data.get("chosen_index")} if candidates_data else {}),
                # добавляем ranker информацию если есть
                **({"ranker": optimization_data.get("ranker")} if optimization_data.get("ranker") else {}),
                # добавляем chooser информацию если есть
                **({"chooser": optimization_data.get("chooser")} if optimization_data.get("chooser") else {}),
                # добавляем hybrid информацию если есть
                **({"hybrid": optimization_data.get("hybrid")} if optimization_data.get("hybrid") else {})
            },
            "exit": {
                "code": decision.code,
                "reason": decision.reason,
                "detail": decision.detail,
            }
        }

        cfg = DatasetWriteConfig(
            dataset_dir=dataset_dir,
            fmt=getattr(args, "dataset_format", "json"),  # меняем на json для отладки
            write_mode=getattr(args, "dataset_write_mode", "append"),
        )
        write_dataset_sample(sample, cfg)

    return decision.code


if __name__ == "__main__":
    raise SystemExit(main())
