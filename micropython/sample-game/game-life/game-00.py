import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# -----------------------------
# ライフゲームの更新ルール
# -----------------------------
def count_neighbors_torus(grid, x, y):
    """トーラス境界条件の近傍カウント"""
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
    """クライン壺境界条件の近傍カウント"""
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
                nx = rows - 1 - nx  # 左右端で反転
            elif ny >= cols:
                ny = 0
                nx = rows - 1 - nx
            total += grid[nx, ny]
    return total

def update(grid, count_func):
    """1ステップ進める"""
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
# 初期化（グライダー配置）
# -----------------------------
rows, cols = 30, 30
initial = np.zeros((rows, cols), dtype=int)

# グライダーを左上に配置
glider = [(0,1),(1,2),(2,0),(2,1),(2,2)]
for x,y in glider:
    initial[x,y] = 1

torus_grid = initial.copy()
klein_grid = initial.copy()

# -----------------------------
# 可視化（アニメーション）
# -----------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

im1 = ax1.imshow(torus_grid, cmap="binary", interpolation="nearest")
ax1.set_title("Torus")
ax1.axis("off")

im2 = ax2.imshow(klein_grid, cmap="binary", interpolation="nearest")
ax2.set_title("Klein bottle")
ax2.axis("off")

def animate(frame):
    global torus_grid, klein_grid
    torus_grid = update(torus_grid, count_neighbors_torus)
    klein_grid = update(klein_grid, count_neighbors_klein)
    im1.set_array(torus_grid)
    im2.set_array(klein_grid)
    return [im1, im2]

ani = animation.FuncAnimation(fig, animate, frames=200, interval=200, blit=True)
plt.show()
