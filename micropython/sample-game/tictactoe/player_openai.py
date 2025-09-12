from player_base import PlayerBase

class PlayerOpenAI(PlayerBase):
    CLASS_LABEL = "OpenAI"
    """
    OpenAI APIを使った打ち手クラス。
    """
    def select_move(self, board):
        # 仮実装: API呼び出し部分は未実装
        # 実際はOpenAI APIを使って手を決定する
        return (0, 0)
