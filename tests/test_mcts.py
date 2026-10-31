import copy
import random
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms import mcts as m
from algorithms.mcts import BLACK, EMPTY, WHITE, get_best_move

def initial_board():
    b = [[EMPTY] * 8 for _ in range(8)]
    b[3][3], b[4][4] = (WHITE, WHITE)
    b[3][4], b[4][3] = (BLACK, BLACK)
    return b

def flat(board):
    return m._to_flat(board)

def legal_coords(board, player):
    return [divmod(sq, 8) for sq in m._legal_moves(flat(board), player)]

def full_board(color):
    return [[color] * 8 for _ in range(8)]

def black_must_pass_board():
    b = [[EMPTY] * 8 for _ in range(8)]
    b[0][0] = WHITE
    b[0][1] = BLACK
    return b

def late_game_board(seed, empties):
    rng = random.Random(seed)
    while True:
        b = flat(initial_board())
        p = BLACK
        passes = 0
        while passes < 2 and b.count(EMPTY) > empties:
            moves = m._legal_moves(b, p)
            if moves:
                m._apply_inplace(b, rng.choice(moves), p)
                passes = 0
            else:
                passes += 1
            p = m._OPPONENT[p]
        if passes < 2 and m._legal_moves(b, p):
            return ([b[i * 8:(i + 1) * 8] for i in range(8)], p)

@pytest.mark.parametrize('bad', [0, -1, -100, 1.5, '10', None, True])
def test_iterations_invalid_raises_value_error(bad):
    with pytest.raises(ValueError):
        get_best_move(initial_board(), BLACK, iterations=bad, seed=0)

def test_invalid_player_raises_value_error():
    with pytest.raises(ValueError):
        get_best_move(initial_board(), 99, iterations=5, seed=0)

@pytest.mark.parametrize('iterations', [1, 100, 500, 1000])
@pytest.mark.parametrize('player', [BLACK, WHITE])
def test_returns_legal_move(iterations, player):
    board = initial_board()
    move, stats = get_best_move(board, player, iterations=iterations, seed=7)
    assert move in legal_coords(board, player)
    assert stats['simulations'] == iterations

def test_deterministic_with_same_seed_and_input():
    a = get_best_move(initial_board(), BLACK, iterations=300, seed=42)
    b = get_best_move(initial_board(), BLACK, iterations=300, seed=42)
    assert a == b

def test_input_board_not_modified():
    board = initial_board()
    snapshot = copy.deepcopy(board)
    get_best_move(board, BLACK, iterations=200, seed=1)
    assert board == snapshot

def test_global_random_state_untouched():
    random.seed(123)
    before = random.getstate()
    get_best_move(initial_board(), BLACK, iterations=50, seed=5)
    assert random.getstate() == before

def test_stats_fields():
    _, stats = get_best_move(initial_board(), BLACK, iterations=100, seed=3)
    assert stats['simulations'] == 100
    assert 2 <= stats['tree_size'] <= 101
    assert stats['nodes_expanded'] == stats['tree_size'] - 1

def test_at_most_one_new_node_per_iteration():
    for n in (1, 2, 10, 123):
        _, stats = get_best_move(initial_board(), BLACK, iterations=n, seed=0)
        assert stats['tree_size'] <= n + 1
        assert stats['tree_size'] == n + 1

def test_visit_counts_consistent():
    root, sims, size = m._run(flat(initial_board()), BLACK, 400, random.Random(0), m.EXPLORATION_CONSTANT)
    assert root.visits == sims == 400
    assert sum((ch.visits for ch in root.children)) == root.visits
    count, stack = (0, [root])
    while stack:
        node = stack.pop()
        count += 1
        stack.extend(node.children)
        assert node.visits >= sum((ch.visits for ch in node.children))
    assert count == size

def test_final_move_ties_choose_smallest_coordinate():
    board = initial_board()
    move, _ = get_best_move(board, BLACK, iterations=1, seed=0)
    assert move in legal_coords(board, BLACK)
    root = m.MCTSNode(flat(board), BLACK)
    for sq in list(root.untried):
        child = root.expand(sq)
        child.visits = 5
    root.untried.clear()
    sq, _ = m._choose_move(root)
    assert divmod(sq, 8) == min(legal_coords(board, BLACK))

def test_unvisited_root_children_have_zero_visits_and_lose_to_visited():
    board = initial_board()
    root, _, _ = m._run(flat(board), BLACK, 2, random.Random(0), m.EXPLORATION_CONSTANT)
    assert len(root.children) == 2 and len(root.untried) == 2
    sq, _ = m._choose_move(root)
    assert sq in {ch.move for ch in root.children}

