"""Shared experiment dispatch; no GUI dependency."""
from importlib import import_module
from typing import TypeAlias

Board: TypeAlias = list[list[int]]
Move: TypeAlias = tuple[int, int]


def search(algorithm: str, board: Board, player: int, parameter: int,
           seed: int = 42) -> tuple[Move | None, dict]:
    """Invoke an AI through the agreed public API."""
    if algorithm not in ("alphabeta", "mcts"):
        raise ValueError("algorithm must be alphabeta or mcts")
    if isinstance(parameter, bool) or not isinstance(parameter, int) or parameter < 1:
        raise ValueError("parameter must be a positive integer")
    if player not in (1, -1):
        raise ValueError("player must be BLACK (1) or WHITE (-1)")
    module = import_module(f"algorithms.{algorithm}")
    kwargs = {"depth": parameter} if algorithm == "alphabeta" else {
        "iterations": parameter, "seed": seed}
    return module.get_best_move(board, player, **kwargs)
