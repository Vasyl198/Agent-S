"""
🧠 GRADING PROCESSOR — СЕРДЦЕ ФАЗЫ 3.3
==========================================

📌 КРИТИЧНО:
❌ не масштаб
❌ не угадывание
✅ семантика → правило → движение
✅ возвращает новую модель
"""

from typing import List

from agent.fashion.cad.core.geometry import Point, Segment
from agent.fashion.cad.core.contour import Contour
from ..model import PatternModel
from ..grading import PatternGrading


class RuleBasedGradingProcessor:
    """
    🧠 ПРОЦЕССОР ГРАДАЦИИ - ПРИМЕНЯЕТ ПРАВИЛА К ТОЧКАМ
    
    🔁 Semantics + Rules → New Contour
    """
    
    def process(self, pattern_model: PatternModel, grading: PatternGrading) -> PatternModel:
        """
        Применить градацию к модели паттерна
        
        Args:
            pattern_model: модель паттерна
            grading: правила градации
            
        Returns:
            новая модель с градированным контуром
        """
        if pattern_model.semantics is None:
            raise ValueError("Semantics required for grading")
        
        if pattern_model.grading is not None:
            raise ValueError("Grading already applied")
        
        # Получаем контур и семантику
        contour = pattern_model.contour
        semantics = pattern_model.semantics
        
        # Создаем новые точки на основе правил
        new_points = self._apply_grading_rules(contour.points, semantics, grading)
        
        # Создаем новые сегменты с новыми точками
        new_segments = self._create_new_segments(contour.segments, new_points)
        
        # Создаем новый контур
        new_contour = Contour(new_segments, closed=contour.closed)
        
        # Возвращаем новую модель с градацией
        return pattern_model.with_grading(grading).with_contour(new_contour)
    
    def _apply_grading_rules(self, points: List[Point], semantics, grading: PatternGrading) -> List[Point]:
        """
        Применить правила градации к точкам
        
        Args:
            points: список точек
            semantics: семантика паттерна
            grading: правила градации
            
        Returns:
            список новых точек
        """
        new_points = []
        
        for i, point in enumerate(points):
            # Получаем роль точки
            role = semantics.get_point_role(i)
            
            if role is None:
                # Если у точки нет роли, не двигаем её
                new_points.append(Point(point.x, point.y))
                continue
            
            # Получаем правило для роли
            dx, dy = grading.get_rule(role)
            
            # Создаем новую точку со смещением
            new_point = Point(point.x + dx, point.y + dy)
            new_points.append(new_point)
        
        return new_points
    
    def _create_new_segments(self, segments: List[Segment], new_points: List[Point]) -> List[Segment]:
        """
        Создать новые сегменты с новыми точками
        
        Args:
            segments: список старых сегментов
            new_points: список новых точек
            
        Returns:
            список новых сегментов
        """
        new_segments = []
        
        for segment in segments:
            # Находим индексы начальной и конечной точек
            start_idx = self._find_point_index(segment.start, new_points)
            end_idx = self._find_point_index(segment.end, new_points)
            
            if start_idx is not None and end_idx is not None:
                # Создаем новый сегмент с новыми точками
                new_segment = Segment(
                    start=new_points[start_idx],
                    end=new_points[end_idx],
                    bulge=segment.bulge
                )
                new_segments.append(new_segment)
            else:
                # Если не нашли точки, копируем сегмент как есть
                new_segments.append(segment)
        
        return new_segments
    
    def _find_point_index(self, target_point: Point, points: List[Point]) -> int:
        """
        Найти индекс точки в списке
        
        Args:
            target_point: искомая точка
            points: список точек
            
        Returns:
            индекс точки или None
        """
        for i, point in enumerate(points):
            if abs(point.x - target_point.x) < 1e-6 and abs(point.y - target_point.y) < 1e-6:
                return i
        return None
    
    def validate_grading_result(self, original_model: PatternModel, graded_model: PatternModel) -> bool:
        """
        Валидировать результат градации
        
        Args:
            original_model: исходная модель
            graded_model: градированная модель
            
        Returns:
            True если результат валиден
        """
        try:
            # Проверяем, что контуры разные
            if original_model.contour == graded_model.contour:
                return False
            
            # Проверяем, что количество точек и сегментов одинаковое
            if (len(original_model.contour.points) != len(graded_model.contour.points) or
                len(original_model.contour.segments) != len(graded_model.contour.segments)):
                return False
            
            # Проверяем, что семантика не изменилась
            if original_model.semantics != graded_model.semantics:
                return False
            
            # Проверяем, что градация установлена
            if graded_model.grading is None:
                return False
            
            return True
        except Exception:
            return False


print("🧠 RuleBasedGradingProcessor загружен")
print("📌 семантика → правило → движение")
print("📌 возвращает новую модель")
print("📌 КОНСТРУКТОРСКИЕ ПРАВИЛА, а не масштаб")
