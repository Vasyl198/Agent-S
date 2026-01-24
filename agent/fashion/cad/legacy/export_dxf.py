import ezdxf
from typing import Dict, Any
from .canonical import CanonicalCAD

def _export_contours(msp, contours, layer_name):
    """Экспорт замкнутых контуров (CAD-правильно)"""
    for contour in contours:
        if len(contour) >= 3:
            # Экспортируем как ОДНУ замкнутую полилинию
            msp.add_lwpolyline(
                contour,
                close=True,
                dxfattribs={
                    "layer": layer_name
                }
            )

def export_dxf(cad: CanonicalCAD, filepath: str, layer_setup: bool = True, export_contours: bool = True):
    """
    Экспорт канонического CAD представления в DXF формат
    
    Args:
        cad: CanonicalCAD объект для экспорта
        filepath: Путь для сохранения DXF файла
        layer_setup: Настроить слои для разных типов элементов
        export_contours: Экспортировать замкнутые контуры (CAD-правильно)
    """
    # Создаем новый DXF документ
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    
    # Настройка слоев
    if layer_setup:
        _setup_layers(doc)
    
    # ПРИОРИТЕТ: Экспорт контуров (CAD-правильно)
    if export_contours and cad.contours:
        _export_contours(msp, cad.contours, "MAIN_CONTOUR")
    
    # Экспорт линий (можно отключить флагом)
    if not export_contours or not cad.contours:
        _export_lines(msp, cad.lines, "LINES")
        _export_polylines(msp, cad.polylines, "POLYLINES")
        _export_splines(msp, cad.splines, "SPLINES")
    
    # Экспорт осей симметрии
    _export_axes(msp, cad.axes, "AXES")
    
    # Экспорт аннотаций
    _export_annotations(msp, cad.annotations, "ANNOTATIONS")
    
    # Добавляем метаданные
    _add_metadata(doc, cad.metadata)
    
    # Сохраняем файл
    doc.saveas(filepath)
    print(f"✅ DXF файл сохранен: {filepath}")
    
    # Информация о контурах
    if export_contours and cad.contours:
        print(f"   📊 Экспортировано контуров: {len(cad.contours)}")
        for i, contour in enumerate(cad.contours):
            print(f"      Контур {i+1}: {len(contour)} точек")

def _setup_layers(doc):
    """Настройка слоев для разных типов элементов"""
    
    # Слой для основных линий
    if "LINES" not in doc.layers:
        doc.layers.new("LINES", dxfattribs={
            "color": 1,  # Красный
            "lineweight": 25  # 0.25mm
        })
    
    # Слой для полилиний
    if "POLYLINES" not in doc.layers:
        doc.layers.new("POLYLINES", dxfattribs={
            "color": 2,  # Желтый
            "lineweight": 25
        })
    
    # Слой для сплайнов (кривых)
    if "SPLINES" not in doc.layers:
        doc.layers.new("SPLINES", dxfattribs={
            "color": 3,  # Зеленый
            "lineweight": 25
        })
    
    # Слой для осей симметрии
    if "AXES" not in doc.layers:
        doc.layers.new("AXES", dxfattribs={
            "color": 4,  # Голубой
            "linetype": "DASHED",
            "lineweight": 13  # 0.13mm
        })
    
    # Слой для аннотаций
    if "ANNOTATIONS" not in doc.layers:
        doc.layers.new("ANNOTATIONS", dxfattribs={
            "color": 7,  # Белый/черный
            "lineweight": 13
        })
    
    # Слой для припусков на швы (ВАЖНО)
    if "SEAM_ALLOWANCE" not in doc.layers:
        doc.layers.new("SEAM_ALLOWANCE", dxfattribs={
            "color": 6,  # Голубой
            "linetype": "CONTINUOUS",
            "lineweight": 18  # 0.18mm
        })
    
    # Слой для основного контура (CAD-правильно)
    if "MAIN_CONTOUR" not in doc.layers:
        doc.layers.new("MAIN_CONTOUR", dxfattribs={
            "color": 1,  # Красный
            "linetype": "CONTINUOUS",
            "lineweight": 30  # 0.30mm (толще основного)
        })

def _export_lines(msp, lines, layer_name):
    """Экспорт прямых линий"""
    for p1, p2 in lines:
        msp.add_line(
            p1, p2,
            dxfattribs={
                "layer": layer_name
            }
        )

def _export_polylines(msp, polylines, layer_name):
    """Экспорт полилиний"""
    for points in polylines:
        if len(points) >= 2:
            # Создаем полилинию
            msp.add_lwpolyline(
                points,
                dxfattribs={
                    "layer": layer_name,
                    "closed": False
                }
            )

