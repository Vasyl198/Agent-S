import matplotlib.pyplot as plt

def plot_contour(points: list, title="Contour Debug"):
    """
    points: [(x, y), (x, y), ...] — В ПОРЯДКЕ ОБХОДА
    """

    if len(points) < 3:
        raise ValueError("Contour must have at least 3 points")

    xs = [p[0] for p in points] + [points[0][0]]
    ys = [p[1] for p in points] + [points[0][1]]

    plt.figure(figsize=(6, 10))
    plt.plot(xs, ys, marker="o")

    for i, (x, y) in enumerate(points):
        plt.text(x, y, f"{i}", fontsize=9)

    plt.title(title)
    plt.axis("equal")
    plt.grid(True)
    plt.show()
