import chess
import chess.engine


def get_best_move(depth, fen, stockfish_path="path/to/stockfish"):
    """
    使用 Stockfish 引擎计算指定深度和 FEN 的最佳移动。

    参数:
        depth (int): 搜索深度
        fen (str): FEN 字符串表示的棋盘局面
        stockfish_path (str): Stockfish 可执行文件路径

    返回:
        str: 最佳移动的 UCI 表示（如 'e2e4'）

    异常:
        ValueError: 如果 FEN 无效
        Exception: 如果 Stockfish 路径错误或其他问题
    """
    print(f"Depth: {depth}")
    print("Calculating...")
    try:
        # 初始化棋盘
        board = chess.Board(fen)
        # 初始化 Stockfish 引擎
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        # 使用 Stockfish 分析
        result = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = result["pv"][0]  # 获取最佳移动
        print("Move found!", str(best_move))
        # 关闭引擎
        engine.quit()
        return str(best_move)
    except ValueError as e:
        print(f"Error: Invalid FEN - {e}")
        raise ValueError(f"Invalid FEN string: {str(e)}")
    except Exception as e:
        print(f"Error: {e}")
        raise Exception(f"Error processing move: {str(e)}")