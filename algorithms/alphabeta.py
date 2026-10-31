# AI Othello berbasis Minimax + Alpha-Beta Pruning.

from __future__ import annotations

from game.board import Board
from game.engine import (
    apply_move,
    get_next_player,
    get_valid_moves,
    is_terminal,
)
from algorithms.evaluation import evaluate

BLACK = 1
WHITE = -1


class _Stats:
    __slots__ = ("nodes_visited", "nodes_expanded", "max_depth_reached", "pruned_branches")

    def __init__(self) -> None:
        self.nodes_visited = 0
        self.nodes_expanded = 0
        self.max_depth_reached = 0
        self.pruned_branches = 0

    def to_dict(self) -> dict:
        return {
            "nodes_visited": self.nodes_visited,
            "nodes_expanded": self.nodes_expanded,
            "max_depth_reached": self.max_depth_reached,
            "pruned_branches": self.pruned_branches,
        }


def _alphabeta(
    board: Board,
    player: int,
    depth: int,
    alpha: float,
    beta: float,
    root_player: int,
    stats: _Stats,
    current_depth: int = 0,
) -> float:
    """Kembalikan nilai evaluasi state `board` dari perspektif `root_player`.

    `player` = pemain yang giliran pada node ini (bisa root atau lawan).
    `depth`  = sisa kedalaman; 0 = leaf.
    """
    stats.nodes_visited += 1
    if current_depth > stats.max_depth_reached:
        stats.max_depth_reached = current_depth

    if depth == 0 or is_terminal(board):
        return evaluate(board, root_player)

    valid_moves = get_valid_moves(board, player)

    if not valid_moves:
        next_player = get_next_player(board, player)
        stats.nodes_expanded += 1
        return _alphabeta(
            board, next_player, depth, alpha, beta,
            root_player, stats, current_depth + 1,
        )

    maximizing = (player == root_player)

    if maximizing:
        value = float("-inf")
        for idx, (row, col) in enumerate(valid_moves):
            child = apply_move(board, row, col, player)
            stats.nodes_expanded += 1
            next_player = get_next_player(child, player)
            if next_player is None:
                score = evaluate(child, root_player)
            else:
                score = _alphabeta(
                    child, next_player, depth - 1, alpha, beta,
                    root_player, stats, current_depth + 1,
                )
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                stats.pruned_branches += (len(valid_moves) - idx - 1)
                break
        return value
    else:
        value = float("inf")
        for idx, (row, col) in enumerate(valid_moves):
            child = apply_move(board, row, col, player)
            stats.nodes_expanded += 1
            next_player = get_next_player(child, player)
            if next_player is None:
                score = evaluate(child, root_player)
            else:
                score = _alphabeta(
                    child, next_player, depth - 1, alpha, beta,
                    root_player, stats, current_depth + 1,
                )
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                stats.pruned_branches += (len(valid_moves) - idx - 1)
                break
        return value



# API publik
def get_best_move(
    board: Board,
    player: int,
    depth: int = 4,
) -> tuple[tuple[int, int] | None, dict]:
    """Pilih langkah terbaik untuk `player` dengan Alpha-Beta Pruning.

    Parameters
    ----------
    board : Board
        Papan 8x8. TIDAK dimodifikasi.
    player : int
        BLACK (1) atau WHITE (-1).
    depth : int
        Kedalaman pencarian. Harus >= 1.

    Returns
    -------
    (move, stats)
        move  : (row, col) atau None jika tidak ada langkah legal.
        stats : dict sesuai kontrak bersama (+ "pruned_branches").
    """
    if player not in (BLACK, WHITE):
        raise ValueError(f"player harus BLACK (1) atau WHITE (-1), diterima: {player}")
    if depth < 1:
        raise ValueError(f"depth minimal 1, diterima: {depth}")

    stats = _Stats()
    valid_moves = get_valid_moves(board, player)

    if not valid_moves:
        return None, stats.to_dict()

    best_move: tuple[int, int] | None = None
    best_value = float("-inf")
    alpha = float("-inf")
    beta = float("inf")

    for (row, col) in valid_moves:
        child = apply_move(board, row, col, player)
        stats.nodes_expanded += 1
        next_player = get_next_player(child, player)

        if next_player is None:
            value = evaluate(child, player)
        else:
            value = _alphabeta(
                child, next_player, depth - 1,
                alpha, beta, root_player=player,
                stats=stats, current_depth=1,
            )

        if value > best_value:
            best_value = value
            best_move = (row, col)
        if best_value > alpha:
            alpha = best_value

    assert best_move is not None
    return best_move, stats.to_dict()