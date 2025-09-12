from player_base import PlayerBase

class PlayerHuman(PlayerBase):
    CLASS_LABEL = "人間"
    """
    人間の打ち手クラス。
    ユーザーからの入力で手を決定する。
    """
    def select_move(self, board):
        # ここでは仮実装として (0, 0) を返す
        # 実際はUIや入力処理で手を取得する
        return (0, 0)