def test_uct_maximizes_reward_of_player_choosing():
    root = m.MCTSNode(flat(initial_board()), BLACK)
    good = root.expand(root.untried.pop(0))
    bad = root.expand(root.untried.pop(0))
    good.visits, good.total_reward = (10, 9.0)
    bad.visits, bad.total_reward = (10, 1.0)
    root.visits = 20
    assert m._best_uct_child(root, m.EXPLORATION_CONSTANT) is good

def test_uct_formula():
    root = m.MCTSNode(flat(initial_board()), BLACK)
    a = root.expand(root.untried.pop(0))
    b = root.expand(root.untried.pop(0))
    a.visits, a.total_reward = (4, 2.0)
    b.visits, b.total_reward = (1, 0.0)
    root.visits = 5
    ua = 2.0 / 4 + m.EXPLORATION_CONSTANT * (m.math.log(5) / 4) ** 0.5
    ub = 0.0 + m.EXPLORATION_CONSTANT * (m.math.log(5) / 1) ** 0.5
    assert ub > ua
    assert m._best_uct_child(root, m.EXPLORATION_CONSTANT) is b

def test_terminal_rewards():
    assert m._reward(flat(full_board(BLACK)), BLACK) == 1.0
    assert m._reward(flat(full_board(BLACK)), WHITE) == 0.0
    b = [[BLACK] * 4 + [WHITE] * 4 for _ in range(8)]
    assert m._reward(flat(b), BLACK) == 0.5

def test_rollouts_end_in_valid_terminal_state():
    rng = random.Random(9)
    start = flat(initial_board())
    for _ in range(30):
        end = m._rollout(start, BLACK, rng)
        assert m._is_terminal(end)
        assert set(end) <= {EMPTY, BLACK, WHITE}
        assert end.count(BLACK) + end.count(WHITE) >= 4
    assert start == flat(initial_board())

def test_terminal_board_returns_none():
    move, stats = get_best_move(full_board(BLACK), BLACK, iterations=10, seed=0)
    assert move is None
    assert stats['simulations'] == 0 and stats['tree_size'] == 1

def test_pass_state_returns_none_and_is_explicit_transition():
    board = black_must_pass_board()
    assert legal_coords(board, BLACK) == []
    assert legal_coords(board, WHITE) != []
    move, _ = get_best_move(board, BLACK, iterations=20, seed=0)
    assert move is None
    node = m.MCTSNode(flat(board), BLACK)
    assert node.untried == [m._PASS]
    child = node.expand(m._PASS)
    assert child.board == node.board
    assert child.player == WHITE
    assert child.mover == BLACK

def test_pass_inside_tree_is_handled():
    board = black_must_pass_board()
    move, stats = get_best_move(board, WHITE, iterations=100, seed=0)
    assert move == (0, 2)
    assert stats['simulations'] == 100

def test_pass_nodes_keep_board_and_switch_player():
    found = 0
    for seed in range(12):
        board, player = late_game_board(seed, empties=8)
        root, _, _ = m._run(flat(board), player, 300, random.Random(seed), m.EXPLORATION_CONSTANT)
        stack = [root]
        while stack:
            node = stack.pop()
            stack.extend(node.children)
            if node.move == m._PASS:
                found += 1
                assert node.board == node.parent.board
                assert node.player == m._OPPONENT[node.parent.player]
                assert len(node.parent.children) == 1
    assert found > 0

@pytest.mark.parametrize('seed', range(5))
def test_prefers_winning_move_near_endgame(seed):
    board, player = late_game_board(seed, empties=4)
    fb = flat(board)

    def solve(b, p, passes=0):
        moves = m._legal_moves(b, p)
        if not moves:
            if passes == 1:
                return m._reward(b, player)
            return solve(b, m._OPPONENT[p], 1)
        vals = []
        for sq in moves:
            nb = b[:]
            m._apply_inplace(nb, sq, p)
            vals.append(solve(nb, m._OPPONENT[p]))
        return max(vals) if p == player else min(vals)
    values = {}
    for sq in m._legal_moves(fb, player):
        nb = fb[:]
        m._apply_inplace(nb, sq, player)
        values[sq] = solve(nb, m._OPPONENT[player])
    best_value = max(values.values())
    move, _ = get_best_move(board, player, iterations=1000, seed=seed)
    assert values[move[0] * 8 + move[1]] == best_value