# Unit test untuk Alpha-Beta Pruning dan heuristik.

from __future__ import annotations

import pytest

from game.board import create_board, copy_board
from game.engine import apply_move, get_valid_moves, get_score, is_terminal
from algorithms.evaluation import evaluate
from algorithms.alphabeta import get_best_move

BLACK = 1
WHITE = -1



# Fixtures bantu
def _play_moves(board, moves):
    """Terapkan urutan langkah (row, col, player) ke board."""
    for (r, c, p) in moves:
        board = apply_move(board, r, c, p)
    return board


def _board_after_opening():
    """Posisi setelah beberapa langkah pembuka standar."""
    board = create_board()
    board = apply_move(board, 2, 3, BLACK)
    board = apply_move(board, 2, 2, WHITE)
    board = apply_move(board, 2, 1, BLACK)
    return board


# Test evaluasi nonterminal
def test_evaluate_initial_position_is_zero():
    """Posisi awal simetris -> heuristik harus 0 untuk kedua pemain."""
    board = create_board()
    assert evaluate(board, BLACK) == pytest.approx(0.0)
    assert evaluate(board, WHITE) == pytest.approx(0.0)


def test_evaluate_returns_float():
    board = create_board()
    result = evaluate(board, BLACK)
    assert isinstance(result, float)


def test_evaluate_invalid_player_raises():
    board = create_board()
    with pytest.raises(ValueError):
        evaluate(board, 0)
    with pytest.raises(ValueError):
        evaluate(board, 2)


def test_evaluate_does_not_mutate_board():
    board = create_board()
    snapshot = copy_board(board)
    evaluate(board, BLACK)
    evaluate(board, WHITE)
    assert board == snapshot


# Test evaluasi terminal
def _build_full_board(black_count: int, white_count: int):
    """Bangun papan penuh manual (hanya untuk unit test evaluasi terminal).

    Catatan: spec menyarankan skenario eksperimen dibentuk dari langkah legal,
    tetapi untuk *unit test* fungsi evaluate() kita boleh menyusun papan
    langsung agar bisa menguji cabang terminal secara terkontrol.
    """
    assert black_count + white_count == 64
    flat = [BLACK] * black_count + [WHITE] * white_count
    return [flat[r * 8:(r + 1) * 8] for r in range(8)]


def test_evaluate_terminal_win_black():
    board = _build_full_board(40, 24)
    assert is_terminal(board)
    val = evaluate(board, BLACK)
    # Menang: +100000 + D, dengan D = 40 - 24 = 16
    assert val == pytest.approx(100_000 + 16)


def test_evaluate_terminal_lose_black():
    board = _build_full_board(24, 40)
    assert is_terminal(board)
    val = evaluate(board, BLACK)
    # Kalah: -100000 + D, dengan D = 24 - 40 = -16
    assert val == pytest.approx(-100_000 - 16)


def test_evaluate_terminal_draw():
    board = _build_full_board(32, 32)
    assert is_terminal(board)
    assert evaluate(board, BLACK) == pytest.approx(0.0)
    assert evaluate(board, WHITE) == pytest.approx(0.0)


def test_evaluate_terminal_perspective_white():
    """Nilai terminal harus berubah tanda sesuai perspektif."""
    board = _build_full_board(40, 24)
    black_val = evaluate(board, BLACK)
    white_val = evaluate(board, WHITE)
    assert white_val == pytest.approx(-black_val)  
    assert black_val > 0
    assert white_val < 0



# Test get_best_move — validasi input
def test_depth_less_than_one_raises():
    board = create_board()
    with pytest.raises(ValueError):
        get_best_move(board, BLACK, depth=0)
    with pytest.raises(ValueError):
        get_best_move(board, BLACK, depth=-3)


def test_invalid_player_raises():
    board = create_board()
    with pytest.raises(ValueError):
        get_best_move(board, 0)
    with pytest.raises(ValueError):
        get_best_move(board, 2)


# Test get_best_move — perilaku
@pytest.mark.parametrize("depth", [1, 2, 4, 6])
def test_returns_legal_move(depth):
    board = create_board()
    move, stats = get_best_move(board, BLACK, depth=depth)
    assert move in get_valid_moves(board, BLACK)


