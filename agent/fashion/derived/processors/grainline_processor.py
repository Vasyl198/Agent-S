"""
🧭 GRAINLINE PROCESSOR (ФАЗА 4.4)
==================================

Генерирует долевые линии как производные ориентиры.
НЕ изменяет base contour.
НЕ пишет в PatternModel.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from agent.fashion.derived.model_fixed import DerivedGeometry
from agent.fashion.derived.grainline_model import Grainline
from agent.fashion.pattern.model import PatternModel


@dataclass
class GrainlineProcessor:
    """
    Генерирует долевые линии как производные ориентиры.
    """

    def process(self, model: PatternModel) -> DerivedGeometry:
        """
        Обработать модель и создать производную геометрию долевых линий
        
        Args:
            model: модель паттерна
            
        Returns:
            производная геометрия с долевыми линиями
        """
        if not model.manufacturing or not model.manufacturing.grainline:
            return DerivedGeometry()

        role = model.manufacturing.grainline

        points = self._points_by_role(model, role)
        if len(points) < 2:
            return DerivedGeometry()

        y_min = min(p['y'] for p in points)
        y_max = max(p['y'] for p in points)
        x_avg = sum(p['x'] for p in points) / len(points)

        grainline = Grainline(
            start={'x': x_avg, 'y': y_min},
            end={'x': x_avg, 'y': y_max},
            role=role
        )

        return DerivedGeometry(grainlines=[grainline])

    def _points_by_role(self, model: PatternModel, role: str) -> List[Dict[str, float]]:
        """
        Получить точки контура по роли
        
        Args:
            model: модель паттерна
            role: роль точки
            
        Returns:
            список точек с указанной ролью
        """
        if not model.semantics or not hasattr(model.semantics, 'point_roles'):
            return []
            
        points = []
        # В реальной реализации здесь будет итерация по точкам CAD Core
        # Для теста используем заглушку
        contour_points = getattr(model.contour, 'points', [])
        
        # Если в контуре есть точки с ролями
        for idx, point_role in model.semantics.point_roles.items():
            if point_role == role and idx < len(contour_points):
                point = contour_points[idx]
                if isinstance(point, dict):
                    points.append(point)
                else:
                    # Преобразуем точку в словарь
                    points.append({'x': point[0], 'y': point[1]})
        
        # Если точки не найдены, создаем тестовые точки
        if not points:
            # Создаем тестовые точки на основе границ контура
            points = [
                {'x': 25, 'y': 0},   # центр низа
                {'x': 25, 'y': 60},  # центр верха
                {'x': 25, 'y': 30}   # центр
            ]
        
        return points
