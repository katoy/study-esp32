#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
"""
Tic-Tac-Toe (三目並べ) GUI for macOS/Windows/Linux.
- マウスで着手（あなた=X）、AI=O。
- 対戦相手を OpenAI / Gemini / オフラインAI から選択可能。

環境変数:
  OPENAI_API_KEY   : OpenAI APIキー（省略可）
  GEMINI_API_KEY   : Gemini APIキー（省略可）
  OPENAI_MODEL     : 既定 'gpt-3.5-turbo'
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

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except Exception:
    _GEMINI_AVAILABLE = False
    genai = None


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

# --- Offline AI ---
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

# --- AI Player Integration ---
class AIPlayer:
    def __init__(self, ai_type: str):
        self.ai_type = ai_type
        self.online_mode = ai_type in ["openai", "gemini"]

        # ChatGPT setup
        self.openai_available = _OPENAI_AVAILABLE and bool(os.environ.get("OPENAI_API_KEY"))
        self.openai_model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.openai_client = OpenAI() if self.openai_available else None

        # Gemini setup
        self.gemini_available = _GEMINI_AVAILABLE and bool(os.environ.get("GEMINI_API_KEY"))
        if self.gemini_available and genai:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

    def board_to_str(self, board: List[List[int]]) -> str:
        return '\n'.join(' '.join(MARKS[v] or '.' for v in row) for row in board)

    def build_prompt(self, board: List[List[int]], mark: int) -> str:
        legal = legal_moves(board)
        who = 'O' if mark == O else 'X'
        return f'''あなたは三目並べ(Tic-Tac-Toe)のAIです。盤面と合法手から、あなた({who})の最善手を1つ選び、JSONで返してください。
盤面:
{self.board_to_str(board)}
合法手: {legal}
出力例: {{'move': [x, y], 'reason': '中央が空いているので有利'}}'''

    def choose(self, board: List[List[int]], mark: int) -> Dict[str, Any]:
        if self.ai_type == "offline":
            mv = best_legal_move(board, mark)
            return {"move": mv, "reason": "オフラインAI"}

        prompt = self.build_prompt(board, mark)
        try:
            if self.ai_type == "openai":
                if not self.openai_client:
                    raise Exception("OpenAI APIキーが設定されていません。")
                text = self._choose_openai_text(prompt)
            elif self.ai_type == "gemini":
                if not self.gemini_model:
                    raise Exception("Gemini APIキーが設定されていません。")
                text = self._choose_gemini_text(prompt)
            else:
                raise Exception(f"Unknown AI type: {self.ai_type}")

            data = self._parse_json_response(text)
            move = tuple(data.get("move", [None, None]))
            reason = data.get("reason", "")
            return {"move": move, "reason": reason}

        except Exception as e:
            mv = best_legal_move(board, mark)
            return {"move": mv, "reason": f"(API失敗→オフラインAI) {e}"}

    def _choose_openai_text(self, prompt: str) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": "あなたは三目並べの強いAIです。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 100,
        }
        resp = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            **payload
        )
        return resp.choices[0].message.content

    def _choose_gemini_text(self, prompt: str) -> str:
        response = self.gemini_model.generate_content(prompt)
        return response.text

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        try:
            # Handle potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            # Fallback for non-json responses
            # Try to find a json-like string
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
            raise ValueError("JSON応答の解析に失敗しました。")


# --- GUI ---
CELL = 100
PAD = 24
BOARD_SIZE = SIZE * CELL

class TicTacToeGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Tic-Tac-Toe (あなた=X / AI=O)")
        self.ai: Optional[AIPlayer] = None
        self.ai_x: Optional[AIPlayer] = None
        self.ai_o: Optional[AIPlayer] = None
        self.busy = False
        self.canvas = tk.Canvas(root, width=BOARD_SIZE+PAD*2, height=BOARD_SIZE+PAD*2, bg="#f0f0f0")
        self.canvas.grid(row=0, column=0)
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Key>", self.on_keypress)
        self.info = tk.Label(root, text="", font=("Helvetica", 14))
        self.info.grid(row=1, column=0, sticky="ew")
        self.advice = tk.Text(root, width=40, height=4, wrap="word")
        self.advice.grid(row=2, column=0, sticky="ew")
        self.human_player = None
        self.game_mode = None
        self.last_x_player = 'human'
        self.last_o_player = 'offline'
        self.ask_game_mode()

    def on_keypress(self, event):
        if self.busy:
            return

        if self.game_mode == 'hvh' or self.turn == self.human_player:
            if event.char in '123456789':
                idx = int(event.char) - 1
                x, y = idx % 3, idx // 3
                if 0 <= x < SIZE and 0 <= y < SIZE:
                    self.handle_move(x, y)

    def handle_move(self, x, y):
        if self.board[y][x] != EMPTY:
            self.update_advice("その場所には置けません。空きマスを選んでください。")
            return

        current_player = self.turn
        res = apply_move(self.board, x, y, current_player)
        if not res:
            return
        self.board = res.board
        self.draw()
        if res.win:
            self.finish_game(f"プレイヤー({MARKS[res.win]})の勝ち！")
            return
        if res.draw:
            self.finish_game("引き分け！")
            return

        self.turn = O if self.turn == X else X

        if self.game_mode == 'hvh':
            self.info.config(text=self.status_text())
        else: # Human vs AI
            self.update_advice("AI思考中…")
            self.busy = True
            self.root.after(100, self.ai_move)

    def ask_game_mode(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("対戦モードを選択")

        # --- Player X Selection ---
        from player_human import PlayerHuman
        from player_local_random import PlayerLocalRandom
        from player_local_minimax import PlayerLocalMinimax
        from player_openai import PlayerOpenAI
        from player_gemini import PlayerGemini
        player_types = [
            ("human", PlayerHuman.CLASS_LABEL),
            ("openai", PlayerOpenAI.CLASS_LABEL),
            ("gemini", PlayerGemini.CLASS_LABEL),
            ("local_random", PlayerLocalRandom.CLASS_LABEL),
            ("local_minimax", PlayerLocalMinimax.CLASS_LABEL),
            ("offline", "オフライン(従来)AI")
        ]
        tk.Label(dialog, text="先手 (X):", font=("Arial", 12, "bold")).pack(anchor='w', padx=10, pady=5)
        x_player_var = tk.StringVar(value=self.last_x_player)
        x_frame = tk.Frame(dialog)
        for value, label in player_types:
            tk.Radiobutton(x_frame, text=label, variable=x_player_var, value=value).pack(side='left')
        x_frame.pack(padx=20, anchor='w')

        tk.Label(dialog, text="後手 (O):", font=("Arial", 12, "bold")).pack(anchor='w', padx=10, pady=5)
        o_player_var = tk.StringVar(value=self.last_o_player)
        o_frame = tk.Frame(dialog)
        for value, label in player_types:
            tk.Radiobutton(o_frame, text=label, variable=o_player_var, value=value).pack(side='left')
        o_frame.pack(padx=20, anchor='w')

        def start_game():
            x_player = x_player_var.get()
            o_player = o_player_var.get()
            self.last_x_player = x_player
            self.last_o_player = o_player
            dialog.destroy()

            def make_ai(ai_type):
                if ai_type == 'local_random':
                    from player_local_random import PlayerLocalRandom
                    return PlayerLocalRandom()
                elif ai_type == 'local_minimax':
                    from player_local_minimax import PlayerLocalMinimax
                    return PlayerLocalMinimax()
                elif ai_type in ['openai', 'gemini', 'offline']:
                    return AIPlayer(ai_type)
                else:
                    return None

            if x_player == 'human' and o_player == 'human':
                self.game_mode = 'hvh'
                self.start_human_vs_human()
            elif x_player == 'human':
                self.game_mode = 'hva'
                self.ai = make_ai(o_player)
                self.set_human_player(X)
            elif o_player == 'human':
                self.game_mode = 'hva'
                self.ai = make_ai(x_player)
                self.set_human_player(O)
            else: # AI vs AI
                self.game_mode = 'ava'
                self.ai_x = make_ai(x_player)
                self.ai_o = make_ai(o_player)
                self.start_ai_vs_ai()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        btn_start = tk.Button(button_frame, text="対戦開始", width=12, command=start_game)
        btn_start.pack(side='left', padx=10)

        btn_quit = tk.Button(button_frame, text="ゲーム終了", width=12, command=lambda: (dialog.destroy(), self.root.destroy()))
        btn_quit.pack(side='right', padx=10)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def start_human_vs_human(self):
        self.game_mode = 'hvh'
        self.reset_game()

    def start_ai_vs_ai(self):
        self.game_mode = 'ava'
        self.reset_game()
        self.root.after(100, self.ai_vs_ai_move)

    def ai_vs_ai_move(self):
        if self.busy:
            return

        ai = self.ai_x if self.turn == X else self.ai_o

        t0 = time.time()
        result = ai.choose(self.board, self.turn)
        dt = time.time() - t0
        mv = result.get("move")
        reason = result.get("reason", "")

        if mv and isinstance(mv, list):
            mv = tuple(mv)

        if mv and isinstance(mv, tuple) and len(mv) == 2 and mv[0] is not None and mv[1] is not None:
            res = apply_move(self.board, mv[0], mv[1], self.turn)
            if res:
                self.board = res.board
                self.draw()
                self.update_advice(f"AI({MARKS[self.turn]})手: {mv} (応答 {dt:.1f}s)\
{reason}")
                if res.win:
                    self.finish_game(f"AI({MARKS[res.win]})の勝ち！")
                    return
                if res.draw:
                    self.finish_game("引き分け！")
                    return
            else:
                self.update_advice(f"AI({MARKS[self.turn]})が無効な手を指しました: {mv}。")
                self.finish_game(f"AI({MARKS[self.turn]})の反則負け！")
                return
        else:
             self.update_advice(f"AI({MARKS[self.turn]})が手を返せませんでした: {result}。")
             self.finish_game(f"AI({MARKS[self.turn]})の反則負け！")
             return

        self.turn = O if self.turn == X else X
        self.info.config(text=self.status_text())
        self.root.after(1000, self.ai_vs_ai_move) # 1秒待って次の手





    def set_human_player(self, player):
        self.human_player = player
        self.reset_game()
        if self.human_player == O:
            self.root.after(200, self.ai_move)

    def reset_game(self):
        self.board = initial_board()
        self.turn = X
        self.draw()
        self.info.config(text=self.status_text())
        self.advice.delete("1.0", tk.END)

        if self.ai:
            msg = f"AI ({self.ai.ai_type}) との対戦を開始します。"
            if self.ai.ai_type == 'gemini' and not self.ai.gemini_available:
                msg += " (Gemini APIキー未設定等のためオフラインAIで動作)"
            elif self.ai.ai_type == 'openai' and not self.ai.openai_available:
                msg += " (OpenAI APIキー未設定等のためオフラインAIで動作)"
            self.update_advice(msg)
        self.busy = False

    def status_text(self) -> str:
        if self.game_mode == 'hvh':
            return f"手番: プレイヤー({MARKS[self.turn]})"
        if self.game_mode == 'ava':
            return f"手番: AI({MARKS[self.turn]})"
        if not self.ai:
            return ""
        t = "あなた(X)" if self.turn == self.human_player else "AI(O)"
        return f"手番: {t}  AI: {self.ai.ai_type.upper()}"

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
        if self.busy:
            return

        if self.game_mode == 'hvh' or self.turn == self.human_player:
            x = int((event.x - PAD) // CELL)
            y = int((event.y - PAD) // CELL)
            if not (0 <= x < SIZE and 0 <= y < SIZE):
                return
            self.handle_move(x, y)

    def ai_move(self):
        if not self.ai or self.turn == self.human_player:
            return
        ai_mark = O if self.human_player == X else X
        t0 = time.time()
        result = self.ai.choose(self.board, ai_mark)
        dt = time.time() - t0
        mv = result.get("move")
        reason = result.get("reason", "")

        if mv and isinstance(mv, list):
            mv = tuple(mv)

        if mv and isinstance(mv, tuple) and len(mv) == 2 and mv[0] is not None and mv[1] is not None:
            res = apply_move(self.board, mv[0], mv[1], ai_mark)
            if res:
                self.board = res.board
                self.draw()
                self.update_advice(f"AI手: {mv} (応答 {dt:.1f}s)\n{reason}")
                if res.win == ai_mark:
                    self.finish_game(f"AI({MARKS[ai_mark]})の勝ち！")
                    return
                if res.draw:
                    self.finish_game("引き分け！")
                    return
            else:
                self.update_advice(f"AIが無効な手を指しました: {mv}。オフラインAIで再試行します。")
                result = AIPlayer('offline').choose(self.board, ai_mark)
                # ... (再試行のロジックをここに追加可能)

        else:
             self.update_advice(f"AIが手を返せませんでした: {result}。オフラインAIで試します。")
             # ... (オフラインAIでの再試行ロジック)

        self.turn = self.human_player
        self.busy = False
        self.info.config(text=self.status_text())

    def finish_game(self, msg: str):
        self.draw()
        self.update_advice(msg)
        def close_and_reask():
            self.ask_game_mode()

        self.root.after(100, lambda: (messagebox.showinfo("結果", msg), close_and_reask()))

# --- main ---
def main():
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()