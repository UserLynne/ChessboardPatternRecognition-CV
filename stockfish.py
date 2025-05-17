# chess_ai.py
import chess
import chess.engine


class ChessAI:
    def __init__(self, engine_path, time_limit=0.5):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.time_limit = time_limit

    # chess_ai.py 中的 get_move 方法
    def get_move(self, fen):
        """获取AI推荐走法"""
        try:
            board = chess.Board(fen=fen)
            if board.is_game_over():
                return None  # 游戏已结束
            result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
            # result = self.engine.play(board, chess.engine.Limit(depth=16))  # 替代time限制
            return result.move
        except ValueError:
            print("错误：非法FEN格式")
            return None



    def close(self):
        self.engine.quit()