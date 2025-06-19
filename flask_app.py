from flask import Flask, render_template, request, jsonify
from stockfish import get_best_move
from image2fen import image_to_fen

YOLO_MODEL_PATH = "chess-model-yolov11m.pt"
STOCKFISH_PATH = "stockfish/stockfish/stockfish-windows-x86-64-avx2.exe"


app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/move/<int:depth>/<path:fen>/')
def get_move(depth, fen):
    print(depth)
    print("Calculating...")
    move = get_best_move(depth - 1, fen, STOCKFISH_PATH)
    print("Move found!", move)
    print()
    return move

@app.route('/recognize', methods=['POST'])
def recognize():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    image_file = request.files['image']
    try:
        fen = image_to_fen(image_file, YOLO_MODEL_PATH)
        return jsonify({'fen': fen})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/test/<string:tester>')
def test_get(tester):
    return tester


if __name__ == '__main__':
    app.run(debug=True)
