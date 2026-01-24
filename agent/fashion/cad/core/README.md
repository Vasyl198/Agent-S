# 🏗️ CAD CORE - ЕДИНСТВЕННЫЙ КОНСТРУКТОР

## 🎯 ЦЕЛЬ ФАЗЫ

Сделать так, чтобы:
- геометрия существовала в одном месте
- winstuf не мог случайно создать "вторую реальность"
- все DXF = 100% предсказуемые

## 🔴 ПРОБЛЕМА №1 (КЛЮЧЕВАЯ)

Сейчас геометрия:
- создаётся в PatternMaker
- модифицируется в contour_builder
- "лечится" в proper_dxf_exporter
- валидируется в validate_dxf.py

❌ Это архитектурная катастрофа при росте проекта.

## ✅ РЕШЕНИЕ: КАНОНИЧЕСКИЙ CAD CORE

### 1️⃣ ЕДИНСТВЕННЫЕ БАЗОВЫЕ КЛАССЫ

**📁 `agent/fashion/cad/core/geometry.py`**

ТОЛЬКО ЗДЕСЬ разрешено:
- Point
- Segment
- Arc (bulge)
- Contour

🚫 НИГДЕ в проекте больше нельзя создавать свои точки

### 2️⃣ ЕДИНСТВЕННЫЙ МОДУЛЬ КОНТУРА

**📁 `agent/fashion/cad/core/contour.py`**

Сюда сливаются:
- contour_builder.py ❌
- куски proper_dxf_exporter ❌
- логика замыкания ✅

Функции:
- сортировка сегментов
- проверка замыкания
- устранение разрывов
- нормализация направления (CW / CCW)

📌 DXF-экспортёр НЕ ИМЕЕТ ПРАВА это делать

### 3️⃣ ВАЛИДАЦИЯ = ЧАСТЬ ЯДРА (НЕ DXF)

**📁 `agent/fashion/cad/core/validation.py`**

Сюда переносим ВСЁ из:
- validate_dxf.py
- проверки из exporters

Проверки:
- разрывы
- самопересечения
- дубли точек
- нулевые сегменты
- инвертированные bulge

📛 Если validation падает → DXF НЕ создаётся

### 4️⃣ CURVES = НЕ ЭКСПОРТ, А МАТЕМАТИКА

**📁 `agent/fashion/cad/core/curves.py`**

Сюда:
- curve_reconstruction.py
- сглаживание
- аппроксимация
- spline → bulge

📌 Экспортёры НЕ ВОССТАНАВЛИВАЮТ КРИВЫЕ

## 🟡 ЧТО ДЕЛАЕМ С PatternMaker (важно)

❌ ЗАПРЕЩАЕМ:
- создавать сегменты
- соединять контуры
- думать о DXF

✅ PatternMaker теперь:
- считает ТОЛЬКО точки
- возвращает семантические точки

```python
return {
    "points": {
        "WAIST_CENTER": Point(...),
        "HEM_LEFT": Point(...)
    }
}
```

📌 Дальше CAD CORE решает, что с этим делать.

## 🔵 EXPORTERS — СТАНОВЯТСЯ ТУПЫМИ

**📁 `agent/fashion/cad/exporters/dxf.py`**

Разрешено:
- взять готовый Contour
- сериализовать в DXF

🚫 Запрещено:
- исправлять
- сортировать
- замыкать
- "лечить"

## 🧠 ПРАВИЛО ДЛЯ winstuf (КРИТИЧЕСКОЕ)

❗ winstuf НЕ ИМЕЕТ ПРАВА:
- добавлять геометрию вне cad/core
- "быстро чинить DXF"
- создавать Point/Segment в экспортёрах

Если что-то не работает → тест → cad/core

## 📍 РЕЗУЛЬТАТ ФАЗЫ 1

После этой фазы:
- ❌ нет 2–3 конструкторов
- ✅ есть ОДИН CAD CORE
- ✅ DXF всегда предсказуем
- ✅ можно безопасно подключать ML
- ✅ можно обучать агента на геометрии

## 🏗️ СТРУКТУРА CAD CORE

```
agent/fashion/cad/
├── core/                          # 🏗️ ЯДРО CAD СИСТЕМЫ
│   ├── __init__.py               # Экспорт классов
│   ├── geometry.py               # 📍 Point, 📏 Segment, 🌙 Arc, 🔲 Contour
│   ├── contour.py               # 🔧 ContourBuilder, ContourProcessor
│   ├── validation.py            # 🔍 GeometryValidator, ValidationError
│   ├── curves.py                # 🌊 CurveProcessor
│   └── README.md                # 📚 Документация
├── exporters/                     # 🔵 ТУПЫЕ ЭКСПОРТЁРЫ
│   ├── __init__.py               # Экспорт классов
│   └── dxf.py                   # 📤 DXFExporter, SemanticDXFExporter
└── [старые файлы]               # 🗑️ Будут удалены
```

## 🎯 ЕДИНСТВЕННЫЕ ТОЧКИ ВХОДА

### Геометрия:
```python
from agent.fashion.cad.core import Point, Segment, Contour

# Создание - ТОЛЬКО ЧЕРЕЗ CAD CORE
point = create_point(x, y, role)
segment = create_segment(start, end, role, bulge)
contour = create_contour(segments, closed)
```

### Обработка контуров:
```python
from agent.fashion.cad.core import process_contour, merge_contours

# Обработка - ТОЛЬКО ЧЕРЕЗ CAD CORE
processed = process_contour(contour, clockwise=True)
merged = merge_contours([contour1, contour2])
```

### Валидация:
```python
from agent.fashion.cad.core import validate_geometry, is_valid_geometry

# Валидация - ТОЛЬКО ЧЕРЕЗ CAD CORE
errors = validate_geometry(contour)
valid = is_valid_geometry(contour)
```

### Экспорт:
```python
from agent.fashion.cad.exporters import export_contour_to_dxf

# Экспорт - ТОЛЬКО ЧЕРЕЗ ТУПЫЕ ЭКСПОРТЁРЫ
result = export_contour_to_dxf(contour, "output.dxf")
```

## 🚫 ГЛОБАЛЬНЫЕ ЗАПРЕТЫ

```python
# ❌ ЗАПРЕЩЕНО В ЛЮБЫХ ДРУГИХ МОДУЛЯХ:
class MyPoint:  # ❌ Свой класс точки
    pass

class MySegment:  # ❌ Свой класс сегмента
    pass

def create_my_geometry():  # ❌ Своя геометрия
    pass

# ✅ РАЗРЕШЕНО ТОЛЬКО:
from agent.fashion.cad.core import Point, Segment, Contour
```

## 🔐 ЗАЩИТА ОТ "ВТОРОЙ РЕАЛЬНОСТИ"

Система включает:
- 🚫 Глобальные запреты на создание геометрии
- 🔍 Валидацию на каждом шаге
- 📛 Отказ в экспорте при невалидной геометрии
- 🧠 Единые точки входа для всех операций

## 🎉 ИТОГ

**CAD Core = ЕДИНСТВЕННЫЙ КОНСТРУКТОР**
- 📍 Все геометрические классы в одном месте
- 🔧 Все операции обработки в одном месте
- 🔍 Все проверки в одном месте
- 📤 Все экспортёры тупые и предсказуемые
- 🚫 Никакой "второй реальности"

**Результат:**
- ✅ Архитектурная целостность
- ✅ Предсказуемость DXF
- ✅ Безопасность для ML
- ✅ Масштабируемость
