import tkinter as tk
from tkinter import messagebox
import math
import json
import os

N_POINTS = 64
SQUARE_SIZE = 250.0
CANVAS_SIZE = 400
TEMPLATE_FILE = "templates.json"

points = []


# ---------------------------------------------------------------------------
# 模板存取
# 格式: { "label": [ [[x, y], ...], [[x, y], ...] ], ... }  每個標籤可有多個模板
# ---------------------------------------------------------------------------
def save_templates(templates, filepath=TEMPLATE_FILE):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)


def load_templates(filepath=TEMPLATE_FILE):
    if not os.path.exists(filepath):
        save_templates({}, filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 相容舊格式（label -> 單一點列）
    for k, v in list(data.items()):
        if v and isinstance(v[0][0], (int, float)):
            data[k] = [v]
    return data


# ---------------------------------------------------------------------------
# $1 前處理
# ---------------------------------------------------------------------------
def find_distance(point1, point2):
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])


def resample(N, points):
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
        if dist > 0 and accum_dist + dist >= interval:
            # 線性插值比例：還需要的距離 / 這段線段長度
            t = (interval - accum_dist) / dist
            q = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
            new_points.append(q)
            # 下一次從新點 q 繼續走向 p2，累積距離歸零
            pts[i] = q
            accum_dist = 0.0
        else:
            accum_dist += dist
            i += 1

    # 浮點誤差可能少一點，補上最後一點
    while len(new_points) < N:
        new_points.append(points[-1])
    return new_points[:N]


# 找質心
def centroid(points):
    x_mean = sum(p[0] for p in points) / len(points)
    y_mean = sum(p[1] for p in points) / len(points)
    return (x_mean, y_mean)


def rotate_by(points, angle, com):
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


def rotate(points, com):
    # indicative angle：第一點 -> 質心 的角度，旋轉 -angle 使其歸零
    angle = math.atan2(com[1] - points[0][1], com[0] - points[0][0])
    return rotate_by(points, -angle, com)


def resize(points, size=SQUARE_SIZE):
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    w = max(max_x - min_x, 1e-6)
    h = max(max_y - min_y, 1e-6)
    return [(p[0] * (size / w), p[1] * (size / h)) for p in points]


def translate_to_origin(points):
    cx, cy = centroid(points)
    return [(p[0] - cx, p[1] - cy) for p in points]


def preprocess(points, N=N_POINTS):
    res_points = resample(N, points)
    rot_points = rotate(res_points, centroid(res_points))
    scaled = resize(rot_points, SQUARE_SIZE)
    return translate_to_origin(scaled)


# ---------------------------------------------------------------------------
# Pattern matching（留給你自己實作）
# ---------------------------------------------------------------------------
def match(candidate, templates):
    """
    candidate : 經過 preprocess 的點列 [(x, y), ...]
    templates : { label: [ [[x, y], ...], ... ] }
    回傳 (best_label, score)；尚未實作時回傳 (None, 0.0)
    """
    # TODO: 實作 $1 的 pattern matching
    #   (例如 path distance + golden section search 找最佳角度，再換算 score)
    return (None, 0.0)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def draw_points(cv, pts, size=CANVAS_SIZE, color="black", r=2):
    """把以原點為中心的點列畫在畫布中央"""
    off = size / 2
    scale = (size * 0.8) / (SQUARE_SIZE * 1.2)  # 讓 250 的方框塞得進畫布
    for i, (x, y) in enumerate(pts):
        px, py = x * scale + off, y * scale + off
        fill = "red" if i == 0 else color  # 起點標紅
        rr = r + 2 if i == 0 else r
        cv.create_oval(px - rr, py - rr, px + rr, py + rr, fill=fill, outline=fill)


def is_record_mode():
    return mode_var.get() == "record"


def on_mode_change():
    canvas.delete("all")
    points.clear()
    if is_record_mode():
        label_entry.config(state="normal")
        label_entry.focus_set()
        status_label.config(text="錄製模式：先輸入標籤，再在畫布上畫手勢")
    else:
        label_entry.config(state="disabled")
        status_label.config(text="辨識模式：請在上方繪製手勢")


def on_press(event):
    canvas.delete("all")
    points.clear()
    points.append((event.x, event.y))


