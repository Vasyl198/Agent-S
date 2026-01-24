"""
🔧 SEAM ALLOWANCE PROCESSOR (ФАЗА 4.2)
======================================

Генерирует производную геометрию припусков.
НЕ изменяет base contour.
НЕ пишет в PatternModel.
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from agent.fashion.derived.model import DerivedGeometry
from agent.fashion.pattern.model import PatternModel


@dataclass
class SeamAllowanceProcessor:
    """
    Генерирует производную геометрию припусков.
    НЕ изменяет base contour.
    НЕ пишет в PatternModel.
    """

    def process(self, model: PatternModel) -> DerivedGeometry:
        """
        Обработать модель и создать производную геометрию припусков
        
        Args:
            model: модель паттерна
            
        Returns:
            производная геометрия с припусками
        """
        manufacturing = model.manufacturing
        semantics = model.semantics

        # ❗ Нет производства → нет derived geometry
        if manufacturing is None or not manufacturing.seam_allowances:
            return DerivedGeometry()

        allowance_contours: Dict[str, Any] = {}

        for role, allowance_mm in manufacturing.seam_allowances.items():
            segments = self._segments_by_role(
                model.contour,
                semantics,
                role
            )

            if not segments:
                continue

            offset_segments = [
                self._offset_segment(seg, allowance_mm)
                for seg in segments
            ]

            # Создаем заглушку контура (в реальной реализации здесь будет CAD Core Contour)
            allowance_contours[role] = {
                'type': 'contour',
                'segments': offset_segments,
                'allowance_mm': allowance_mm,
                'role': role
            }

        return DerivedGeometry(allowance_contours=allowance_contours)

    # ---------- helpers ----------

    def _segments_by_role(
        self,
        contour: Any,
        semantics: Any,
        role: str
    ) -> List[Any]:
        """
        Получить сегменты контура по роли
        
        Args:
            contour: контур паттерна
            semantics: семантика паттерна
            role: роль сегмента
            
        Returns:
            список сегментов с указанной ролью
        """
        if not semantics or not hasattr(semantics, 'segment_roles'):
            return []
            
        segments = []
        # В реальной реализации здесь будет итерация по сегментам CAD Core
        # Для теста используем заглушку
        for idx, segment in enumerate(getattr(contour, 'segments', [])):
            if semantics.segment_roles.get(idx) == role:
                segments.append(segment)
        
        return segments

    def _offset_segment(self, segment: Any, offset: float) -> Dict[str, Any]:
        """
        Примитивный offset сегмента в нормаль
        
        Args:
            segment: сегмент для offset
            offset: величина offset в мм
            
        Returns:
            offset сегмент (заглушка)
        """
        """
        V1: примитивный offset в нормаль сегмента
        ❗ Без скруглений
        ❗ Без соединений
        ❗ Только доказательство архитектуры
        """
        
        # В реальной реализации здесь будет геометрический расчет
        # Для теста возвращаем заглушку с информацией об offset
        return {
            'type': 'offset_segment',
            'original': segment,
            'offset_mm': offset,
            'normal': (0.0, 1.0),  # Заглушка нормали
            'description': f'Offset by {offset}mm'
        }
