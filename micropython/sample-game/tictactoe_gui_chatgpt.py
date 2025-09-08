#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
"""
Tic-Tac-Toe (三目並べ) GUI for macOS/Windows/Linux.
- マウスで着手（あなた=X）、AI=O。
- ChatGPT(API)が使えない/使わない場合はローカルAIで動作。

環境変数:
  OPENAI_API_KEY   : APIキー（省略可）
  OPENAI_MODEL     : 既定 'gpt-3.5-turbo'
  TTT_OFFLINE      : '1' でオンライン問い合わせを無効化（強制オフライン）
"""
import os
import json
import time
from typing import List, Optional, Tuple, Dict, Any

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False
    OpenAI = None

import tkinter as tk
from tkinter import messagebox

SIZE = 3
EMPTY, X, O = 0, 1, -1
MARKS = {X: 'X', O: 'O', EMPTY: ''}

@dataclass
class MoveResult:
    board: List[List[int]]
    win: Optional[int]
    draw: bool

# --- Game Logic ---
def initial_board() -> List[List[int]]:
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [(x, y) for y in range(SIZE) for x in range(SIZE) if board[y][x] == EMPTY]

def apply_move(board: List[List[int]], x: int, y: int, mark: int) -> Optional[MoveResult]:
    if board[y][x] != EMPTY:
        return None
    nb = [row[:] for row in board]
    nb[y][x] = mark
    win = check_win(nb)
    draw = all(nb[j][i] != EMPTY for j in range(SIZE) for i in range(SIZE)) and win is None
    return MoveResult(board=nb, win=win, draw=draw)

def check_win(board: List[List[int]]) -> Optional[int]:
    for i in range(SIZE):
        if abs(sum(board[i])) == SIZE and board[i][0] != EMPTY:
            return board[i][0]
        if abs(sum(board[j][i] for j in range(SIZE))) == SIZE and board[0][i] != EMPTY:
            return board[0][i]
    if abs(sum(board[i][i] for i in range(SIZE))) == SIZE and board[0][0] != EMPTY:
        return board[0][0]
    if abs(sum(board[i][SIZE-1-i] for i in range(SIZE))) == SIZE and board[0][SIZE-1] != EMPTY:
        return board[0][SIZE-1]
    return None

# --- Local AI ---
def best_legal_move(board: List[List[int]], mark: int) -> Optional[Tuple[int, int]]:
    moves = legal_moves(board)
    if not moves:
        return None
    # 1. 勝てる手
    for x, y in moves:
        res = apply_move(board, x, y, mark)
        if res and res.win == mark:
            return (x, y)
    # 2. 相手の勝ちを防ぐ
    for x, y in moves:
        res = apply_move(board, x, y, -mark)
        if res and res.win == -mark:
            return (x, y)
    # 3. 中央
    if board[1][1] == EMPTY:
        return (1, 1)
    # 4. 角
    for (x, y) in [(0,0),(0,2),(2,0),(2,2)]:
        if board[y][x] == EMPTY:
            return (x, y)
    # 5. その他
    return moves[0]

