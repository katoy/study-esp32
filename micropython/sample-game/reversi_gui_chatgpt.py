#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversi (Othello) GUI for macOS (and cross‑platform).
- マウスで着手（あなた=黒）、AI=白。
- ChatGPT(API)が使えない/使わない場合は完全ローカルAIで動作。

環境変数:
  OPENAI_API_KEY   : APIキー（省略可）
  OPENAI_MODEL     : 既定 'gpt-5'
  OTHELLO_OFFLINE  : '1' でオンライン問い合わせを無効化（強制オフライン）
"""
from __future__ import annotations
import os
import json
import threading
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

# --- OpenAI の有無を判定（無ければオフライン扱い） ---
try:
    from openai import OpenAI  # pip install openai
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore

import tkinter as tk
from tkinter import messagebox

# ----------------------------- Game constants ------------------------------
SIZE = 8
EMPTY, BLACK, WHITE = 0, 1, -1
DIRS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1)
]

COORD_A = "ABCDEFGH"

# A classic positional weight matrix (corners > edges > center; avoid X-squares early)
WEIGHTS = [
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
]

@dataclass
class MoveResult:
    board: List[List[int]]
    flips: List[Tuple[int, int]]

# ----------------------------- Game logic ----------------------------------

def initial_board() -> List[List[int]]:
    b = [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]
    b[3][3] = WHITE
    b[3][4] = BLACK
    b[4][3] = BLACK
    b[4][4] = WHITE
    return b

def on_board(x: int, y: int) -> bool:
    return 0 <= x < SIZE and 0 <= y < SIZE

def opponent(c: int) -> int:
    return -c

def capture_line(board: List[List[int]], x: int, y: int, dx: int, dy: int, color: int) -> List[Tuple[int, int]]:
    # returns list of opponent discs to flip if placing at (x,y) along dir (dx,dy)
    line = []
    i, j = x + dx, y + dy
    while on_board(i, j) and board[j][i] == opponent(color):
        line.append((i, j))
        i += dx
        j += dy
    if line and on_board(i, j) and board[j][i] == color:
        return line
    return []

def legal_flips(board: List[List[int]], x: int, y: int, color: int) -> List[Tuple[int, int]]:
    if not on_board(x, y) or board[y][x] != EMPTY:
        return []
    flips: List[Tuple[int, int]] = []
    for dx, dy in DIRS:
        flips.extend(capture_line(board, x, y, dx, dy, color))
    return flips

def legal_moves(board: List[List[int]], color: int) -> List[Tuple[int, int]]:
    moves: List[Tuple[int, int]] = []
    for y in range(SIZE):
        for x in range(SIZE):
            if legal_flips(board, x, y, color):
                moves.append((x, y))
    return moves

def apply_move(board: List[List[int]], x: int, y: int, color: int) -> Optional[MoveResult]:
    flips = legal_flips(board, x, y, color)
    if not flips:
        return None
    nb = [row[:] for row in board]
    nb[y][x] = color
    for (i, j) in flips:
        nb[j][i] = color
    return MoveResult(board=nb, flips=flips)

def score(board: List[List[int]]) -> Tuple[int, int]:
    b = sum(1 for row in board for v in row if v == BLACK)
    w = sum(1 for row in board for v in row if v == WHITE)
    return b, w

def game_over(board: List[List[int]]) -> bool:
    return not legal_moves(board, BLACK) and not legal_moves(board, WHITE)

# Heuristic evaluation used for fallback AI and tie-breakers

def evaluate(board: List[List[int]], color: int) -> int:
    # positional weights + mobility heuristic
    pos = 0
    for y in range(SIZE):
        for x in range(SIZE):
            if board[y][x] == color:
                pos += WEIGHTS[y][x]
            elif board[y][x] == opponent(color):
                pos -= WEIGHTS[y][x]
    my_moves = len(legal_moves(board, color))
    opp_moves = len(legal_moves(board, opponent(color)))
    mobility = 5 * (my_moves - opp_moves)
    return pos + mobility

# Simple 1-ply greedy fallback

def best_legal_move(board: List[List[int]], color: int) -> Optional[Tuple[int, int]]:
    moves = legal_moves(board, color)
    if not moves:
        return None
    best = None
    best_val = -10**9
    for (x, y) in moves:
        res = apply_move(board, x, y, color)
        if not res:
            continue
        val = evaluate(res.board, color)
        if val > best_val:
            best_val = val
            best = (x, y)
    return best

# ------------------------ OpenAI (ChatGPT) integration ----------------------

class ChatGPTOthello:
    def __init__(self):
        # ChatGPT（OpenAI API）が利用可能かどうかをAPIキーのみで判定し、OTHELLO_OFFLINEは無視
        self.enabled = _OPENAI_AVAILABLE and bool(os.environ.get("OPENAI_API_KEY"))
        self.model = os.environ.get("OPENAI_MODEL", "gpt-5")
        self.client = OpenAI() if (self.enabled and OpenAI is not None) else None

    @staticmethod
    def to_notation(x: int, y: int) -> str:
        return f"{COORD_A[x]}{y+1}"

    # クラス変数として定義
    all_coords = [(x, y) for y in range(SIZE) for x in range(SIZE)]  # for small helpers

    @staticmethod
    def from_notation(s: str) -> Optional[Tuple[int, int]]:
        s = s.strip().upper()
        if s == "PASS":
            return None
        if len(s) != 2:
            return None
        col, row = s[0], s[1]
        if col not in COORD_A or row < '1' or row > '8':
            return None
        x = COORD_A.index(col)
        y = int(row) - 1
        return (x, y)

    @staticmethod
    def board_as_strings(board: List[List[int]]) -> List[str]:
        # '.' empty, 'B' black, 'W' white; row 8 at top for readability
        lines = []
        for y in range(SIZE-1, -1, -1):  # 7..0 so that display is 8..1 top->bottom
            row = ''.join('B' if v == BLACK else 'W' if v == WHITE else '.' for v in board[y])
            lines.append(row)
        return lines

    @staticmethod
    def detect_phase(board: List[List[int]]) -> str:
        empties = sum(1 for row in board for v in row if v == EMPTY)
        if empties > 40:
            return "序盤"
        elif empties > 15:
            return "中盤"
        else:
            return "終盤"

    def _local_candidates(self, board, color, k=3):
        moves = legal_moves(board, color)
        scored = []
        for (x, y) in moves:
            res = apply_move(board, x, y, color)
            if not res:
                continue
            val = evaluate(res.board, color)
            # 簡易ノート
            note = []
            if (x, y) in [(0,0),(0,7),(7,0),(7,7)]:
                note.append("角")
            elif x in (0,7) or y in (0,7):
                note.append("辺")
            scored.append((val, (x, y), " / ".join(note)))
        scored.sort(reverse=True, key=lambda t: t[0])
        cands = [{"move": self.to_notation(x, y), "score": val, "note": note} for val, (x, y), note in scored[:k]]
        analysis = "（ローカルAI）位置評価＋可動性を考慮した1手先グリーディ。角・辺をやや優遇。"
        return cands, analysis

    def build_prompt(self, board: List[List[int]], color: int) -> Dict[str, Any]:
        legal = legal_moves(board, color)
        legal_not = [self.to_notation(x, y) for (x, y) in legal]
        b_lines = self.board_as_strings(board)
        phase = self.detect_phase(board)
        who = "白(White)" if color == WHITE else "黒(Black)"
        instructions = (
            "あなたはオセロ(Reversi)のコーチ兼対戦相手です。\n"
            "与えられた盤面と合法手一覧から、あなた(\"{who}\")の着手を1つ選び、"
            "JSONだけを返してください。違法手は絶対に選ばないでください。\n"
            "評価では隅(角)・辺・可動性・パリティ・相手にX/Squareを打たせる筋などを考慮し、"
            "日本語で簡潔に解説してください。合法手が無い場合は move に 'PASS' を設定。".format(who=who)
        )
        schema = {
            "name": "ReversiAdvice",
            "schema": {
                "type": "object",
                "properties": {
                    "move": {"type": "string", "pattern": "^(?:[A-H][1-8]|PASS)$"},
                    "candidates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "move": {"type": "string", "pattern": "^(?:[A-H][1-8]|PASS)$"},
                                "score": {"type": "number"},
                                "note": {"type": "string"}
                            },
                            "required": ["move"],
                            "additionalProperties": False
                        },
                        "maxItems": 5
                    },
                    "analysis": {"type": "string"},
                    "lookahead": {"type": "string"},
                    "win_prob": {"type": "number"}
                },
                "required": ["move"],
                "additionalProperties": False
            }
        }
        user_payload = {
            "role": "user",
            "content": (
                "盤面(上から8段目→1段目の順で8行):\n" + "\n".join(b_lines) + "\n\n"+
                f"手番: {who}\n"+
                f"局面フェーズ: {phase}\n"+
                f"合法手一覧: {legal_not if legal_not else '[]'}\n"+
                "出力は必ず JSON のみ。候補手は最大3つ程度で十分です。\n"
            )
        }
        return {
            "instructions": instructions,
            "input": [user_payload],
            "response_format": {"type": "json_schema", "json_schema": schema},
            "temperature": 0.2,
            "max_output_tokens": 500,
        }

    def choose(self, board: List[List[int]], color: int) -> Dict[str, Any]:
        """Return dict with keys: move(str A1..H8 or 'PASS'), candidates(list), analysis(str), source(str)."""
        legal_not = {self.to_notation(x, y) for (x, y) in legal_moves(board, color)}

        # --- 完全ローカル ---
        if not self.enabled or self.client is None:
            mv_xy = best_legal_move(board, color)
            if mv_xy is None:
                return {"move": "PASS", "candidates": [], "analysis": "(ローカルAI) 合法手なし。", "source": "local"}
            cands, analysis = self._local_candidates(board, color, k=3)
            return {"move": self.to_notation(*mv_xy), "candidates": cands, "analysis": analysis, "source": "local"}

        # --- オンライン（API） ---
        try:
            prompt = self.build_prompt(board, color)
            messages = [
                {"role": "system", "content": prompt["instructions"]},
                *prompt["input"]
            ]
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=prompt.get("temperature", 0.2),
                max_tokens=prompt.get("max_output_tokens", 500),
            )
            text = resp.choices[0].message.content
            data = json.loads(text)
            move = str(data.get("move", "")).upper()
            cand = data.get("candidates", []) or []
            analysis = data.get("analysis", "")

            if move not in legal_not:
                legal_c = next((c for c in cand if str(c.get("move", "")).upper() in legal_not), None)
                if legal_c:
                    move = str(legal_c.get("move")).upper()
                else:
                    mv_xy = best_legal_move(board, color)
                    move = self.to_notation(*mv_xy) if mv_xy else "PASS"
            return {"move": move, "candidates": cand, "analysis": analysis, "source": "chatgpt"}

        except Exception as e:
            # 429等が出たら以後はローカル固定に切替
            if "insufficient_quota" in str(e) or "exceeded your current quota" in str(e):
                self.enabled = False
            mv_xy = best_legal_move(board, color)
            if mv_xy is None:
                return {"move": "PASS", "candidates": [], "analysis": f"(API失敗→ローカル) {e}", "source": "local"}
            cands, _ = self._local_candidates(board, color, k=3)
            return {"move": self.to_notation(*mv_xy), "candidates": cands, "analysis": f"(API失敗→ローカル) {e}", "source": "local"}

# ------------------------------ GUI layer ----------------------------------

CELL = 72  # pixel per cell
PAD = 24
BOARD_SIZE = SIZE * CELL
STONE_R = int(CELL * 0.38)

class ReversiGUI:
    def after_user_move(self):
        print("[after_user_move] called")
        if game_over(self.board):
            print("[after_user_move] game_over detected")
            self.finish_game()
            return
        # If AI has no move, pass back
        if not legal_moves(self.board, WHITE):
            print("[after_user_move] AI has no legal moves (pass)")
            self.update_advice("白(AI)はパスします。あなたの手番です。")
            self.turn = BLACK
            self.draw()
            self.update_status()
            if game_over(self.board):
                print("[after_user_move] game_over detected after pass")
                self.finish_game()
            return
        # otherwise, call AI in background
        print("[after_user_move] start AI thinking thread")
        self.busy = True
        self.update_advice("AI思考中…")
        import threading
        threading.Thread(target=self.ai_worker, daemon=True).start()
    def __init__(self, root: tk.Tk):
        print("[ReversiGUI.__init__] called")
        self.root = root
        self.root.title("Reversi (あなた=黒 / AI=白)")
        self.board: List[List[int]] = initial_board()
        self.turn = BLACK  # user starts (黒)
        self.ai = ChatGPTOthello()
        self.busy = False
        self._drawing = False  # draw()再入防止フラグ
        self._canvas_ids = []  # 描画IDリスト

        self.canvas = tk.Canvas(root, width=BOARD_SIZE + PAD*2, height=BOARD_SIZE + PAD*2, bg="#2c7d2c")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Button-1>", self.on_click)

        side = tk.Frame(root)
        side.grid(row=0, column=1, sticky="ns")

        self.info = tk.Label(side, text=self.status_text(), justify="left", anchor="w")
        self.info.pack(fill="x", padx=6, pady=6)

        self.advice = tk.Text(side, width=40, height=24, wrap="word")
        self.advice.pack(fill="both", expand=True, padx=6, pady=6)

        btns = tk.Frame(side)
        btns.pack(fill="x", padx=6, pady=6)
        tk.Button(btns, text="新規ゲーム", command=self.reset).pack(side="left")
        tk.Button(btns, text="パス(あなた)", command=self.user_pass).pack(side="left", padx=6)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.draw()
        if self.ai.enabled:
            self.update_advice("ヒント: 盤上の緑の点が合法手。クリックで黒石を置きます。AI(白)はChatGPTに問い合わせます。")
        else:
            self.update_advice("ヒント: 盤上の緑の点が合法手。クリックで黒石を置きます。現在はOFFLINE（ローカルAIで応手）。")
        print("[ReversiGUI.__init__] 完了")

    def reset(self):
        if self.busy:
            return
        self.board = initial_board()
        self.turn = BLACK
        self.draw()
        self.update_status()
        self.advice.delete("1.0", tk.END)
        self.update_advice("新規ゲームを開始しました。あなたが先手(黒)です。")

    def status_text(self) -> str:
        b, w = score(self.board)
        t = "黒(あなた)" if self.turn == BLACK else "白(AI)"
        mode = "ONLINE" if self.ai.enabled else "OFFLINE"
        return f"手番: {t}  モード: {mode}\n黒: {b}  白: {w}"

    def update_status(self):
        print("[update_status] called")
        self.info.config(text=self.status_text())

    def update_advice(self, msg: str):
        self.advice.insert(tk.END, msg + "\n")
        self.advice.see(tk.END)

    def draw(self):
        if self._drawing:
            print("[draw] skipped (reentrant)")
            return
        self._drawing = True
        print("[draw] called")
        # canvas.delete("all") の代わりに個別削除
        for cid in self._canvas_ids:
            try:
                self.canvas.delete(cid)
            except Exception as e:
                print(f"[draw] delete id {cid} failed: {e}")
        self._canvas_ids.clear()
        print("[draw] grid lines start")
        x0, y0 = PAD, PAD
        for i in range(SIZE+1):
            self._canvas_ids.append(self.canvas.create_line(x0, y0 + i*CELL, x0 + BOARD_SIZE, y0 + i*CELL, width=2, fill="#224422"))
            self._canvas_ids.append(self.canvas.create_line(x0 + i*CELL, y0, x0 + i*CELL, y0 + BOARD_SIZE, width=2, fill="#224422"))
        print("[draw] grid lines end")
        print("[draw] labels start")
        for i, ch in enumerate(COORD_A):
            self._canvas_ids.append(self.canvas.create_text(PAD + i*CELL + CELL/2, PAD/2, text=ch, fill="white", font=("Helvetica", 12, "bold")))
        for j in range(SIZE):
            self._canvas_ids.append(self.canvas.create_text(PAD/2, PAD + (SIZE-1-j)*CELL + CELL/2, text=str(j+1), fill="white", font=("Helvetica", 12, "bold")))
        print("[draw] labels end")
        print("[draw] stones start")
        for y in range(SIZE):
            for x in range(SIZE):
                v = self.board[y][x]
                if v != EMPTY:
                    cx = PAD + x*CELL + CELL/2
                    cy = PAD + (SIZE-1-y)*CELL + CELL/2  # invert Y for display
                    color = "black" if v == BLACK else "white"
                    outline = "#111" if v == BLACK else "#ddd"
                    self._canvas_ids.append(self.canvas.create_oval(cx-STONE_R, cy-STONE_R, cx+STONE_R, cy+STONE_R, fill=color, outline=outline, width=3))
        print("[draw] stones end")
        print("[draw] hints start")
        for (x, y) in legal_moves(self.board, self.turn):
            cx = PAD + x*CELL + CELL/2
            cy = PAD + (SIZE-1-y)*CELL + CELL/2
            self._canvas_ids.append(self.canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#99cc99", outline=""))
        print("[draw] hints end")
        self._drawing = False

    def on_click(self, event):
        print(f"[on_click] called: event=({event.x}, {event.y}) busy={self.busy} turn={self.turn}")
        if self.busy or self.turn != BLACK:
            print("[on_click] busy or not your turn")
            return
        x = int((event.x - PAD) // CELL)
        y_disp = int((event.y - PAD) // CELL)
        print(f"[on_click] x={x} y_disp={y_disp}")
        if not (0 <= x < SIZE and 0 <= y_disp < SIZE):
            print("[on_click] out of board")
            return
        y = SIZE - 1 - y_disp  # convert display to board coords
        print(f"[on_click] board coords: x={x} y={y}")
        res = apply_move(self.board, x, y, BLACK)
        print(f"[on_click] apply_move result: {res}")
        if not res:
            self.update_advice("その場所には置けません。合法手の点を参考にしてください。")
            print("[on_click] not a legal move")
            return
        self.board = res.board
        self.turn = WHITE
        self.draw()
        self.update_status()
        print("[on_click] user move applied, calling after_user_move")
        self.root.after(0, self.after_user_move)

    def user_pass(self):
        if self.busy or self.turn != BLACK:
            return
        if legal_moves(self.board, BLACK):
            self.update_advice("※ 合法手があるためパスは推奨されません。")
        self.turn = WHITE
        self.draw()
        self.update_status()
        self.root.after(0, self.after_user_move)

    def ai_worker(self):
        print("[ai_worker] start")
        t0 = time.time()
        try:
            print("[ai_worker] calling self.ai.choose...")
            result = self.ai.choose(self.board, WHITE)
            print(f"[ai_worker] ai.choose result: {result}")
        except Exception as e:
            import traceback
            print(f"[ai_worker] 例外: {e}")
            traceback.print_exc()
            result = {"move": "PASS", "candidates": [], "analysis": f"AI例外: {e}", "source": "local"}
        dt = time.time() - t0
        def apply():
            print("[ai_worker] apply called")
            try:
                print("[ai_worker] apply start")
                self.busy = False
                mv = result.get("move", "PASS").upper()
                src = result.get("source", "?")
                analysis = result.get("analysis", "")
                print(f"[ai_worker] apply: mv={mv} src={src} analysis={analysis}")
                self.update_advice(f"AI手({src}): {mv}  (応答 {dt:.1f}s)\n{analysis}")
                if mv != "PASS":
                    xy = ChatGPTOthello.from_notation(mv)
                    print(f"[ai_worker] apply: xy(from_notation)={xy}")
                    if xy is None:
                        print("[ai_worker] apply: xy is None (invalid notation)")
                        self.update_advice("AI応答が不正形式のため手をスキップしました。")
                    else:
                        print(f"[ai_worker] apply: before apply_move, board={self.board}")
                        res = apply_move(self.board, xy[0], xy[1], WHITE)
                        print(f"[ai_worker] apply: apply_move result={res}")
                        if res:
                            print(f"[ai_worker] apply: res.board={res.board}")
                            self.board = res.board
                            print(f"[ai_worker] apply: self.board updated={self.board}")
                        else:
                            print("[ai_worker] apply: apply_move returned None (illegal move?)")
                else:
                    print("[ai_worker] apply: AI passed (no move)")
                    self.update_advice("AIは合法手が無いためパスしました。")
                print(f"[ai_worker] apply: board after AI move={self.board}")
                if game_over(self.board):
                    print("[ai_worker] apply: game_over detected")
                    self.draw()
                    self.update_status()
                    self.finish_game()
                    return
                if legal_moves(self.board, BLACK):
                    print("[ai_worker] apply: user turn")
                    self.turn = BLACK
                    self.draw()
                    self.update_status()
                else:
                    if not legal_moves(self.board, WHITE):
                        print("[ai_worker] apply: both players no moves, game over")
                        self.draw()
                        self.update_status()
                        self.finish_game()
                        return
                    print("[ai_worker] apply: AI turn again")
                    self.turn = WHITE
                    self.draw()
                    self.update_status()
                    self.after_user_move()
                print("[ai_worker] apply end")
            except Exception as e:
                import traceback
                print(f"[ai_worker] apply: 例外発生: {e}")
                traceback.print_exc()
        apply()

    def finish_game(self):
        b, w = score(self.board)
        if b > w:
            msg = f"ゲーム終了: 黒(あなた)の勝ち！  {b}-{w}"
        elif w > b:
            msg = f"ゲーム終了: 白(AI)の勝ち！  {b}-{w}"
        else:
            msg = f"ゲーム終了: 引き分け  {b}-{w}"
        self.update_advice(msg)
        messagebox.showinfo("結果", msg)

# --------------------------------- main ------------------------------------

def main():
    print("[main] Tkinter起動")
    root = tk.Tk()
    print("[main] ReversiGUIインスタンス生成")
    app = ReversiGUI(root)
    print("[main] mainloop開始")
    root.mainloop()

if __name__ == "__main__":
    main()
