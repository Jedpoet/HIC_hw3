import tkinter as tk
import math

points = []

in_INPUT = True


def find_distance(point1, point2):
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])


def resample(N, points):
    new_points = []
    length = sum(
        find_distance(points[i], points[i + 1]) for i in range(len(points) - 1)
    )

    if length == 0:
        return [points[0]] * N

    interval = length / (N - 1)
    accum_dist = 0.0
    new_points = [points[0]]
    pts = list(points)

    i = 0
    while i < len(pts) - 1:
        p1 = pts[i]
        p2 = pts[i + 1]
        dist = find_distance(p1, p2)
        if accum_dist + dist >= interval:
            # 線性插值比例：還需要的距離 / 這段線段長度
            t = (interval - accum_dist) / dist
            qx = p1[0] + t * (p2[0] - p1[0])
            qy = p1[1] + t * (p2[1] - p1[1])
            q = (qx, qy)

            new_points.append(q)
            # 下一次從新點 q 繼續走向 p2，累積距離歸零
            pts[i] = q
            accum_dist = 0.0
        else:
            accum_dist += dist
            i += 1


# 找質心
def centroid(points):
    x_mean = sum(p[0] for p in points) / len(points)
    y_mean = sum(p[1] for p in points) / len(points)
    return (x_mean, y_mean)


def rotate(points, com):
    angle = math.atan2(com[1] - points[0][1], com[0] - points[0][0])
    cos_val = math.cos(angle)
    sin_val = math.sin(angle)

    rotated_points = []
    for x, y in points:
        # 平移至原點
        dx = x - com[0]
        dy = y - com[1]
        # 旋轉並平移回質心
        rx = dx * cos_val - dy * sin_val + com[0]
        ry = dx * sin_val + dy * cos_val + com[1]
        rotated_points.append((rx, ry))

    return rotated_points


def resize(points, com, size=250.0):
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    w = max(max_x - min_x, 1e-6)
    h = max(max_y - min_y, 1e-6)
    pts = [(p[0] * (size / w), p[1] * (size / h)) for p in points]

    target_pt = (0.0, 0.0)
    return [(p[0] + target_pt[0] - com[0], p[1] + target_pt[1] - com[1]) for p in pts]


def recognize(N, points):
    res_points = resample(N, points)
    com = centroid(res_points)
    rot_points = rotate(res_points, com)
    new_points = resize(rot_points, 250.0)

    if in_INPUT:
        # TODO: 存檔
        pass
    else:
        # TODO: 分析
        pass

    return "3"


def on_drag(event):
    points.append((event.x, event.y))
    canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill="black")


def on_release(event):
    # 呼叫 $1 辨識函數
    result = recognize(64, points)
    result_label.config(text=f"辨識結果: {result}")
    points.clear()


def on_click():
    canvas.delete("all")


# TODO: 整理switch相關功能成輸入模板
switch_var = tk.StringVar(value="OFF")


def toggle():
    if switch_var.get() == "ON":
        switch_btn.config(text="Switch is ON", bg="lightgreen")
    else:
        switch_btn.config(text="Switch is OFF", bg="lightgray")


root = tk.Tk()
canvas = tk.Canvas(root, width=400, height=400, bg="white")
canvas.pack()
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)
result_label = tk.Label(root, text="請在上方繪製數字 (0-9)", font=("Arial", 16))
result_label.pack()
switch_btn = tk.Checkbutton(
    root,
    text="輸入模板",
    variable=switch_var,
    onvalue="ON",
    offvalue="OFF",
    indicatoron=False,  # Hides the standard checkbox box
    command=toggle,
    bg="lightgray",
    selectcolor="lightgreen",
    padx=10,
    pady=5,
)
clear_button = tk.Button(root, text="清空", command=on_click)
clear_button.pack()

root.mainloop()
