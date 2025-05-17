import chess
from chess.engine import SimpleEngine


def print_board(board):
    print("\n当前棋盘：")
    print(board.unicode(borders=True, empty_square="·"))

# 初始化引擎
engine_path = "stockfish/stockfish/stockfish-windows-x86-64-avx2.exe"  # 例如："./stockfish/stockfish.exe"
engine = SimpleEngine.popen_uci(engine_path)

# 手动输入FEN（后续替换为CV模块输入）
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
board = chess.Board(fen)

# 获取AI推荐走法
result = engine.play(board, chess.engine.Limit(time=0.5))
print("AI推荐走法:", result.move)


print_board(board)
# 关闭引擎
engine.quit()