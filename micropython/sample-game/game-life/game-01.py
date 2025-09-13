"""
ライフゲーム（Conway's Game of Life） - トーラス／クラインの比較
============================================================

【機能概要】
- 2つのトポロジー（トーラス／クラインボトル）でライフゲームの進化を比較表示
- 初期状態は指定数のグライダーをランダム配置
- ダークモード（背景黒、セル緑）
- 盤面の外枠を白線で常時表示
- キー操作説明を h または ? でトグル表示（表示中は進行停止）

【実行方法】
    python game-01.py [rowsxcols] [n_gliders]
    例: python game-01.py 60x40 5
    （引数省略時は 50x50 盤面・グライダー3個）

【キー操作】
    +     : 更新速度を上げる（速く）
    -     : 更新速度を下げる（遅く）
    1〜9  : 指定世代ごとに画面更新（スキップ表示）
    Space : 一時停止／再開
    h, ?  : キー操作説明の表示／非表示（表示中は進行停止）
    q     : 終了（ウィンドウを閉じてプログラム終了）

【注意】
- macOSで日本語フォントが正しく表示されない場合は、fontdictのfontnameを適宜変更してください。
- matplotlibのバージョンや環境によっては動作が異なる場合があります。
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import os
import re

# -----------------------------
# Game of Lifeの盤面を1ステップ進める汎用関数
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

# Klein bottle用の隣接セルカウント関数
def count_neighbors_klein(grid, x, y):
    rows, cols = grid.shape
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % rows
            ny = y + dy
            # 左右端で反転
            if ny < 0:
                ny = cols - 1
                nx = (rows - nx - 1) % rows
            elif ny >= cols:
                ny = 0
                nx = (rows - nx - 1) % rows
            count += grid[nx, ny]
    return count

# Torus用の隣接セルカウント関数
def count_neighbors_torus(grid, x, y):
    rows, cols = grid.shape
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % rows
            ny = (y + dy) % cols
            count += grid[nx, ny]
    return count


# -----------------------------

# コマンドライン引数で rowsxcols, n_gliders を指定可能に
# 使い方: python game-01.py [rowsxcols] [n_gliders]
# 例: python game-01.py 60x40 5
if len(sys.argv) > 2:
    m = re.match(r'^(\d+)x(\d+)$', sys.argv[1])
    if m:
        rows = int(m.group(1))
        cols = int(m.group(2))
        try:
            n_gliders = int(sys.argv[2])
        except ValueError:
            print("Usage: python game-01.py [rowsxcols] [n_gliders]")
            sys.exit(1)
    else:
        print("Usage: python game-01.py [rowsxcols] [n_gliders]")
        sys.exit(1)
elif len(sys.argv) > 1:
    m = re.match(r'^(\d+)x(\d+)$', sys.argv[1])
    if m:
        rows = int(m.group(1))
        cols = int(m.group(2))
        n_gliders = 3
    else:
        print("Usage: python game-01.py [rowsxcols] [n_gliders]")
        sys.exit(1)
else:
    rows, cols, n_gliders = 50, 50, 3

initial = np.zeros((rows, cols), dtype=int)

glider = [(0,1),(1,2),(2,0),(2,1),(2,2)]

for _ in range(n_gliders):
    gx = random.randint(0, rows-3)
    gy = random.randint(0, cols-3)
    for dx, dy in glider:
        initial[(gx+dx)%rows, (gy+dy)%cols] = 1

torus_grid = initial.copy()
klein_grid = initial.copy()

# ヘルプテキストのアーティストをグローバルで管理
help_text_obj = None
# 可視化（アニメーション, ダークモード）
# -----------------------------
plt.style.use("dark_background")
cmap = ListedColormap(["black", "lime"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
fig.patch.set_facecolor("black")

# origin='lower' と extent を合わせて、(0,0)〜(cols,rows) を盤面座標に
im1 = ax1.imshow(torus_grid, cmap=cmap, interpolation="nearest",
                 vmin=0, vmax=1, origin="lower", extent=(0, cols, 0, rows))
ax1.set_title("Torus", color="white")
ax1.set_facecolor("black")
ax1.set_xlim(0, cols)
ax1.set_ylim(0, rows)
ax1.axis("off")

im2 = ax2.imshow(klein_grid, cmap=cmap, interpolation="nearest",
                 vmin=0, vmax=1, origin="lower", extent=(0, cols, 0, rows))
ax2.set_title("Klein bottle", color="white")
ax2.set_facecolor("black")
ax2.set_xlim(0, cols)
ax2.set_ylim(0, rows)
ax2.axis("off")

# --- 盤面の外枠（白枠）を描画 ---
frame_style = dict(fill=False, edgecolor="white", linewidth=2.5, zorder=10)
rect1 = Rectangle((0, 0), cols, rows, **frame_style)
rect2 = Rectangle((0, 0), cols, rows, **frame_style)
ax1.add_patch(rect1)
ax2.add_patch(rect2)


# -----------------------------
# アニメーション制御（方法2: タイマー作り直し）
# -----------------------------
paused = False
interval = 100  # アニメーションのタイマー間隔 (ms)
step_interval = 1  # 何世代ごとに画面を更新するか（デフォルト1）
_frame_counter = 0
ani = None

def animate(frame):
    global torus_grid, klein_grid, _frame_counter, step_interval
    if not paused:
        _frame_counter += 1
        if _frame_counter >= step_interval:
            # step_interval回分一気に進めてから表示
            for _ in range(step_interval):
                torus_grid = update(torus_grid, count_neighbors_torus)
                klein_grid = update(klein_grid, count_neighbors_klein)
            im1.set_array(torus_grid)
            im2.set_array(klein_grid)
            _frame_counter = 0
    return [im1, im2, rect1, rect2]

def start_animation():
    global ani
    ani = animation.FuncAnimation(fig, animate, interval=interval, blit=False, cache_frame_data=False)
    return ani

ani = start_animation()

# -----------------------------
# キー操作
# -----------------------------
def on_key(event):
    global ani, paused, interval, help_text_obj, step_interval, _frame_counter, torus_grid, klein_grid
    # 数字キー(1..9)でstep_intervalを変更
    if event.key in [str(i) for i in range(1, 10)]:
        # step_intervalとintervalを連動させて見た目の画面更新頻度を一定に保つ
        step_interval = int(event.key)
        base_interval = 100  # 1世代ごとの基準速度（ms）
        # step_intervalが大きいほどintervalは短く（画面更新が速く）
        interval = max(10, int(base_interval * (1.0 / step_interval)))
        if ani is not None:
            ani.event_source.stop()
            ani.event_source.interval = interval
            if not paused:
                ani.event_source.start()
        _frame_counter = 0
        print(f"画面更新を{step_interval}世代ごとに設定（interval={interval}msに自動調整）")
        return
    # h, ? でキー操作説明文をトグル表示
    if event.key in ['h', '?']:
        help_text = (
            '【キー操作一覧】\n'
            '+ : 更新速度を上げる    - : 更新速度を下げる\n'
            '1〜9 : 指定世代ごとに画面更新\n'
            'Space : 一時停止／再開\n'
            'q : 終了（ウィンドウを閉じてプログラム終了）\n'
            'h, ? : このヘルプをトグル表示'
        )
        if help_text_obj is not None:
            # 既に表示中なら消す＆アニメ再開
            help_text_obj.remove()
            help_text_obj = None
            paused = False
            fig.canvas.draw_idle()
            return
        # 非表示なら表示＆アニメ停止
        fontdict = {'fontsize': 14, 'color': 'white', 'fontname': 'Hiragino Sans'}
        help_text_obj = fig.text(
            0.5, 0.95, help_text, ha='center', va='top', fontdict=fontdict, zorder=100,
            bbox=dict(facecolor='black', alpha=0.92, boxstyle='round,pad=0.7')
        )
        paused = True
        fig.canvas.draw_idle()
        return
    if event.key == '+':
        interval = max(10, interval - 20)
        if ani is not None:
            ani.event_source.stop()
            ani.event_source.interval = interval
            if not paused:
                ani.event_source.start()
        print(f"Speed up: interval={interval} ms")
    elif event.key == '-':
        interval = interval + 20
        if ani is not None:
            ani.event_source.stop()
            ani.event_source.interval = interval
            if not paused:
                ani.event_source.start()
        print(f"Slow down: interval={interval} ms")
    elif event.key == ' ':
        paused = not paused
        if paused:
            print("Paused")
        else:
            print("Resumed")
    elif event.key == 'q':
        print("Quit.")
        plt.close(fig)
        os._exit(0)
fig.canvas.mpl_connect('key_press_event', on_key)
plt.show()