def _export_splines(msp, splines, layer_name):
    """Экспорт сплайнов (кривых Безье)"""
    for spline_points in splines:
        if len(spline_points) >= 3:
            # Для ezdxf сплайны нужны контрольные точки
            # Используем fit points для гладкой кривой
            msp.add_spline(
                fit_points=spline_points,
                dxfattribs={
                    "layer": layer_name
                }
            )

def _export_axes(msp, axes, layer_name):
    """Экспорт осей симметрии"""
    for p1, p2 in axes:
        msp.add_line(
            p1, p2,
            dxfattribs={
                "layer": layer_name,
                "linetype": "DASHED"
            }
        )

def _export_annotations(msp, annotations, layer_name):
    """Экспорт аннотаций"""
    for annotation in annotations:
        text = annotation.get("text", "")
        position = annotation.get("position", (0, 0))
        annotation_type = annotation.get("type", "text")
        
        if annotation_type == "dimension":
            # Размеры - добавляем текст
            text_entity = msp.add_text(
                text,
                dxfattribs={
                    "layer": layer_name,
                    "height": 2.0,  # Высота текста
                    "style": "Standard"
                }
            )
            # Устанавливаем позицию через dxf атрибуты
            text_entity.dxf.insert = position
        else:
            # Обычный текст
            text_entity = msp.add_text(
                text,
                dxfattribs={
                    "layer": layer_name,
                    "height": 2.5,
                    "style": "Standard"
                }
            )
            # Устанавливаем позицию через dxf атрибуты
            text_entity.dxf.insert = position

def _add_metadata(doc, metadata):
    """Добавление метаданных в DXF файл"""
    if not metadata:
        return
    
    # Добавляем метаданные в секцию объектов
    msp = doc.modelspace()
    
    # Добавляем текстовую информацию о паттерне
    y_position = 0
    for key, value in metadata.items():
        if key in ["pattern_type", "construction_method", "source"]:
            text = f"{key}: {value}"
            text_entity = msp.add_text(
                text,
                dxfattribs={
                    "layer": "ANNOTATIONS",
                    "height": 1.5
                }
            )
            # Устанавливаем позицию через dxf атрибуты
            text_entity.dxf.insert = (0, y_position)
            y_position -= 3

def export_dxf_with_seam_allowance(main_cad: CanonicalCAD, seam_cad: CanonicalCAD, filepath: str):
    """
    Экспорт основного контура и припусков в один DXF файл
    
    Args:
        main_cad: Основной CAD контур
        seam_cad: CAD контур припусков
        filepath: Путь для сохранения DXF файла
    """
    # Создаем новый DXF документ
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    
    # Настройка слоев
    _setup_layers(doc)
    
    # Экспорт основного контура
    _export_lines(msp, main_cad.lines, "LINES")
    _export_polylines(msp, main_cad.polylines, "POLYLINES")
    _export_splines(msp, main_cad.splines, "SPLINES")
    _export_axes(msp, main_cad.axes, "AXES")
    _export_annotations(msp, main_cad.annotations, "ANNOTATIONS")
    
    # Экспорт припусков (ВАЖНО - отдельный слой)
    _export_seam_allowance(msp, seam_cad)
    
    # Добавляем метаданные
    _add_metadata(doc, main_cad.metadata)
    _add_seam_allowance_metadata(doc, seam_cad.metadata)
    
    # Сохраняем файл
    doc.saveas(filepath)
    print(f"✅ DXF файл с припусками сохранен: {filepath}")

def _export_seam_allowance(msp, seam_cad: CanonicalCAD):
    """Экспорт контура припусков"""
    # Экспорт линий припусков
    for p1, p2 in seam_cad.lines:
        msp.add_line(
            p1, p2,
            dxfattribs={
                "layer": "SEAM_ALLOWANCE"
            }
        )
    
    # Экспорт полилиний припусков
    for polyline in seam_cad.polylines:
        if len(polyline) >= 2:
            msp.add_lwpolyline(
                polyline,
                dxfattribs={
                    "layer": "SEAM_ALLOWANCE",
                    "closed": False
                }
            )
    
    # Экспорт аннотаций припусков
    for annotation in seam_cad.annotations:
        text = annotation.get("text", "")
        position = annotation.get("position", (0, 0))
        annotation_type = annotation.get("type", "text")
        
        if annotation_type == "seam_allowance":
            # Аннотации припусков
            text_entity = msp.add_text(
                text,
                dxfattribs={
                    "layer": "SEAM_ALLOWANCE",
                    "height": 1.8,  # Чуть меньше основного текста
                    "style": "Standard"
                }
            )
            text_entity.dxf.insert = position