# --- ChatGPT Integration ---
class ChatGPTTicTacToe:
    def __init__(self):
        self.enabled = _OPENAI_AVAILABLE and bool(os.environ.get("OPENAI_API_KEY"))
        if os.environ.get("TTT_OFFLINE") == "1":
            self.enabled = False
        self.model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.client = OpenAI() if (self.enabled and OpenAI is not None) else None

    def board_to_str(self, board: List[List[int]]) -> str:
        return '\n'.join(' '.join(MARKS[v] or '.' for v in row) for row in board)

    def build_prompt(self, board: List[List[int]], mark: int) -> Dict[str, Any]:
        legal = legal_moves(board)
        who = 'O' if mark == O else 'X'
        prompt = (
            f"あなたは三目並べ(Tic-Tac-Toe)のAIです。盤面と合法手から、あなた({who})の最善手を1つ選び、JSONで返してください。\n"
            f"盤面:\n{self.board_to_str(board)}\n"
            f"合法手: {legal}\n"
            "出力例: {\"move\": [x, y], \"reason\": \"中央が空いているので有利\"}"
        )
        return {
            "messages": [
                {"role": "system", "content": "あなたは三目並べの強いAIです。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 100,
        }

    def choose(self, board: List[List[int]], mark: int) -> Dict[str, Any]:
        if not self.enabled or self.client is None:
            mv = best_legal_move(board, mark)
            return {"move": mv, "reason": "ローカルAI"}
        try:
            payload = self.build_prompt(board, mark)
            resp = self.client.chat.completions.create(
                model=self.model,
                **payload
            )
            text = resp.choices[0].message.content
            data = json.loads(text)
            move = tuple(data.get("move", [None, None]))
            reason = data.get("reason", "")
            return {"move": move, "reason": reason}
        except Exception as e:
            mv = best_legal_move(board, mark)
            return {"move": mv, "reason": f"(API失敗→ローカル) {e}"}

# --- GUI ---
CELL = 100
PAD = 24
BOARD_SIZE = SIZE * CELL

class TicTacToeGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tic-Tac-Toe (あなた=X / AI=O)")
        self.ai = ChatGPTTicTacToe()
        self.busy = False
        self.canvas = tk.Canvas(root, width=BOARD_SIZE+PAD*2, height=BOARD_SIZE+PAD*2, bg="#f0f0f0")
        self.canvas.grid(row=0, column=0)
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Key>", self.on_keypress)
        self.info = tk.Label(root, text="", font=("Helvetica", 14))
        self.info.grid(row=1, column=0, sticky="ew")
        self.advice = tk.Text(root, width=40, height=4, wrap="word")
        self.advice.grid(row=2, column=0, sticky="ew")
        self.human_player = None  # X or O
        self.ask_first_player()

    def on_keypress(self, event):
        if self.busy or self.turn != self.human_player:
            return
        if event.char in '123456789':
            idx = int(event.char) - 1
            x, y = idx % 3, idx // 3
            if 0 <= x < SIZE and 0 <= y < SIZE:
                self.handle_move(x, y)

    def handle_move(self, x, y):
        if self.board[y][x] != EMPTY:
            self.update_advice("その場所には置けません。空きマスを選んでください。")
            return
        res = apply_move(self.board, x, y, self.human_player)
        if not res:
            self.update_advice("その場所には置けません。空きマスを選んでください。")
            return
        self.board = res.board
        self.draw()
        if res.win == self.human_player:
            self.finish_game(f"あなた({MARKS[self.human_player]})の勝ち！")
            return
        if res.draw:
            self.finish_game("引き分け！")
            return
        self.turn = O if self.human_player == X else X
        self.update_advice("AI思考中…")
        self.busy = True
        self.root.after(100, self.ai_move)

    def ask_first_player(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("先手・後手・終了の選択")
        tk.Label(dialog, text="どちらでプレイしますか？", font=("Arial", 12)).pack(padx=20, pady=10)
        btn_x = tk.Button(dialog, text="先手 (X)", width=12, command=lambda: (dialog.destroy(), self.set_human_player(X)))
        btn_o = tk.Button(dialog, text="後手 (O)", width=12, command=lambda: (dialog.destroy(), self.set_human_player(O)))
        btn_quit = tk.Button(dialog, text="終了", width=12, command=lambda: (dialog.destroy(), self.root.destroy()))
        btn_x.pack(pady=5)
        btn_o.pack(pady=5)
        btn_quit.pack(pady=5)
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def set_human_player(self, player):
        self.human_player = player
        self.reset_game()
        if self.human_player == O:
            self.root.after(200, self.ai_move)

    def reset_game(self):
        self.board = initial_board()
        self.turn = X if self.human_player is None else (X if self.human_player == X else O)
        self.draw()
        self.info.config(text=self.status_text())
        self.advice.delete("1.0", tk.END)
        if self.ai.enabled:
            self.update_advice("ヒント: 盤上をクリックしてXを置きます。AI(O)はChatGPTに問い合わせます。")
        else:
            self.update_advice("ヒント: 盤上をクリックしてXを置きます。現在はOFFLINE（ローカルAIで応手）。")
        self.busy = False

    def status_text(self) -> str:
        t = "あなた(X)" if self.turn == X else "AI(O)"
        mode = "ONLINE" if self.ai.enabled else "OFFLINE"
        return f"手番: {t}  モード: {mode}"

    def update_advice(self, msg: str):
        self.advice.insert(tk.END, msg + "\n")
        self.advice.see(tk.END)

    def draw(self):
        self.canvas.delete("all")
        for i in range(1, SIZE):
            self.canvas.create_line(PAD, PAD + i*CELL, PAD + BOARD_SIZE, PAD + i*CELL, width=2)
            self.canvas.create_line(PAD + i*CELL, PAD, PAD + i*CELL, PAD + BOARD_SIZE, width=2)
        for y in range(SIZE):
            for x in range(SIZE):
                v = self.board[y][x]
                cx = PAD + x*CELL + CELL/2
                cy = PAD + y*CELL + CELL/2
                if v != EMPTY:
                    self.canvas.create_text(cx, cy, text=MARKS[v], font=("Helvetica", 48, "bold"), fill="#333")
                else:
                    idx = y * 3 + x + 1
                    self.canvas.create_text(cx, cy, text=str(idx), font=("Helvetica", 20), fill="#bbb")

    def on_click(self, event):
        if self.busy or self.turn != self.human_player:
            return
        x = int((event.x - PAD) // CELL)
        y = int((event.y - PAD) // CELL)
        if not (0 <= x < SIZE and 0 <= y < SIZE):
            return
        self.handle_move(x, y)

    def ai_move(self):
        ai_mark = O if self.human_player == X else X
        t0 = time.time()
        result = self.ai.choose(self.board, ai_mark)
        dt = time.time() - t0
        mv = result.get("move", (None, None))
        reason = result.get("reason", "")
        if mv and mv[0] is not None and mv[1] is not None:
            res = apply_move(self.board, mv[0], mv[1], ai_mark)
            if res:
                self.board = res.board
                self.draw()
                self.update_advice(f"AI手: {mv}  (応答 {dt:.1f}s)\n{reason}")
                if res.win == ai_mark:
                    self.finish_game(f"AI({MARKS[ai_mark]})の勝ち！")
                    return
                if res.draw:
                    self.finish_game("引き分け！")
                    return
        self.turn = self.human_player
        self.busy = False
        self.info.config(text=self.status_text())

    def finish_game(self, msg: str):
        self.draw()  # 盤面を先に反映
        self.update_advice(msg)
        def clear_board():
            self.ask_first_player()
        self.root.after(100, lambda: (messagebox.showinfo("結果", msg), clear_board()))

# --- main ---
def main():
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