def on_drag(event):
    points.append((event.x, event.y))
    canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill="black")


def on_release(event):
    if len(points) < 5:
        status_label.config(text="筆畫太短，請重畫")
        points.clear()
        return

    if is_record_mode():
        label = label_var.get().strip()
        if not label:
            messagebox.showwarning("缺少標籤", "請先輸入標籤再畫手勢")
            canvas.delete("all")
            points.clear()
            return

    new_points = preprocess(points)
    canvas.delete("all")
    draw_points(canvas, new_points)

    data = load_templates()
    if is_record_mode():
        data.setdefault(label, []).append([list(p) for p in new_points])
        save_templates(data)
        status_label.config(
            text=f"已存入「{label}」（共 {len(data[label])} 個模板）"
        )
    else:
        if not data:
            status_label.config(text="沒有手勢模板，請先切到錄製模式")
        else:
            best, score = match(new_points, data)
            if best is None:
                status_label.config(text="辨識結果: （matching 尚未實作）")
            else:
                status_label.config(text=f"辨識結果: {best}  (score {score:.2f})")
    points.clear()


def on_clear():
    canvas.delete("all")
    points.clear()


def open_template_viewer():
    win = tk.Toplevel(root)
    win.title("已儲存的手勢模板")

    left = tk.Frame(win)
    left.pack(side="left", fill="y", padx=5, pady=5)
    listbox = tk.Listbox(left, width=24, height=20)
    listbox.pack(fill="y", expand=True)

    preview = tk.Canvas(win, width=300, height=300, bg="white")
    preview.pack(side="right", padx=5, pady=5)

    entries = []  # (label, index)

    def refresh():
        listbox.delete(0, "end")
        entries.clear()
        data = load_templates()
        for label in sorted(data):
            for idx in range(len(data[label])):
                entries.append((label, idx))
                listbox.insert("end", f"{label}  #{idx + 1}")
        preview.delete("all")

    def on_select(_event=None):
        sel = listbox.curselection()
        if not sel:
            return
        label, idx = entries[sel[0]]
        preview.delete("all")
        draw_points(preview, load_templates()[label][idx], size=300)
        preview.create_text(10, 10, anchor="nw", text=f"{label} #{idx + 1}")

    def on_delete():
        sel = listbox.curselection()
        if not sel:
            return
        label, idx = entries[sel[0]]
        if not messagebox.askyesno("刪除", f"刪除「{label} #{idx + 1}」？", parent=win):
            return
        data = load_templates()
        del data[label][idx]
        if not data[label]:
            del data[label]
        save_templates(data)
        refresh()

    listbox.bind("<<ListboxSelect>>", on_select)
    btns = tk.Frame(left)
    btns.pack(fill="x", pady=4)
    tk.Button(btns, text="重新整理", command=refresh).pack(side="left", expand=True, fill="x")
    tk.Button(btns, text="刪除", command=on_delete).pack(side="left", expand=True, fill="x")
    refresh()


root = tk.Tk()
root.title("$1 Unistroke Recognizer")

# 模式選擇（預設辨識）
top = tk.Frame(root)
top.pack(fill="x", padx=8, pady=6)
mode_var = tk.StringVar(value="recognize")
tk.Radiobutton(top, text="辨識", variable=mode_var, value="recognize",
               command=on_mode_change, indicatoron=False, padx=10, pady=4,
               selectcolor="lightblue").pack(side="left")
tk.Radiobutton(top, text="錄製模板", variable=mode_var, value="record",
               command=on_mode_change, indicatoron=False, padx=10, pady=4,
               selectcolor="lightgreen").pack(side="left", padx=(4, 12))
tk.Label(top, text="標籤:").pack(side="left")
label_var = tk.StringVar()
label_entry = tk.Entry(top, textvariable=label_var, width=12, state="disabled")
label_entry.pack(side="left")

canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
canvas.pack(padx=8)
canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

status_label = tk.Label(root, text="", font=("Arial", 14))
status_label.pack(pady=4)

bottom = tk.Frame(root)
bottom.pack(pady=(0, 8))
tk.Button(bottom, text="清空", command=on_clear, width=10).pack(side="left", padx=4)
tk.Button(bottom, text="查看模板", command=open_template_viewer, width=10).pack(side="left", padx=4)

on_mode_change()
root.mainloop()
