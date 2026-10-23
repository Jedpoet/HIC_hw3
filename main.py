import tkinter as tk

points = []


def recognize():
    return "3"


def on_drag(event):
    points.append((event.x, event.y))
    canvas.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill="black")


def on_release(event):
    # 呼叫 $1 辨識函數
    # result = recognize(points, N=64)
    result = recognize()
    result_label.config(text=f"辨識結果: {result}")
    points.clear()


def on_click():
    canvas.delete("all")


root = tk.Tk()
canvas = tk.Canvas(root, width=400, height=400, bg="white")
canvas.pack()
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)
result_label = tk.Label(root, text="請在上方繪製數字 (0-9)", font=("Arial", 16))
result_label.pack()
clear_button = tk.Button(root, text="清空", command=on_click)
clear_button.pack()
root.mainloop()
