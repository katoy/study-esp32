import random
from player_base import PlayerBase

class PlayerLocalRandom(PlayerBase):
    CLASS_LABEL = "Local(random)"
    """
    ランダムに空きマスを選ぶローカルAI。
    """
    def select_move(self, board):
        empty = [(i, j) for i, row in enumerate(board) for j, cell in enumerate(row) if cell == 0]
        if not empty:
            return None
        return random.choice(empty)
