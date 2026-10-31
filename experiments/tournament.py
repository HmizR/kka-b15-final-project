"""Balanced Alpha-Beta versus MCTS matches and CSV export."""
import argparse
import time
from pathlib import Path

from experiments.benchmark import save_csv
from experiments.common import search


def tournament(pairs: int = 1, depth: int = 4, iterations: int = 500,
               seed: int = 42, output: str | Path = "results/tournament.csv") -> list[dict]:
    """Play two games per pair, swapping colors with paired MCTS seeds.

    MCTS uses game_seed + its zero-based decision index; both are recorded
    through the game seed and documented seed policy.
    """
    for name, value in (("pairs", pairs), ("depth", depth), ("iterations", iterations)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    from game.board import create_board
    from game.engine import (apply_move, get_next_player, get_score,
                             get_valid_moves, get_winner, is_terminal)
    records = []
    for game_index in range(pairs * 2):
        black = "alphabeta" if game_index % 2 == 0 else "mcts"
        white = "mcts" if black == "alphabeta" else "alphabeta"
        board, player, placements, decisions = create_board(), 1, 0, 0
        game_seed = seed + (game_index // 2) * 1000
        started = time.perf_counter_ns()
        while not is_terminal(board):
            legal = get_valid_moves(board, player)
            if not legal:
                player = -player
                continue
            algorithm = black if player == 1 else white
            move, _ = search(algorithm, [r[:] for r in board], player,
                             depth if algorithm == "alphabeta" else iterations,
                             game_seed + decisions)
            if algorithm == "mcts":
                decisions += 1
            if move not in legal:
                raise ValueError(f"{algorithm} returned illegal move {move!r}")
            board = apply_move(board, *move, player)
            placements += 1
            next_player = get_next_player(board, player)
            if next_player is None:
                if not is_terminal(board):
                    raise ValueError("Engine returned None on a nonterminal board")
                break
            player = next_player
        duration = (time.perf_counter_ns() - started) / 1_000_000_000
        winner = get_winner(board)
        black_score, white_score = get_score(board)
        records.append({"game": game_index, "pair": game_index // 2,
                        "black_algorithm": black, "white_algorithm": white,
                        "depth": depth, "iterations": iterations, "mcts_seed": game_seed,
                        "seed_policy": "game_seed + mcts_decision_index",
                        "winner": winner, "winner_algorithm": "draw" if winner == 0 else black if winner == 1 else white,
                        "black_score": black_score, "white_score": white_score,
                        "moves": placements, "duration_seconds": duration})
    save_csv(records, output)
    return records


def main() -> None:
    """Run a balanced tournament from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=1)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/tournament.csv")
    tournament(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
