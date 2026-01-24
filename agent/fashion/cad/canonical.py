from typing import Dict, List, Tuple

Point = Tuple[float, float]
Segment = Tuple[Point, Point]

class CanonicalCAD:
    """
    Каноническое CAD представление паттерна
    
    Приводит любой паттерн (алгоритмический или датасетный) к единому CAD-формату
    для последующего экспорта в DXF, Seamly2D и другие CAD системы
    """
    
    def __init__(self):
        self.lines: List[Tuple[Point, Point]] = []          # Прямые линии
        self.polylines: List[List[Point]] = []              # Полилинии
        self.splines: List[List[Point]] = []                # Сплайны (кривые)
        self.axes: List[Tuple[Point, Point]] = []           # Оси симметрии
        self.annotations: List[Dict] = []                  # Аннотации и размеры
        self.contours: List[List[Point]] = []               # Замкнутые контуры (CAD-правильно)
        self.metadata: Dict = {}                            # Метаданные
        
    def add_line(self, p1: Point, p2: Point):
        """Добавить прямую линию"""
        self.lines.append((p1, p2))
    
    def add_polyline(self, points: List[Point]):
        """Добавить полилинию"""
        if len(points) >= 2:
            self.polylines.append(points)
    
    def add_contour(self, points: List[Point]):
        """Добавить замкнутый контур"""
        if len(points) >= 3:
            # Убеждаемся что контур замкнут
            if not self._is_close(points[0], points[-1], 0.1):
                points = points + [points[0]]
            self.contours.append(points)
    
    def _is_close(self, p1: Point, p2: Point, tol: float = 0.1) -> bool:
        """Проверка близости точек"""
        return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol
    
    def add_spline(self, control_points: List[Point]):
        """Добавить сплайн (кривую Безье)"""
        if len(control_points) >= 2:
            self.splines.append(control_points)
    
    def add_axis(self, p1: Point, p2: Point):
        """Добавить ось симметрии"""
        self.axes.append((p1, p2))
    
    def add_annotation(self, text: str, position: Point, annotation_type: str = "text"):
        """Добавить аннотацию"""
        self.annotations.append({
            "text": text,
            "position": position,
            "type": annotation_type
        })
    
    def get_bounds(self) -> Tuple[Point, Point]:
        """Получить границы паттерна (min_point, max_point)"""
        all_points = []
        
        # Собираем все точки
        for line in self.lines:
            all_points.extend(line)
        for polyline in self.polylines:
            all_points.extend(polyline)
        for spline in self.splines:
            all_points.extend(spline)
        for axis in self.axes:
            all_points.extend(axis)
        
        if not all_points:
            return ((0.0, 0.0), (0.0, 0.0))
        
        min_x = min(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_x = max(p[0] for p in all_points)
        max_y = max(p[1] for p in all_points)
        
        return ((min_x, min_y), (max_x, max_y))
    
    def get_statistics(self) -> Dict:
        """Получить статистику паттерна"""
        bounds = self.get_bounds()
        width = bounds[1][0] - bounds[0][0]
        height = bounds[1][1] - bounds[0][1]
        
        return {
            "total_elements": len(self.lines) + len(self.polylines) + len(self.splines) + len(self.axes),
            "lines": len(self.lines),
            "polylines": len(self.polylines),
            "splines": len(self.splines),
            "axes": len(self.axes),
            "annotations": len(self.annotations),
            "bounds": bounds,
            "width": width,
            "height": height,
            "metadata": self.metadata
        }
    
    def validate(self) -> List[str]:
        """Валидация CAD представления"""
        issues = []
        
        # Проверяем наличие элементов
        if not self.lines and not self.polylines and not self.splines:
            issues.append("No geometric elements found")
        
        # Проверяем метаданные
        if not self.metadata:
            issues.append("No metadata provided")
        
        # Проверяем границы
        bounds = self.get_bounds()
        if bounds[0][0] == bounds[1][0] and bounds[0][1] == bounds[1][1]:
            issues.append("Invalid bounds (all points at same location)")
        
        return issues
    
    def __repr__(self):
        stats = self.get_statistics()
        return f"CanonicalCAD(lines={stats['lines']}, splines={stats['splines']}, axes={stats['axes']})"
