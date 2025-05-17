from stockfish import ChessAI
import chess
from colorama import Fore, Style

ai = ChessAI(engine_path="stockfish/stockfish/stockfish-windows-x86-64-avx2.exe")
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
board = chess.Board(fen)
history = []


def validate_move(uci_move):
    """验证走法是否合法"""
    try:
        move = chess.Move.from_uci(uci_move)
        return move in board.legal_moves
    except ValueError:
        return False

def print_color_board(board):
    """打印彩色Unicode棋盘"""
    print("\n" + "=" * 30)
    print(Fore.YELLOW + "    a  b  c  d  e  f  g  h")
    for rank in range(7, -1, -1):
        line = []
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            # 获取Unicode符号，无棋子时用"·"
            symbol = piece.unicode_symbol() if piece else "·"
            # 颜色设置：白棋亮蓝，黑棋亮红
            color = Fore.CYAN if piece and piece.color == chess.WHITE else Fore.RED
            line.append(f"{color}{symbol:^3}{Style.RESET_ALL}")
        print(Fore.YELLOW + f"{rank + 1} " + "".join(line))
    print("=" * 30 + "\n")


print(Fore.GREEN + "==== 国际象棋人机对战 ====")
while not board.is_game_over():
    print_color_board(board)
    print(Fore.MAGENTA + f"当前回合：{'白方' if board.turn == chess.WHITE else '黑方'}")

    if board.turn == chess.WHITE:
        # 人类玩家回合
        while True:
            result = ai.engine.play(board, chess.engine.Limit(time=0.5))
            print("AI推荐走法:", result.move)
            cmd = input("输入走法（如e2e4）或命令（undo/quit）: ").strip()
            if cmd == "quit":
                exit()
            elif cmd == "undo" and len(history) >= 1:
                board.pop()
                board.pop()
                history = history[:-2]
                print(Fore.BLUE + "已撤回一步")
                print_color_board(board)
            elif validate_move(cmd):
                board.push_uci(cmd)
                history.append(cmd)
                break
            else:
                print(Fore.RED + "非法输入！有效示例：e2e4")
    else:
        # AI回合
        result = ai.engine.play(board, chess.engine.Limit(time=0.5))
        board.push(result.move)
        history.append(str(result.move))
        print(Fore.BLUE + f"AI走法: {result.move}")

# 游戏结束
print(Fore.GREEN + "\n==== 对局结束 ====")
print(Fore.CYAN + f"结果: {board.result()}")
ai.engine.quit()
