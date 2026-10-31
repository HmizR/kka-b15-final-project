# Fungsi evaluasi heuristik untuk Othello.

from __future__ import annotations

from game.board import Board
from game.engine import get_score, get_valid_moves, is_terminal

BLACK = 1
WHITE = -1
EMPTY = 0

# Koordinat empat sudut papan.
_CORNERS = ((0, 0), (0, 7), (7, 0), (7, 7))

W_CORNER = 25
W_MOBILITY = 5
W_DISC = 1

WIN_BONUS = 100_000


def _count_corners(board: Board, player: int) -> int:
    """Hitung jumlah sudut yang dikuasai `player`."""
    return sum(1 for (r, c) in _CORNERS if board[r][c] == player)


def _validate_player(player: int) -> None:
    if player not in (BLACK, WHITE):
        raise ValueError(f"player harus BLACK (1) atau WHITE (-1), diterima: {player}")


def evaluate(board: Board, player: int) -> float:
    """Evaluasi state papan dari perspektif `player`.

    Parameters
    board : Board
        Papan 8x8. Tidak dimodifikasi.
    player : int
        BLACK (1) atau WHITE (-1).

    Returns
    -------
    float
        Skor heuristik. Positif = menguntungkan `player`.
    """
    _validate_player(player)

    opponent = -player

    # 1. Terminal state dicek lebih dulu
    if is_terminal(board):
        black_count, white_count = get_score(board)
        if black_count == white_count:
            return 0.0  # seri
        winner = BLACK if black_count > white_count else WHITE
        diff = (black_count - white_count) if player == BLACK else (white_count - black_count)
        return float(WIN_BONUS + diff) if winner == player else float(-WIN_BONUS + diff)

    # 2. Heuristik nonterminal 
    corner_diff = _count_corners(board, player) - _count_corners(board, opponent)
    mobility_diff = len(get_valid_moves(board, player)) - len(get_valid_moves(board, opponent))
    black_count, white_count = get_score(board)
    disc_diff = (black_count - white_count) if player == BLACK else (white_count - black_count)

    return float(W_CORNER * corner_diff + W_MOBILITY * mobility_diff + W_DISC * disc_diff)