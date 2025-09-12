from abc import ABC, abstractmethod

class PlayerBase(ABC):
    """
    打ち手の抽象クラス。
    すべてのプレイヤー（人間、AIなど）はこのクラスを継承する。
    """
    @abstractmethod
    def select_move(self, board):
        """
        盤面を受け取り、次の手を選択する。
        Args:
            board: 現在の盤面情報
        Returns:
            選択した手（例: (row, col)）
        """
        pass