def _add_seam_allowance_metadata(doc, seam_metadata):
    """Добавление метаданных о припусках в DXF файл"""
    if not seam_metadata:
        return
    
    msp = doc.modelspace()
    
    # Добавляем информацию о припусках
    seam_allowances = seam_metadata.get("seam_allowances", {})
    if seam_allowances:
        y_position = -20  # Ниже основной информации
        
        text_entity = msp.add_text(
            "SEAM ALLOWANCES:",
            dxfattribs={
                "layer": "ANNOTATIONS",
                "height": 2.0
            }
        )
        text_entity.dxf.insert = (0, y_position)
        y_position -= 3
        
        for line_name, allowance_info in seam_allowances.items():
            allowance = allowance_info.get("allowance", 0)
            line_type = allowance_info.get("type", "unknown")
            text = f"  {line_name} ({line_type}): {allowance}mm"
            
            text_entity = msp.add_text(
                text,
                dxfattribs={
                    "layer": "ANNOTATIONS",
                    "height": 1.5
                }
            )
            text_entity.dxf.insert = (0, y_position)
            y_position -= 2.5

def export_dxf_advanced(cad: CanonicalCAD, filepath: str, **options):
    """
    Расширенный экспорт DXF с дополнительными опциями
    
    Args:
        cad: CanonicalCAD объект
        filepath: Путь для сохранения
        **options: Дополнительные опции экспорта
    """
    # Опции экспорта
    include_dimensions = options.get("include_dimensions", True)
    include_grid = options.get("include_grid", False)
    scale_factor = options.get("scale_factor", 1.0)
    
    # Создаем документ
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    
    # Настройка слоев
    _setup_layers(doc)
    
    # Применяем масштабирование
    if scale_factor != 1.0:
        cad = _scale_cad(cad, scale_factor)
    
    # Экспорт элементов
    _export_lines(msp, cad.lines, "LINES")
    _export_polylines(msp, cad.polylines, "POLYLINES")
    _export_splines(msp, cad.splines, "SPLINES")
    _export_axes(msp, cad.axes, "AXES")
    
    if include_dimensions:
        _export_annotations(msp, cad.annotations, "ANNOTATIONS")
    
    if include_grid:
        _add_grid(msp, cad)
    
    _add_metadata(doc, cad.metadata)
    
    doc.saveas(filepath)
    print(f"✅ Расширенный DXF файл сохранен: {filepath}")

def _scale_cad(cad: CanonicalCAD, scale_factor: float) -> CanonicalCAD:
    """Масштабирование CAD объекта"""
    scaled = CanonicalCAD()
    
    # Масштабируем линии
    for p1, p2 in cad.lines:
        scaled_p1 = (p1[0] * scale_factor, p1[1] * scale_factor)
        scaled_p2 = (p2[0] * scale_factor, p2[1] * scale_factor)
        scaled.add_line(scaled_p1, scaled_p2)
    
    # Масштабируем полилинии
    for polyline in cad.polylines:
        scaled_polyline = [(p[0] * scale_factor, p[1] * scale_factor) for p in polyline]
        scaled.add_polyline(scaled_polyline)
    
    # Масштабируем сплайны
    for spline in cad.splines:
        scaled_spline = [(p[0] * scale_factor, p[1] * scale_factor) for p in spline]
        scaled.add_spline(scaled_spline)
    
    # Масштабируем оси
    for p1, p2 in cad.axes:
        scaled_p1 = (p1[0] * scale_factor, p1[1] * scale_factor)
        scaled_p2 = (p2[0] * scale_factor, p2[1] * scale_factor)
        scaled.add_axis(scaled_p1, scaled_p2)
    
    # Копируем аннотации и метаданные
    scaled.annotations = cad.annotations.copy()
    scaled.metadata = cad.metadata.copy()
    
    return scaled

def _add_grid(msp, cad: CanonicalCAD):
    """Добавление сетки для удобства"""
    bounds = cad.get_bounds()
    if bounds[0] == bounds[1]:
        return
    
    min_x, min_y = bounds[0]
    max_x, max_y = bounds[1]
    
    # Добавляем слой для сетки
    if "GRID" not in msp.doc.layers:
        msp.doc.layers.new("GRID", dxfattribs={
            "color": 8,  # Серый
            "linetype": "DASHED",
            "lineweight": 13
        })
    
    # Вертикальные линии сетки
    grid_spacing = 50  # 50 единиц
    x = min_x
    while x <= max_x:
        msp.add_line(
            (x, min_y), (x, max_y),
            dxfattribs={"layer": "GRID"}
        )
        x += grid_spacing
    
    # Горизонтальные линии сетки
    y = min_y
    while y <= max_y:
        msp.add_line(
            (min_x, y), (max_x, y),
            dxfattribs={"layer": "GRID"}
        )
        y += grid_spacing
