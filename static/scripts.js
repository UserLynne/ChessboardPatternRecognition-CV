var board,
    game = new Chess(),
    statusEl = $('#status'),
    pgnEl = $('#pgn');

// 禁止拖动已结束游戏的棋子或非当前轮次的棋子
var onDragStart = function(source, piece, position, orientation) {
    if (game.game_over() ||
        (game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
    }
};

// 处理棋子放下，检查合法性并触发 AI 移动
var onDrop = function(source, target) {
    var move = game.move({
        from: source,
        to: target,
        promotion: 'q' // 自动升变为后
    });

    if (move === null) return 'snapback';

    updateStatus();
    if (!game.game_over()) {
        setTimeout(makeAIMove, 250);
    }
};

// 棋子放下后更新棋盘（处理特殊移动如王车易位）
var onSnapEnd = function() {
    board.position(game.fen());
};

// 更新游戏状态和移动记录
var updateStatus = function() {
    var status = '';
    var moveColor = game.turn() === 'w' ? 'White' : 'Black';

    if (game.in_checkmate()) {
        status = 'Game over, ' + moveColor + ' is in checkmate.';
    } else if (game.in_draw()) {
        status = 'Game over, drawn position';
    } else {
        status = moveColor + ' to move';
        if (game.in_check()) {
            status += ', ' + moveColor + ' is in check';
        }
    }

    statusEl.html(status);
    updateMoveTable();
    updateScroll();
};

// 更新移动记录表
var updateMoveTable = function() {
    var pgn = game.pgn().split(' ');
    var data = [];

    for (var i = 0; i < pgn.length; i += 3) {
        var index = i / 3;
        data[index] = {};
        for (var j = 0; j < 3; j++) {
            var label = j === 0 ? 'moveNumber' : j === 1 ? 'whiteMove' : 'blackMove';
            data[index][label] = (i + j < pgn.length) ? pgn[i + j] : '';
        }
    }

    $('#pgn tr').not(':first').remove();
    var html = '';
    for (var i = 0; i < data.length; i++) {
        html += '<tr><td>' + data[i].moveNumber + '</td><td>' +
                data[i].whiteMove + '</td><td>' +
                data[i].blackMove + '</td></tr>';
    }
    $('#pgn tr').first().after(html);
};

// 滚动移动记录表到底部
var updateScroll = function() {
    $('#moveTable').scrollTop($('#moveTable')[0].scrollHeight);
};

// 获取 AI 移动
var makeAIMove = function() {
    var depth = $('#sel1').val();
    var fen = game.fen();

    $.get($SCRIPT_ROOT + '/move/' + depth + '/' + fen, function(data) {
        game.move(data, { sloppy: true });
        board.position(game.fen());
        updateStatus();
    }).fail(function(jqXHR) {
        alert('Error getting AI move: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.error : 'Unknown error'));
    });
};

function getPieceName(pieceCode) {
    const map = {
        'p': '兵',
        'n': '骑士',
        'b': '象',
        'r': '车',
        'q': '皇后',
        'k': '国王'
    };
    return map[pieceCode.toLowerCase()] || '未知';
}

var getHint = function() {
    var depth = $('#sel1').val();
    var fen = game.fen();

    $.get($SCRIPT_ROOT + '/move/' + depth + '/' + fen, function(data) {
        var move = game.move(data, { sloppy: true, dry_run: true });
        if (move) {
            var colorZh = game.turn() === 'w' ? '黑方' : '白方';
            var pieceZh = getPieceName(move.piece);
            var square = move.to;

            $('#hintText').text('提示：' + colorZh + ' ' + pieceZh + ' 移动到 ' + square);
        }
        game.undo(); // 撤销试探
    }).fail(function(jqXHR) {
        alert('Error getting hint: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.error : 'Unknown error'));
    });
};



// 撤销一步（玩家和 AI 各一步）
var takeBack = function() {
    game.undo();
    game.undo();
    board.position(game.fen());
    updateStatus();
};

// 新游戏
var newGame = function() {
    game.reset();
    board.start();
    updateStatus();
    $('#previewImage').hide();
    $('#imageInput').val('');
};

// 上传图片并识别棋盘
var uploadImage = function() {
    var fileInput = document.getElementById('imageInput');
    var file = fileInput.files[0];
    if (!file) {
        alert('Please select an image');
        return;
    }

    // 显示预览和加载提示
    var previewImage = document.getElementById('previewImage');
    previewImage.src = URL.createObjectURL(file);
    previewImage.style.display = 'block';
    $('#loading').show();

    var formData = new FormData();
    formData.append('image', file);

    $.ajax({
        url: $SCRIPT_ROOT + '/recognize',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data) {
            $('#loading').hide();
            if (data.fen) {
                try {
                    game.load(data.fen);
                    board.position(data.fen);
                    updateStatus();
                    alert('Chess board recognized! FEN: ' + data.fen);
                    if (game.turn() === 'b') {
                        setTimeout(makeAIMove, 250);
                    }
                } catch (e) {
                    alert('Invalid FEN: ' + data.fen);
                }
            } else {
                alert('Error recognizing board: ' + data.error);
            }
        },
        error: function(jqXHR) {
            $('#loading').hide();
            alert('Error uploading image: ' + (jqXHR.responseJSON ? jqXHR.responseJSON.error : 'Unknown error'));
        }
    });
};

// 初始化棋盘
var cfg = {
    draggable: true,
    position: 'start',
    pieceTheme: $SCRIPT_ROOT + '/static/libs/chessboard/img/chesspieces/wikipedia/{piece}.png',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd
};

$(document).ready(function() {
    board = ChessBoard('board', cfg);
    updateStatus();
});
