# agent/fashion/cad/visual_debug.py

import matplotlib.pyplot as plt


def debug_draw_contour(
    points,
    segments=None,
    title="CAD Contour Debug",
    save_path="output/debug_contour.png",
):
    """
    Визуальный дебаг CAD-контура.
    
    points   : [(x, y), ...] — итоговый контур (замкнутый или нет)
    segments : {
        'waist': [...],
        'side': [...],
        'hem': [...]
    }
    """

    if not points or len(points) < 2:
        raise ValueError("Недостаточно точек для визуализации")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    plt.figure(figsize=(8, 10))
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.4)

    # ===== ОСНОВНОЙ КОНТУР =====
    plt.plot(xs + [xs[0]], ys + [ys[0]], "k-", linewidth=2, label="Contour")

    # ===== ТОЧКИ С НОМЕРАМИ =====
    for i, (x, y) in enumerate(points):
        plt.scatter(x, y, color="black", zorder=5)
        plt.text(x, y, f"{i}", fontsize=9, color="black")

    # ===== НАПРАВЛЕНИЕ ОБХОДА =====
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        plt.arrow(
            x1,
            y1,
            x2 - x1,
            y2 - y1,
            head_width=1.5,
            length_includes_head=True,
            color="gray",
            alpha=0.6,
        )

    # ===== ЦЕНТР МАСС =====
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    plt.scatter(cx, cy, color="purple", s=80, label="Center")
    plt.text(cx, cy, "CENTER", fontsize=10, color="purple")

    # ===== СЕГМЕНТЫ =====
    if segments:
        if "waist" in segments:
            _draw_segment(segments["waist"], "red", "Waist")
        if "side" in segments:
            _draw_segment(segments["side"], "blue", "Side")
        if "hem" in segments:
            _draw_segment(segments["hem"], "green", "Hem")

    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()

    print(f"🎨 Визуальный дебаг сохранён: {save_path}")


def _draw_segment(points, color, label):
    if not points or len(points) < 2:
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    plt.plot(xs, ys, color=color, linewidth=3, label=label)
