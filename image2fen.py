import cv2
import numpy as np
import math
from ultralytics import YOLO
import chess

# 全局加载 YOLO 模型
_model = None


def get_yolo_model(model_path="chess-model-yolov8m.pt"):
    global _model
    if _model is None:
        _model = YOLO(model_path)
    return _model


# 棋子类别映射
class_dict = {
    0: 'black-bishop', 1: 'black-king', 2: 'black-knight', 3: 'black-pawn', 4: 'black-queen', 5: 'black-rook',
    6: 'white-bishop', 7: 'white-king', 8: 'white-knight', 9: 'white-pawn', 10: 'white-queen', 11: 'white-rook'
}

# FEN 符号映射
fen_dict = {
    "white-pawn": "P", "white-rook": "R", "white-knight": "N", "white-bishop": "B", "white-queen": "Q",
    "white-king": "K",
    "black-pawn": "p", "black-rook": "r", "black-knight": "n", "black-bishop": "b", "black-queen": "q",
    "black-king": "k",
    "space": "1"
}


def image_to_fen(image_file, model_path="chess-model-yolov8m.pt"):
    """
    将棋盘图片转换为 FEN 字符串。

    参数:
        image_file: Flask 上传的文件对象
        model_path: YOLO 模型路径

    返回:
        str: 完整的 FEN 字符串

    异常:
        ValueError: 无效图片或无法识别棋盘
        Exception: 其他错误
    """
    try:
        # 读取图片
        img_data = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Unable to read image")

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # OTSU 阈值
        _, otsu_binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Canny 边缘检测
        canny_image = cv2.Canny(otsu_binary, 20, 255)

        # 膨胀
        kernel = np.ones((6, 6), np.uint8)
        dilation_image = cv2.dilate(canny_image, kernel, iterations=1)

        # Hough 线检测
        lines = cv2.HoughLinesP(dilation_image, 1, np.pi / 180, threshold=500, minLineLength=150, maxLineGap=100)

        # 创建黑色图像，仅绘制 Hough 线
        black_image = np.zeros_like(dilation_image)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(black_image, (x1, y1), (x2, y2), (255, 255, 255), 2)

        # 膨胀
        kernel = np.ones((3, 3), np.uint8)
        black_image = cv2.dilate(black_image, kernel, iterations=1)

        # 寻找轮廓
        board_contours, _ = cv2.findContours(black_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        valid_squares_image = np.zeros_like(black_image)

        # 筛选潜在方格
        squares = []
        for contour in board_contours:
            if 2000 < cv2.contourArea(contour) < 50000:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) == 4:
                    pts = [pt[0].tolist() for pt in approx]
                    index_sorted = sorted(pts, key=lambda x: x[0], reverse=True)

                    if index_sorted[0][1] < index_sorted[1][1]:
                        index_sorted[0], index_sorted[1] = index_sorted[1], index_sorted[0]
                    if index_sorted[2][1] > index_sorted[3][1]:
                        index_sorted[2], index_sorted[3] = index_sorted[3], index_sorted[2]

                    pt1, pt2, pt3, pt4 = index_sorted
                    l1 = math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)
                    l2 = math.sqrt((pt2[0] - pt3[0]) ** 2 + (pt2[1] - pt3[1]) ** 2)
                    l3 = math.sqrt((pt3[0] - pt4[0]) ** 2 + (pt3[1] - pt4[1]) ** 2)
                    l4 = math.sqrt((pt1[0] - pt4[0]) ** 2 + (pt1[1] - pt4[1]) ** 2)
                    lengths = [l1, l2, l3, l4]
                    if max(lengths) - min(lengths) <= 70:
                        squares.append([pt1, pt2, pt3, pt4])

        if not squares:
            raise ValueError("No valid squares detected")

        # 膨胀有效方格图像
        kernel = np.ones((7, 7), np.uint8)
        for square in squares:
            pts = np.array(square, np.int32).reshape((-1, 1, 2))
            cv2.polylines(valid_squares_image, [pts], True, (255, 255, 255), 7)
        dilated_valid_squares_image = cv2.dilate(valid_squares_image, kernel, iterations=1)

        # 找到最大轮廓
        contours, _ = cv2.findContours(dilated_valid_squares_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea)

        # 找到棋盘四个角点
        top_left, top_right, bottom_left, bottom_right = None, None, None, None
        for point in largest_contour[:, 0]:
            x, y = point
            if top_left is None or (x + y < top_left[0] + top_left[1]):
                top_left = (x, y)
            if top_right is None or (x - y > top_right[0] - top_right[1]):
                top_right = (x, y)
            if bottom_left is None or (x - y < bottom_left[0] - bottom_left[1]):
                bottom_left = (x, y)
            if bottom_right is None or (x + y > bottom_right[0] + bottom_right[1]):
                bottom_right = (x, y)

        if not all([top_left, top_right, bottom_left, bottom_right]):
            raise ValueError("Unable to detect chessboard corners")

        # 透视变换
        width, height = 1200, 1200
        threshold = 0
        extreme_points_list = np.float32([top_left, top_right, bottom_left, bottom_right])
        dst_pts = np.float32([
            [threshold, threshold],
            [width + threshold, threshold],
            [threshold, height + threshold],
            [width + threshold, height + threshold]
        ])
        M = cv2.getPerspectiveTransform(extreme_points_list, dst_pts)
        warped_image = cv2.warpPerspective(rgb_image, M, (width + 2 * threshold, height + 2 * threshold))

        # 分割 8x8 网格
        rows, cols = 8, 8
        square_width = width // cols
        square_height = height // rows
        squares_data_warped = []
        for i in range(rows):
            for j in range(cols):
                top_left = (j * square_width, i * square_height)
                top_right = ((j + 1) * square_width, i * square_height)
                bottom_left = (j * square_width, (i + 1) * square_height)
                bottom_right = ((j + 1) * square_width, (i + 1) * square_height)
                x_center = (top_left[0] + bottom_right[0]) // 2
                y_center = (top_left[1] + bottom_right[1]) // 2
                squares_data_warped.append([
                    (x_center, y_center), bottom_right, top_right, top_left, bottom_left
                ])

        # 逆透视变换到原图
        M_inv = cv2.invert(M)[1]
        squares_data_warped_np = np.array([pt[0] for pt in squares_data_warped], dtype=np.float32).reshape(-1, 1, 2)
        squares_data_original_np = cv2.perspectiveTransform(squares_data_warped_np, M_inv)
        squares_data_original = squares_data_original_np.reshape(-1, 2)

        # 构建坐标字典
        coord_dict = {}
        cell = 1
        for center in squares_data_original:
            x, y = center
            # 近似边界（简化，假设方格大小均匀）
            size = square_width // 2
            coord_dict[cell] = [
                [x + size, y + size], [x + size, y - size],
                [x - size, y - size], [x - size, y + size]
            ]
            cell += 1

        # YOLO 棋子检测
        model = get_yolo_model(model_path)
        results = model(image)

        game_list = []
        for result in results:
            for id, box in enumerate(result.boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                x_mid = (x1 + x2) // 2
                y_mid = (y1 + y2) // 2 + 25
                for cell_value, coordinates in coord_dict.items():
                    x_values = [point[0] for point in coordinates]
                    y_values = [point[1] for point in coordinates]
                    if (min(x_values) <= x_mid <= max(x_values)) and (min(y_values) <= y_mid <= max(y_values)):
                        class_id = int(result.boxes.cls[id])
                        game_list.append([cell_value, class_id])
                        break

        # 生成棋盘字符串
        chess_str = ""
        for i in range(1, 65):
            for slist in game_list:
                if slist[0] == i:
                    chess_str += f" {class_dict[slist[1]]} "
                    break
            else:
                chess_str += " space "
            if i % 8 == 0:
                chess_str += "\n"

        # 转换为 FEN
        lines = [line.strip().split() for line in chess_str.strip().split('\n')]
        fen_rows = []
        for row in lines:
            fen_row = ""
            empty_count = 0
            for cell in row:
                symbol = fen_dict[cell]
                if symbol == "1":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += symbol
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)

        # 拼接棋盘部分
        fen_board = "/".join(fen_rows)

        # 添加默认 FEN 元信息（轮次、城堡、吃过路兵、步数）
        # 假设白方先走，无城堡和吃过路兵，初始步数
        fen = f"{fen_board} w KQkq - 0 1"

        # 验证 FEN
        chess.Board(fen)
        return fen

    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")