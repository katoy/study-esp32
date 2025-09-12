"""
Life Game (Conway's Game of Life) - Torus vs Klein Bottle Comparison
===================================================================

■ 機能概要
- Conway のライフゲームを 2 つのトポロジー（Torus / Klein bottle）で比較
- 初期状態は指定数のグライダーをランダム配置
- ダークモード表示（背景黒、セル緑）

■ 実行方法
    python life_compare.py <number_of_gliders>

■ 実行中の操作
    +     → 更新速度を上げる（interval を短くする）
    -     → 更新速度を下げる（interval を長くする）
    Space → 一時停止 / 再開
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from matplotlib.colors import ListedColormap

# -----------------------------
# ライフゲームの更新ルール
# -----------------------------
def count_neighbors_torus(grid, x, y):
    rows, cols = grid.shape
    total = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = (x + dx) % rows, (y + dy) % cols
            total += grid[nx, ny]
    return total

def count_neighbors_klein(grid, x, y):
    rows, cols = grid.shape
    total = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % rows
            ny = y + dy
            if ny < 0:
                ny = cols - 1
                nx = rows - 1 - nx
            elif ny >= cols:
                ny = 0
                nx = rows - 1 - nx
            total += grid[nx, ny]
    return total

def update(grid, count_func):
    rows, cols = grid.shape
    new_grid = np.zeros((rows, cols), dtype=int)
    for x in range(rows):
        for y in range(cols):
            neighbors = count_func(grid, x, y)
            if grid[x, y] == 1 and neighbors in [2, 3]:
                new_grid[x, y] = 1
            elif grid[x, y] == 0 and neighbors == 3:
                new_grid[x, y] = 1
    return new_grid

# -----------------------------
# 初期化（複数グライダー配置）
# -----------------------------
rows, cols = 50, 50
initial = np.zeros((rows, cols), dtype=int)

if len(sys.argv) > 1:
    try:
        n_gliders = int(sys.argv[1])
    except ValueError:
        print("Usage: python life_compare.py <number_of_gliders>")
        sys.exit(1)
else:
    n_gliders = 3

glider = [(0,1),(1,2),(2,0),(2,1),(2,2)]

for _ in range(n_gliders):
    gx = random.randint(0, rows-3)
    gy = random.randint(0, cols-3)
    for dx, dy in glider:
        initial[(gx+dx)%rows, (gy+dy)%cols] = 1

torus_grid = initial.copy()
klein_grid = initial.copy()

# -----------------------------
# 可視化（アニメーション, ダークモード）
# -----------------------------
plt.style.use("dark_background")
cmap = ListedColormap(["black", "lime"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
fig.patch.set_facecolor("black")

im1 = ax1.imshow(torus_grid, cmap=cmap, interpolation="nearest", vmin=0, vmax=1)
ax1.set_title("Torus", color="white")
ax1.axis("off")
ax1.set_facecolor("black")

im2 = ax2.imshow(klein_grid, cmap=cmap, interpolation="nearest", vmin=0, vmax=1)
ax2.set_title("Klein bottle", color="white")
ax2.axis("off")
ax2.set_facecolor("black")

# -----------------------------
# アニメーション制御
# -----------------------------
paused = False
interval = 100  # 初期速度 (ms)
ani = None

def animate(frame):
    global torus_grid, klein_grid
    if not paused:
        torus_grid = update(torus_grid, count_neighbors_torus)
        klein_grid = update(klein_grid, count_neighbors_klein)
        im1.set_array(torus_grid)
        im2.set_array(klein_grid)
    return [im1, im2]

def start_animation():
    global ani
    ani = animation.FuncAnimation(fig, animate, interval=interval, blit=True)
    return ani

ani = start_animation()

# -----------------------------
# キー操作
# -----------------------------
def on_key(event):
    global ani, paused, interval
    if event.key == '+':
        interval = max(10, interval - 20)
        ani.event_source.stop()
        ani = start_animation()
        print(f"Speed up: interval={interval} ms")
    elif event.key == '-':
        interval = interval + 20
        ani.event_source.stop()
        ani = start_animation()
        print(f"Slow down: interval={interval} ms")
    elif event.key == ' ':
        paused = not paused
        if paused:
            print("Paused")
        else:
            print("Resumed")

fig.canvas.mpl_connect("key_press_event", on_key)

plt.show()
