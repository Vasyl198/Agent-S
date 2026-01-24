"""
🔄 OPTIMIZATION LOOP — ОСНОВНОЙ ЦИКЛ ОПТИМИЗАЦИИ
================================================

🎯 Создает Optimization Loop: генерирует → применяет → оценивает → выбирает

❌ НЕ читает геометрию
✅ Полностью детерминированный
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
try:
    from .base import BaseOptimizer, OptimizationResult, DeterministicOptimizer
    from .candidate import OptimizationCandidate, CandidatePool
    from .generator import CandidateGenerator
    from .evaluator import CandidateEvaluator
except ImportError:
    # Fallback если модули недоступны
    BaseOptimizer = None
    OptimizationResult = None
    DeterministicOptimizer = None
    OptimizationCandidate = None
    CandidatePool = None
    CandidateGenerator = None
    CandidateEvaluator = None

# Импортируем TargetLibrary для единой точки входа
try:
    from ..targets.library import TargetLibrary
    from ..targets.spec import TargetSpec
    from ..rule_proposal import propose_rule_changes
    from ..apply_proposal import apply_proposal_with_target
except ImportError:
    # Если targets еще не импортированы, используем заглушки
    TargetLibrary = None
    TargetSpec = None
    propose_rule_changes = None
    apply_proposal_with_target = None


@dataclass(frozen=True)
class OptimizationStepResult:
    """Результат одного шага оптимизации"""
    step_index: int
    baseline_score: float
    best_score: float
    improvement: float
    chosen_proposal: Optional[Dict[str, Any]]
    candidates_count: int
    valid_candidates_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OptimizationRunResult:
    """Результат многошаговой оптимизации"""
    baseline_score: float
    final_score: float
    improvement: float
    steps: List[Dict[str, Any]]
    final_model: Any  # PatternModel
    stopped_reason: str
    candidates_data: Optional[Dict[str, Any]] = None  # 6.6.1: кандидаты для dataset
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # final_model не сериализуем тут — только explain_full() выше уровнем, если нужно
        d["final_model"] = None
        return d


class OptimizationLoop:
    """
    Основной цикл оптимизации
    
    📌 Генерирует предложения → применяет → оценивает → выбирает лучший
    """
    
    def __init__(
        self, 
        constraint_validator=None,
        reward_evaluator=None,
        target: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализировать цикл оптимизации
        
        Args:
            constraint_validator: валидатор ограничений
            reward_evaluator: оценщик качества
            target: цель оптимизации для демо evaluator
        """
        self.evaluator = CandidateEvaluator(constraint_validator, reward_evaluator, target=target)
        self.target = target
        self.reward_evaluator = reward_evaluator
        
        if CandidateGenerator is not None:
            self.generator = CandidateGenerator()
        else:
            self.generator = None
    
    def optimize(self, pattern_model, candidate_count: int = 5, **kwargs) -> OptimizationResult:
        """
        Оптимизировать PatternModel
        
        Args:
            pattern_model: исходная модель паттерна
            candidate_count: количество кандидатов
            **kwargs: дополнительные параметры
            
        Returns:
            результат оптимизации
        """
        # 1. Оцениваем baseline
        baseline_score = self._evaluate_model(pattern_model)
        
        # 2. Генерируем предложения
        proposals = self.generator.generate_candidates(pattern_model, candidate_count)
        
        # Если нет предложений, возвращаем baseline
        if not proposals:
            return OptimizationResult(
                best_score=baseline_score,
                baseline_score=baseline_score,
                improvement=0.0,
                chosen_proposal=None,
                candidates=[],
                best_model=pattern_model,
                baseline_model=pattern_model
            )
        
        # 3. Оцениваем кандидатов
        candidate_pool = self.evaluator.evaluate_candidates(pattern_model, proposals)
        
        # 4. Добавляем baseline как кандидата
        baseline_candidate = OptimizationCandidate(
            model=pattern_model,
            proposal=None,
            score=baseline_score,
            is_valid=True
        )
        candidate_pool.add_candidate(baseline_candidate)
        
        # 5. Выбираем лучшего
        best_candidate = candidate_pool.get_best_candidate()
        
        if best_candidate is None:
            # Если нет кандидатов, возвращаем baseline
            return OptimizationResult(
                best_score=baseline_score,
                baseline_score=baseline_score,
                improvement=0.0,
                chosen_proposal=None,
                candidates=[],
                best_model=pattern_model,
                baseline_model=pattern_model
            )
        
        # Собираем информацию о кандидатах
        candidates_info = []
        for candidate in candidate_pool.get_sorted_candidates():
            candidates_info.append({
                "score": candidate.score,
                "is_valid": candidate.is_valid,
                "proposal": candidate.proposal,
                "error_message": candidate.error_message
            })
        
        # Вычисляем improvement
        improvement = float(best_candidate.score) - float(baseline_score)
        
        return OptimizationResult(
            best_score=best_candidate.score,
            baseline_score=baseline_score,
            improvement=improvement,
            chosen_proposal=best_candidate.proposal,
            candidates=candidates_info,
            best_model=best_candidate.model,
            baseline_model=pattern_model
        )
    
    def optimize_for_target(
        self, 
        pattern_model, 
        target_spec: Union[Dict[str, Any], 'TargetSpec'], 
        candidate_count: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Оптимизировать для конкретной цели (единственная точка входа)
        
        Args:
            pattern_model: исходная модель паттерна
            target_spec: цель оптимизации (TargetSpec или dict)
            candidate_count: количество кандидатов
            **kwargs: дополнительные параметры
            
        Returns:
            результат оптимизации с chosen_target
        """
        # Нормализуем и валидируем цель
        if TargetLibrary is not None and TargetSpec is not None:
            if isinstance(target_spec, dict):
                target = TargetLibrary.from_dict(target_spec)
            else:
                target = target_spec
            
            # Полная валидация цели
            TargetLibrary.full_validate(target)
            
            # Получаем разрешенные пути
            allowed_paths = TargetLibrary.allowed_paths(target)
        else:
            # Fallback если TargetLibrary недоступен
            target = target_spec
        
        # 1. Оцениваем baseline
        baseline_score = self._evaluate_model(pattern_model)
        
        # 2. Генерируем explain_graph для proposal engine
        explain_graph = self._get_explain_graph(pattern_model)
        
        # 3. Генерируем предложение через RuleProposalEngine
        if propose_rule_changes is not None:
            proposal = propose_rule_changes(explain_graph, target)
        else:
            # Fallback - генерируем простое предложение
            proposal = {"proposed_rule_changes": [], "affected_derived": []}
        
        # 4. Применяем предложение с гейтингом
        if apply_proposal_with_target is not None:
            new_model = apply_proposal_with_target(pattern_model, proposal, target)
        else:
            # Fallback - применяем без гейтинга
            new_model = self._apply_proposal(pattern_model, proposal)
        
        # 5. Оцениваем новую модель
        final_score = self._evaluate_model(new_model)
        improvement = final_score - baseline_score
        
        # 6. Формируем результат
        result = {
            "baseline_score": baseline_score,
            "final_score": final_score,
            "improvement": improvement,
            "chosen_target": target.to_dict() if hasattr(target, 'to_dict') else target,
            "steps": [{
                "step_index": 0,
                "baseline_score": baseline_score,
                "best_score": final_score,
                "improvement": improvement,
                "chosen_proposal": proposal,
                "candidates_count": 1,
                "valid_candidates_count": 1 if proposal.get("proposed_rule_changes") else 0
            }],
            "best_model": new_model,
            "baseline_model": pattern_model
        }
        
        return result
    
    def _get_explain_graph(self, pattern_model) -> Dict[str, Any]:
        """Получить explain_graph из модели"""
        try:
            if hasattr(pattern_model, 'explain_full'):
                return pattern_model.explain_full()
            else:
                # Fallback - простой explain_graph
                return {
                    "type": "pattern_explain_graph",
                    "intent": {
                        "manufacturing": pattern_model.manufacturing.__dict__ if pattern_model.manufacturing else {},
                        "grading": pattern_model.grading.__dict__ if pattern_model.grading else {}
                    },
                    "links": []
                }
        except Exception:
            # Если не удалось получить explain_graph
            return {
                "type": "pattern_explain_graph",
                "intent": {},
                "links": []
            }
    
    def run_steps(
        self,
        pattern_model,
        target: Dict[str, Any],
        *,
        max_steps: int = 5,
        epsilon: float = 0.01,
        strict: bool = True,
        seed: int = 0,
        max_candidates_per_step: int = 8,
        ranker_model: Optional[str] = None,
        ranker_top_k: int = 5,
        ranker_fallback: str = "baseline",
        ranker_only: bool = False,
        chooser_model: Optional[str] = None,
        chooser_top_k: int = 5,
        chooser_only: bool = False,
        chooser_temperature: Optional[float] = None,
        # 7.4.0: hybrid параметры
        hybrid: bool = False,
        chooser_top_m: int = 10,
        hybrid_top_k: Optional[int] = None,
    ) -> OptimizationRunResult:
        """
        Запустить многошаговую оптимизацию
        
        Args:
            pattern_model: исходная модель паттерна
            target: цель оптимизации
            max_steps: максимальное количество шагов
            epsilon: порог улучшения для остановки
            strict: строгий режим (не позволяет ухудшение)
            seed: seed для детерминизма
            max_candidates_per_step: максимальное количество кандидатов на шаг
            
        Returns:
            результат многошаговой оптимизации
        """
        # Используем seed для детерминизма
        local_generator = CandidateGenerator(seed)
        seen_changes = set()  # guard от циклов: (path, from, to)
        steps: List[Dict[str, Any]] = []

        baseline_score = self._evaluate_model(pattern_model)
        current_model = pattern_model
        current_score = baseline_score
        all_candidates_for_dataset = []  # 6.6.1: все кандидаты для dataset
        final_chosen_index = -1  # 6.6.1: финальный выбранный индекс
        candidates_data = {  # 7.1.0: инициализируем candidates_data
            "candidates": [],
            "chosen_index": -1
        }
        
        # 7.1.0: загружаем ranker если указан
        ranker = None
        if ranker_model:
            try:
                from ...ml.ranker_runtime import load_ranker
                ranker = load_ranker(ranker_model)
            except Exception as e:
                if ranker_fallback == "none":
                    raise RuntimeError(f"Failed to load ranker model: {e}")
                # fallback to baseline
                ranker = None
        
        # 7.3.1: загружаем chooser если указан
        chooser = None
        if chooser_model:
            try:
                from ...ml.chooser_runtime import load_chooser
                chooser = load_chooser(chooser_model)
                # 7.3.2: устанавливаем температуру
                chooser.temperature = float(chooser_temperature) if chooser_temperature is not None else 1.0
            except Exception as e:
                # chooser не имеет fallback - всегда ошибка
                raise RuntimeError(f"Failed to load chooser model: {e}")

        stopped_reason = "max_steps_reached"
        
        # 7.3.2: переменная для хранения chooser метрик
        chooser_metrics = None
        
        # 7.4.0: переменная для хранения hybrid метаданных
        hybrid_metrics = None

        def _is_chooser_flat(probs: list[float], eps: float = 1e-12) -> bool:
            """Определяет, является ли chooser signal плоским"""
            if not probs:
                return True
            pmin = min(probs)
            pmax = max(probs)
            return (pmax - pmin) < eps

        for step_idx in range(max_steps):
            # 1) сгенерировать кандидатов proposals (детерминированно)
            candidates = local_generator.generate_candidates(current_model, max_candidates_per_step)

            # 7.1.0: ранжирование кандидатов с ML ranker (только если не hybrid)
            ranked_candidates = []
            if ranker and not hybrid:
                from ...ml.rank_candidates import rank_candidates
                # Создаем sample для featurize
                sample_for_ranker = {
                    "run_id": f"step_{step_idx}",
                    "input": {"target": target},
                    "optimization": {"candidates": candidates, "chosen_index": None}
                }
                ranked_candidates = rank_candidates(ranker, sample_for_ranker, candidates)
                # Добавляем rank_position и pred_score
                for i, c in enumerate(ranked_candidates):
                    c["rank_position"] = i
                    c["evaluated"] = False
                filtered = ranked_candidates
            else:
                # Без раннего ranker или в hybrid режиме - базовая фильтрация
                filtered = []
                for c in candidates:
                    # 6.6.1: Поддерживаем как target-предложения, так и rule changes
                    if c.get("type") == "target":
                        # Target-предложения всегда пропускаем
                        filtered.append(c)
                    else:
                        # Оригинальная логика для rule changes
                        changes = c.get("proposed_rule_changes", [])
                        if not changes:
                            continue
                        key = (changes[0].get("path"), changes[0].get("from"), changes[0].get("to"))
                        if key in seen_changes:
                            continue
                        filtered.append(c)

            # если нет кандидатов — стоп
            if not filtered:
                stopped_reason = "no_candidates"
                break

            # 7.3.1: chooser ранжирование кандидатов (только если не hybrid)
            if chooser and not hybrid:
                # Создаем sample для featurize
                sample_for_chooser = {
                    "run_id": f"step_{step_idx}",
                    "input": {"target": target},
                    "optimization": {"candidates": filtered, "chosen_index": None}
                }
                
                # 7.3.2: получаем logits и вероятности
                logits, probs = chooser.predict_logits_and_probs(sample_for_chooser, filtered)
                
                # Добавляем choice_logit и p_choose к кандидатам
                for candidate_data, logit, p in zip(filtered, logits, probs):
                    candidate_data["choice_logit"] = float(logit)
                    candidate_data["p_choose"] = float(p)
                
                # Ранжируем по p_choose
                filtered_with_indices = list(enumerate(filtered))
                filtered_with_indices.sort(key=lambda t: t[1].get("p_choose", 0.0), reverse=True)
                filtered = [c for _, c in filtered_with_indices]
                
                # Сохраняем choice_rank_position
                for pos, candidate_data in enumerate(filtered):
                    candidate_data["choice_rank_position"] = pos
                
                # 7.3.2: считаем метрики entropy и margin
                import math
                
                def _entropy(p):
                    return -(p * math.log(p) + (1 - p) * math.log(1 - p))
                
                # Mean entropy
                mean_entropy = sum(_entropy(c["p_choose"]) for c in filtered) / len(filtered)
                
                # Margin (top1 - top2)
                sorted_probs = [c["p_choose"] for c in filtered]
                margin = float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) >= 2 else 0.0
                
                # Сохраняем метрики для использования в dataset
                chooser_metrics = {
                    "mean_entropy": float(mean_entropy),
                    "mean_margin": float(margin),
                    "temperature": float(chooser.temperature)
                }
            elif not hybrid:
                # Если chooser не используется, но и не hybrid - устанавливаем пустые метрики
                chooser_metrics = {
                    "mean_entropy": 0.0,
                    "mean_margin": 0.0,
                    "temperature": 1.0
                }

            # 7.4.0: Hybrid Policy - Chooser → Ranker → Top-K real evaluate
            if hybrid:
                print(f"[DEBUG] Hybrid mode enabled! hybrid={hybrid}")
                # Инициализируем переменные для hybrid режима
                evaluated = []
                valid_count = 0
                chooser_flat = None  # 7.4.1: инициализируем переменную
                
                # Сохраняем оригинальные кандидаты до chooser фильтрации
                original_filtered = filtered.copy()
                
                # Создаем sample для featurize
                sample_for_chooser = {
                    "run_id": f"step_{step_idx}",
                    "input": {"target": target},
                    "optimization": {"candidates": original_filtered, "chosen_index": None}
                }
                
                # 1) Chooser stage (optional)
                if chooser:
                    logits, probs = chooser.predict_logits_and_probs(sample_for_chooser, original_filtered)
                    for i, c in enumerate(original_filtered):
                        c["choice_logit"] = float(logits[i])
                        c["p_choose"] = float(probs[i])
                    # Ранжируем по p_choose
                    original_filtered.sort(key=lambda c: c.get("p_choose", 0.0), reverse=True)
                    for pos, c in enumerate(original_filtered):
                        c["choice_rank_position"] = pos
                    print(f"[DEBUG] Chooser fields added to {len(original_filtered)} candidates")
                    
                    # 7.4.1: Fallback логика для flat chooser
                    probs_list = [c.get("p_choose", 0.0) for c in original_filtered]
                    chooser_flat = _is_chooser_flat(probs_list)
                    
                    if chooser_flat:
                        effective_top_m = len(original_filtered)  # не режем
                        print(f"[DEBUG] Chooser is flat, using all {len(original_filtered)} candidates")
                    else:
                        effective_top_m = min(chooser_top_m, len(original_filtered))
                        print(f"[DEBUG] Chooser not flat, using top {effective_top_m} candidates")
                    
                    stage1 = original_filtered[:effective_top_m]
                    stage2_rest = original_filtered[effective_top_m:]
                    M = effective_top_m
                else:
                    # Без chooser - все кандидаты идут в stage1
                    stage1 = original_filtered
                    stage2_rest = []
                    M = len(original_filtered)
                    chooser_flat = False  # 7.4.1: нет chooser = не flat
                    print(f"[DEBUG] No chooser - using all {len(original_filtered)} candidates")
                
                # 2) Ranker stage (required in hybrid)
                if ranker:
                    # Ранжируем stage1 через ranker
                    from ...ml.rank_candidates import rank_candidates
                    ranked_stage1 = rank_candidates(ranker, sample_for_chooser, stage1)
                    # rank_candidates уже ставит pred_score и rank_position
                else:
                    raise ValueError("Hybrid mode requires ranker model")
                
                K = hybrid_top_k or ranker_top_k or 5
                K = min(K, len(ranked_stage1))
                
                to_evaluate = ranked_stage1[:K]
                skipped = ranked_stage1[K:] + stage2_rest
                
                # 3) Real evaluation
                if not ranker_only and not chooser_only:
                    for candidate_data in to_evaluate:
                        if isinstance(candidate_data, dict) and "proposal" in candidate_data:
                            proposal = candidate_data["proposal"]
                        else:
                            proposal = candidate_data
                        
                        new_model = self._apply_proposal(current_model, proposal)
                        constraint_result = self._validate_constraints(new_model)
                        if not constraint_result.ok:
                            candidate_data["evaluated"] = False
                            candidate_data["constraint_ok"] = False
                            continue
                        
                        candidate = self.evaluator.evaluate_candidate(current_model, proposal=proposal)
                        score = candidate.score
                        improvement = score - current_score
                        
                        candidate_data["evaluated"] = True
                        candidate_data["score"] = score
                        candidate_data["improvement"] = improvement
                        candidate_data["constraint_ok"] = True
                        
                        evaluated.append((score, proposal, new_model))
                else:
                    for candidate_data in to_evaluate:
                        candidate_data["evaluated"] = False
                
                for candidate_data in skipped:
                    candidate_data["evaluated"] = False
                
                # Итоговый список кандидатов для dataset
                candidates_final = to_evaluate + skipped
                step_candidates_for_dataset = candidates_final
                
                # 7.4.0: Сохраняем hybrid метаданные
                hybrid_metrics = {
                    "enabled": True,
                    "candidate_count": len(original_filtered),
                    "chooser_requested_top_m": chooser_top_m,
                    "chooser_effective_top_m": M,
                    "chooser_flat": chooser_flat,
                    "ranker_top_k": K
                }
                print(f"[DEBUG] Hybrid metrics created: {hybrid_metrics}")
                
                # 7.4.0: Устанавливаем chooser_metrics для hybrid режима
                if chooser:
                    # Считаем метрики для всех отфильтрованных кандидатов
                    import math
                    def _entropy(p):
                        return -(p * math.log(p) + (1 - p) * math.log(1 - p))
                    
                    mean_entropy = sum(_entropy(c["p_choose"]) for c in original_filtered) / len(original_filtered)
                    sorted_probs = sorted([c["p_choose"] for c in original_filtered], reverse=True)
                    margin = float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) >= 2 else 0.0
                    
                    chooser_metrics = {
                        "mean_entropy": float(mean_entropy),
                        "mean_margin": float(margin),
                        "temperature": float(chooser.temperature)
                    }
                else:
                    chooser_metrics = {
                        "mean_entropy": 0.0,
                        "mean_margin": 0.0,
                        "temperature": 1.0
                    }
                
                # Обновляем filtered для дальнейшей обработки
                filtered = candidates_final
            else:
                # Оригинальная логика (non-hybrid)
                # 2) оценить кандидатов
                evaluated = []
                valid_count = 0
                step_candidates_for_dataset = []  # кандидаты только для этого шага
                evaluated_count = 0
                
                # Определяем top_k для реальной оценки
                if chooser:
                    top_k = min(chooser_top_k, len(filtered))
                elif ranker:
                    top_k = min(ranker_top_k, len(filtered))
                else:
                    top_k = len(filtered)

                for i, candidate_data in enumerate(filtered):
                    # Определяем proposal и helper функции
                    if chooser or ranker:
                        # Для chooser/ranker: candidate_data - это словарь с proposal и метаданными
                        if isinstance(candidate_data, dict) and "proposal" in candidate_data:
                            proposal = candidate_data["proposal"]
                            def get_field(field, default=0.0):
                                return candidate_data.get(field, default)
                            def set_field(field, value):
                                candidate_data[field] = value
                        else:
                            # Если структура другая, используем весь candidate_data как proposal
                            proposal = candidate_data
                            def get_field(field, default=0.0):
                                return candidate_data.get(field, default)
                            def set_field(field, value):
                                candidate_data[field] = value
                    else:
                        # Если нет chooser/ranker, candidate_data это сам proposal
                        proposal = candidate_data
                        def get_field(field, default=0.0):
                            return default
                        def set_field(field, value):
                            pass  # не можем изменять не-dict

                    
                    if chooser:
                        if chooser_only:
                            # Сохраняем только chooser данные
                            step_candidates_for_dataset.append({
                                "score": get_field("p_choose", 0.0),
                                "improvement": get_field("p_choose", 0.0) - current_score,
                                "proposal": proposal,
                                "constraint_ok": True,  # предполагаем валидность
                                "p_choose": get_field("p_choose", 0.0),
                                "choice_logit": get_field("choice_logit", 0.0),
                                "choice_rank_position": get_field("choice_rank_position", i),
                                "evaluated": False
                            })
                            evaluated.append((get_field("p_choose", 0.0), proposal, current_model))
                            continue
                        # violations — кандидат можно считать невалидным
                        continue
                    valid_count += 1
                    
                    if chooser:
                        # Для chooser: реальная оценка top-K
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        # Обновляем candidate_data с реальными данными
                        if isinstance(candidate_data, dict):
                            candidate_data["evaluated"] = True
                            candidate_data["score"] = score
                            candidate_data["improvement"] = improvement
                        else:
                            # Если candidate_data это не dict, создаем новый dict
                            candidate_data = {
                                "evaluated": True,
                                "score": score,
                                "improvement": improvement,
                                "proposal": proposal
                            }
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "p_choose": candidate_data.get("p_choose", 0.0) if isinstance(candidate_data, dict) else 0.0,
                            "choice_logit": candidate_data.get("choice_logit", 0.0) if isinstance(candidate_data, dict) else 0.0,
                            "choice_rank_position": candidate_data.get("choice_rank_position", i) if isinstance(candidate_data, dict) else i,
                            "evaluated": True
                        })
                        evaluated_count += 1
                    elif ranker:
                        # Для ranker: реальная оценка top-K
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        # Обновляем candidate_data с реальными данными
                        candidate_data["evaluated"] = True
                        candidate_data["score"] = score
                        candidate_data["improvement"] = improvement
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "pred_score": candidate_data["pred_score"],
                            "rank_position": candidate_data["rank_position"],
                            "evaluated": True,
                            # 7.3.2: добавляем chooser поля
                            "choice_logit": candidate_data.get("choice_logit", 0.0),
                            "p_choose": candidate_data.get("p_choose", 0.0),
                            "choice_rank_position": candidate_data.get("choice_rank_position", 0)
                        })
                        print(f"[DEBUG] Saved to dataset: choice_logit={candidate_data.get('choice_logit', 0.0)}")
                        evaluated_count += 1
                    else:
                        # Для evaluator: обычная оценка
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "evaluated": True
                        })
                    
                    if chooser:
                        # Для chooser: реальная оценка top-K
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        # Обновляем candidate_data с реальными данными
                        if isinstance(candidate_data, dict):
                            candidate_data["evaluated"] = True
                            candidate_data["score"] = score
                            candidate_data["improvement"] = improvement
                        else:
                            # Если candidate_data это не dict, создаем новый dict
                            candidate_data = {
                                "evaluated": True,
                                "score": score,
                                "improvement": improvement,
                                "proposal": proposal
                            }
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "p_choose": candidate_data.get("p_choose", 0.0) if isinstance(candidate_data, dict) else 0.0,
                            "choice_logit": candidate_data.get("choice_logit", 0.0) if isinstance(candidate_data, dict) else 0.0,
                            "choice_rank_position": candidate_data.get("choice_rank_position", i) if isinstance(candidate_data, dict) else i,
                            "evaluated": True
                        })
                        evaluated_count += 1
                        evaluated.append((score, proposal, new_model))
                    elif ranker:
                        # Для ranker: реальная оценка top-K
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        # Обновляем candidate_data с реальными данными
                        candidate_data["evaluated"] = True
                        candidate_data["score"] = score
                        candidate_data["improvement"] = improvement
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "pred_score": candidate_data["pred_score"],
                            "rank_position": candidate_data["rank_position"],
                            "evaluated": True,
                            # 7.3.2: добавляем chooser поля
                            "choice_logit": candidate_data.get("choice_logit", 0.0),
                            "p_choose": candidate_data.get("p_choose", 0.0),
                            "choice_rank_position": candidate_data.get("choice_rank_position", 0)
                        })
                        evaluated_count += 1
                        evaluated.append((score, proposal, new_model))
                    else:
                        # Для evaluator: обычная оценка
                        candidate = self.evaluator.evaluate_candidate(
                            current_model, 
                            proposal=proposal
                        )
                        score = candidate.score
                        improvement = score - current_score
                        
                        step_candidates_for_dataset.append({
                            "score": score,
                            "improvement": improvement,
                            "proposal": proposal,
                            "constraint_ok": True,
                            "evaluated": True
                        })
                    
                    evaluated.append((score, proposal, new_model))

            if not evaluated:
                stopped_reason = "all_candidates_invalid"
                break

            # 3) выбрать лучшего
            if chooser_only and chooser:
                # В chooser_only режиме выбираем по p_choose
                best_candidate_data = max(filtered, key=lambda c: c.get("p_choose", 0.0))
                best_score = best_candidate_data.get("p_choose", 0.0)
                # Получаем proposal из candidate_data
                if isinstance(best_candidate_data, dict) and "proposal" in best_candidate_data:
                    best_proposal = best_candidate_data["proposal"]
                else:
                    # Если это сам proposal
                    best_proposal = best_candidate_data
                best_model = current_model  # не применяем изменения
                improvement = best_score - current_score
                best_idx = best_candidate_data.get("choice_rank_position", 0)
            elif ranker_only and ranker:
                # В ranker_only режиме выбираем по pred_score
                best_candidate_data = max(filtered, key=lambda c: c["pred_score"])
                best_score = best_candidate_data["pred_score"]
                best_proposal = best_candidate_data["proposal"]
                best_model = current_model  # не применяем изменения
                improvement = best_score - current_score
                best_idx = best_candidate_data["rank_position"]
            else:
                # Обычный режим: выбираем по реальной оценке
                evaluated.sort(key=lambda x: x[0], reverse=True)
                best_score, best_proposal, best_model = evaluated[0]
                improvement = best_score - current_score
                best_idx = next((i for i, (s, p, m) in enumerate(evaluated) if p == best_proposal), -1)
            
            # 6.6.1: сохраняем всех кандидатов для dataset (не только последнего)
            all_candidates_for_dataset.extend(step_candidates_for_dataset)
            
            # 6.6.1: обновляем chosen_index если это последний шаг
            if step_idx == max_steps - 1:
                if chooser_only and chooser:
                    # В chooser_only режиме chosen_index это choice_rank_position лучшего
                    final_chosen_index = best_idx
                elif ranker_only and ranker:
                    # В ranker_only режиме chosen_index это rank_position лучшего
                    final_chosen_index = best_idx
                elif evaluated:
                    best_proposal_global = evaluated[0][1]  # лучший из этого шага
                    # Ищем его индекс среди всех кандидатов этого шага
                    final_chosen_index = next((i for i, (s, p, m) in enumerate(evaluated) if p == best_proposal_global), -1)
                else:
                    final_chosen_index = -1
                candidates_data["chosen_index"] = final_chosen_index

            # зафиксировать шаг
            step_result = OptimizationStepResult(
                step_index=step_idx,
                baseline_score=current_score,
                best_score=best_score,
                improvement=improvement,
                chosen_proposal=best_proposal,
                candidates_count=len(candidates),
                valid_candidates_count=valid_count
            )
            steps.append(step_result.to_dict())

            # guard: пометить выбранное изменение
            ch = best_proposal.get("proposed_rule_changes", [])
            if ch:
                key = (ch[0].get("path"), ch[0].get("from"), ch[0].get("to"))
                seen_changes.add(key)

            # stop criteria
            if improvement <= epsilon:
                stopped_reason = "epsilon_reached"
                if strict:
                    break
                # если не strict — можно продолжать, но обычно не нужно
                break

            if strict and best_score < current_score:
                stopped_reason = "score_decreased_strict"
                break

            # принять лучший и идти дальше
            current_model = best_model
            current_score = best_score

        print(f"[DEBUG] Final candidates_data hybrid_metrics: {hybrid_metrics}")
        print(f"[DEBUG] Final candidates_data structure: {candidates_data.keys() if candidates_data else 'None'}")
        print(f"[DEBUG] all_candidates_for_dataset length: {len(all_candidates_for_dataset) if all_candidates_for_dataset else 'None'}")
        
        candidates_data_dict = {
            "candidates": all_candidates_for_dataset,
            "chosen_index": final_chosen_index,
            "chooser_metrics": chooser_metrics,
            "hybrid_metrics": hybrid_metrics if hybrid else None
        }
        
        return OptimizationRunResult(
            baseline_score=baseline_score,
            final_score=current_score,
            improvement=current_score - baseline_score,
            steps=steps,
            final_model=current_model,
            stopped_reason=stopped_reason,
            candidates_data=candidates_data_dict if all_candidates_for_dataset else None
        )
    
    def _apply_proposal(self, pattern_model, proposal: Dict[str, Any]) -> Any:
        """Применить предложение к модели"""
        try:
            if proposal.get("type") == "target":
                # 6.6.1: Применяем target-предложение напрямую
                return self._apply_target_proposal(pattern_model, proposal)
            else:
                # Оригинальная логика для rule changes
                from ..apply_proposal import apply_rule_proposal
                return apply_rule_proposal(pattern_model, proposal)
        except Exception as e:
            # ВАЖНО: не делаем тихий fallback - поднимаем ошибку
            raise RuntimeError(f"apply_rule_proposal failed: {e}") from e
    
    def _apply_target_proposal(self, pattern_model, proposal: Dict[str, Any]) -> Any:
        """Применить target-предложение к модели"""
        # Для target-предложений просто возвращаем ту же модель
        # В реальной системе здесь была бы трансформация в rule changes
        # Но для демо просто возвращаем модель без изменений
        return pattern_model
    
    def _validate_constraints(self, pattern_model) -> Any:
        """Валидировать ограничения модели"""
        if self.evaluator.constraint_validator:
            return self.evaluator.constraint_validator.validate(pattern_model)
        # Возвращаем mock результат если нет валидатора
        from types import SimpleNamespace
        return SimpleNamespace(ok=True)
    
    def _evaluate_model(self, pattern_model) -> float:
        """
        Оценить модель
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            оценка качества
        """
        return self.evaluator._evaluate_model(pattern_model)
    
    @property
    def name(self) -> str:
        """Название оптимизатора"""
        return "optimization_loop"
    
    @property
    def description(self) -> str:
        """Описание оптимизатора"""
        return "Детерминированный цикл оптимизации: генерирует → применяет → оценивает → выбирает"
    
    def set_constraint_validator(self, constraint_validator) -> None:
        """
        Установить валидатор ограничений
        
        Args:
            constraint_validator: валидатор ограничений
        """
        self.evaluator.set_constraint_validator(constraint_validator)
    
    def set_reward_evaluator(self, reward_evaluator) -> None:
        """
        Установить оценщик качества
        
        Args:
            reward_evaluator: оценщик качества
        """
        self.evaluator.set_reward_evaluator(reward_evaluator)


class MultiStepOptimizer:
    """
    Многошаговый оптимизатор
    
    📌 Применяет оптимизацию несколько раз подряд
    """
    
    def __init__(
        self, 
        steps: int = 3,
        seed: Optional[int] = None,
        constraint_validator=None,
        reward_evaluator=None
    ):
        """
        Инициализировать многошаговый оптимизатор
        
        Args:
            steps: количество шагов оптимизации
            seed: seed для детерминизма
            constraint_validator: валидатор ограничений
            reward_evaluator: оценщик качества
        """
        self.steps = steps
        self.seed = seed
        self.base_optimizer = OptimizationLoop(seed, constraint_validator, reward_evaluator)
    
    def optimize(self, pattern_model, candidate_count: int = 5, **kwargs) -> OptimizationResult:
        """
        Оптимизировать PatternModel за несколько шагов
        
        Args:
            pattern_model: исходная модель паттерна
            candidate_count: количество кандидатов на шаг
            **kwargs: дополнительные параметры
            
        Returns:
            результат оптимизации
        """
        current_model = pattern_model
        current_score = self._evaluate_model(pattern_model)
        
        all_candidates = []
        best_proposal = None
        
        for step in range(self.steps):
            # Оптимизируем текущую модель
            result = self.base_optimizer.optimize(current_model, candidate_count)
            
            # Если нет улучшения, останавливаемся
            if result.best_score <= current_score + 0.001:  # Порог улучшения
                break
            
            # Обновляем текущую модель
            current_model = result.best_model
            current_score = result.best_score
            best_proposal = result.chosen_proposal
            
            # Собираем кандидатов
            all_candidates.extend(result.candidates)
        
        return OptimizationResult(
            best_score=current_score,
            baseline_score=self._evaluate_model(pattern_model),
            improvement=current_score - self._evaluate_model(pattern_model),
            chosen_proposal=best_proposal,
            candidates=all_candidates,
            best_model=current_model,
            baseline_model=pattern_model
        )
    
    def _evaluate_model(self, pattern_model) -> float:
        """
        Оценить модель
        
        Args:
            pattern_model: модель паттерна
            
        Returns:
            оценка качества
        """
        return self.base_optimizer._evaluate_model(pattern_model)
    
    @property
    def name(self) -> str:
        """Название оптимизатора"""
        return "multi_step_optimizer"
    
    @property
    def description(self) -> str:
        """Описание оптимизатора"""
        return f"Многошаговый оптимизатор: {self.steps} шагов оптимизации"


# Создаем оптимизатор по умолчанию
default_optimizer = OptimizationLoop()


def optimize_pattern_model(pattern_model, **kwargs) -> OptimizationResult:
    """
    Оптимизировать PatternModel с оптимизатором по умолчанию
    
    Args:
        pattern_model: модель паттерна
        **kwargs: дополнительные параметры
        
    Returns:
        результат оптимизации
    """
    return default_optimizer.optimize(pattern_model, **kwargs)


import logging
logger = logging.getLogger(__name__)

logger.debug("OptimizationLoop loaded")
logger.debug("Основной цикл оптимизации: генерирует → применяет → оценивает → выбирает")
logger.debug("MultiStepOptimizer — многошаговая оптимизация")
logger.debug("Полностью детерминированный")
