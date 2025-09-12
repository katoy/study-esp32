from player_base import PlayerBase
import math

class PlayerLocalMinimax(PlayerBase):
    CLASS_LABEL = "Local(minimax)"
    """
    Minimax法で最善手を選ぶローカルAI。
    盤面は 0:空, 1:自分, -1:相手 で表現されていると仮定。
    """
    def select_move(self, board):
        best_score = -math.inf
        best_move = None
        for i in range(len(board)):
            for j in range(len(board[i])):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = self.minimax(board, False)
                    board[i][j] = 0
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
        return best_move

    def minimax(self, board, is_maximizing):
        winner = self.check_winner(board)
        if winner is not None:
            return winner
        if all(cell != 0 for row in board for cell in row):
            return 0  # 引き分け
        if is_maximizing:
            best_score = -math.inf
            for i in range(len(board)):
                for j in range(len(board[i])):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        score = self.minimax(board, False)
                        board[i][j] = 0
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = math.inf
            for i in range(len(board)):
                for j in range(len(board[i])):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        score = self.minimax(board, True)
                        board[i][j] = 0
                        best_score = min(score, best_score)
            return best_score

    def check_winner(self, board):
        # 横・縦・斜めの勝敗判定
        lines = []
        size = len(board)
        for i in range(size):
            lines.append(board[i])  # 横
            lines.append([board[j][i] for j in range(size)])  # 縦
        lines.append([board[i][i] for i in range(size)])  # 斜め
        lines.append([board[i][size - 1 - i] for i in range(size)])  # 逆斜め
        for line in lines:
            if all(cell == 1 for cell in line):
                return 1  # 自分の勝ち
            if all(cell == -1 for cell in line):
                return -1  # 相手の勝ち
        return None
