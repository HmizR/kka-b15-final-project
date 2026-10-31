"""Reproducible, reachable Othello positions with replayable move histories."""
from experiments.common import Board, Move


def get_scenarios() -> dict[str, dict]:
    """Generate opening, midgame (24 placements), and endgame (50 placements).

    Choose the lexicographically first legal move at every turn. Histories
    record the player as well as coordinates so automatic passes are explicit.
    Each call returns independent boards and histories.
    """
    from game.board import create_board
    from game.engine import apply_move, get_next_player, get_valid_moves, is_terminal
    board: Board = create_board()
    player = 1
    history: list[tuple[int, Move]] = []
    scenarios = {"opening": {"board": [r[:] for r in board], "player": player, "moves": []}}
    targets = {24: "midgame", 50: "endgame"}
    while len(history) < 50 and not is_terminal(board):
        moves = get_valid_moves(board, player)
        if not moves:
            player = -player
            continue
        move = sorted(moves)[0]
        history.append((player, move))
        board = apply_move(board, *move, player)
        next_player = get_next_player(board, player)
        if next_player is None:
            break
        player = next_player
        if len(history) in targets:
            scenarios[targets[len(history)]] = {
                "board": [r[:] for r in board], "player": player, "moves": history[:]}
    if len(scenarios) != 3:
        raise RuntimeError("Engine ended the deterministic scenario trajectory before 50 moves")
    return scenarios