def test_initial_black_move_is_lexicographically_smallest_on_tie():
    """Pada posisi awal semua langkah simetris -> tie-break -> (2,3)."""
    board = create_board()
    move, _ = get_best_move(board, BLACK, depth=2)
    assert move == (2, 3)


def test_returns_none_on_pass():
    """Posisi di mana pemain tidak punya langkah legal -> (None, stats)."""
    board = create_board()
    full = _build_full_board(32, 32)
    move, stats = get_best_move(full, BLACK, depth=2)
    assert move is None
    assert stats["nodes_visited"] == 0
    assert stats["nodes_expanded"] == 0
    assert stats["max_depth_reached"] == 0
    assert stats["pruned_branches"] == 0


def test_board_not_mutated():
    board = create_board()
    snapshot = copy_board(board)
    get_best_move(board, BLACK, depth=4)
    assert board == snapshot


def test_deterministic():
    board = create_board()
    move1, stats1 = get_best_move(board, BLACK, depth=4)
    move2, stats2 = get_best_move(board, BLACK, depth=4)
    assert move1 == move2
    assert stats1 == stats2


# Test statistik
def test_stats_keys_and_nonnegative():
    board = create_board()
    _, stats = get_best_move(board, BLACK, depth=3)
    for key in ("nodes_visited", "nodes_expanded", "max_depth_reached", "pruned_branches"):
        assert key in stats
        assert isinstance(stats[key], int)
        assert stats[key] >= 0


def test_stats_nodes_visited_positive_when_searching():
    board = create_board()
    _, stats = get_best_move(board, BLACK, depth=2)
    assert stats["nodes_visited"] > 0
    assert stats["nodes_expanded"] > 0


def test_max_depth_reached_not_exceeding_depth():
    board = create_board()
    depth = 3
    _, stats = get_best_move(board, BLACK, depth=depth)
    assert stats["max_depth_reached"] <= depth


# Test ekuivalensi Alpha-Beta vs Minimax tanpa pruning
def _minimax_no_pruning(board, player, depth, root_player):
    """Minimax murni tanpa pruning — referensi untuk uji ekuivalensi."""
    if depth == 0 or is_terminal(board):
        return evaluate(board, root_player)

    from game.engine import get_next_player
    valid = get_valid_moves(board, player)
    if not valid:
        np_ = get_next_player(board, player)
        return _minimax_no_pruning(board, np_, depth, root_player)

    maximizing = (player == root_player)
    if maximizing:
        best = float("-inf")
        for (r, c) in valid:
            child = apply_move(board, r, c, player)
            np_ = get_next_player(child, player)
            v = (evaluate(child, root_player) if np_ is None
                 else _minimax_no_pruning(child, np_, depth - 1, root_player))
            best = max(best, v)
        return best
    else:
        best = float("inf")
        for (r, c) in valid:
            child = apply_move(board, r, c, player)
            np_ = get_next_player(child, player)
            v = (evaluate(child, root_player) if np_ is None
                 else _minimax_no_pruning(child, np_, depth - 1, root_player))
            best = min(best, v)
        return best


def test_alphabeta_equals_minimax_value():
    """Nilai terbaik Alpha-Beta harus sama dengan Minimax tanpa pruning."""
    from algorithms.alphabeta import _alphabeta, _Stats
    from game.engine import get_next_player

    board = _board_after_opening()
    player = WHITE
    depth = 3

    stats = _Stats()
    stats.nodes_visited += 1
    next_p = get_next_player(board, player)

    for (r, c) in get_valid_moves(board, player):
        child = apply_move(board, r, c, player)
        np_ = get_next_player(child, player)
        ab_stats = _Stats()
        if np_ is None:
            ab_val = evaluate(child, player)
        else:
            ab_val = _alphabeta(child, np_, depth - 1, float("-inf"), float("inf"),
                                root_player=player, stats=ab_stats, current_depth=1)
        mm_val = (evaluate(child, player) if np_ is None
                  else _minimax_no_pruning(child, np_, depth - 1, player))
        assert ab_val == pytest.approx(mm_val), f"mismatch at move {(r, c)}"