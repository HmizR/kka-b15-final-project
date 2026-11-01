from __future__ import annotations
import math
import random
from typing import Dict, List, Optional, Sequence, Tuple
BOARD_SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = -1
EXPLORATION_CONSTANT = math.sqrt(2)
Move = Tuple[int, int]
_N = BOARD_SIZE
_SQUARES = _N * _N
_PASS = -1
_OPPONENT = {BLACK: WHITE, WHITE: BLACK}

def _to_flat(board: Sequence[Sequence[int]]) -> List[int]:
    rows = getattr(board, 'grid', board)
    if len(rows) != _N or any((len(row) != _N for row in rows)):
        raise ValueError(f'board harus berukuran {_N}x{_N}')
    flat: List[int] = []
    for row in rows:
        for cell in row:
            if cell == BLACK:
                flat.append(BLACK)
            elif cell == WHITE:
                flat.append(WHITE)
            elif cell is None or cell == EMPTY:
                flat.append(EMPTY)
            else:
                raise ValueError(f'nilai sel tidak dikenal: {cell!r}')
    return flat

def _build_rays() -> List[List[Tuple[int, ...]]]:
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    rays: List[List[Tuple[int, ...]]] = []
    for sq in range(_SQUARES):
        r0, c0 = divmod(sq, _N)
        square_rays = []
        for dr, dc in directions:
            ray = []
            r, c = (r0 + dr, c0 + dc)
            while 0 <= r < _N and 0 <= c < _N:
                ray.append(r * _N + c)
                r += dr
                c += dc
            if len(ray) >= 2:
                square_rays.append(tuple(ray))
        rays.append(square_rays)
    return rays
_RAYS = _build_rays()

def _flips(board: List[int], sq: int, player: int, opp: int) -> List[int]:
    flipped: List[int] = []
    for ray in _RAYS[sq]:
        line: List[int] = []
        for i in ray:
            v = board[i]
            if v == opp:
                line.append(i)
            elif v == player:
                if line:
                    flipped.extend(line)
                break
            else:
                break
    return flipped

def _is_legal(board: List[int], sq: int, player: int, opp: int) -> bool:
    if board[sq] != EMPTY:
        return False
    for ray in _RAYS[sq]:
        seen_opp = False
        for i in ray:
            v = board[i]
            if v == opp:
                seen_opp = True
            elif v == player:
                if seen_opp:
                    return True
                break
            else:
                break
    return False

def _legal_moves(board: List[int], player: int) -> List[int]:
    opp = _OPPONENT[player]
    return [sq for sq in range(_SQUARES) if _is_legal(board, sq, player, opp)]

def _has_moves(board: List[int], player: int) -> bool:
    opp = _OPPONENT[player]
    return any((_is_legal(board, sq, player, opp) for sq in range(_SQUARES)))

def _is_terminal(board: List[int]) -> bool:
    return not _has_moves(board, BLACK) and (not _has_moves(board, WHITE))

def _apply_inplace(board: List[int], sq: int, player: int) -> None:
    opp = _OPPONENT[player]
    for i in _flips(board, sq, player, opp):
        board[i] = player
    board[sq] = player

def _reward(board: List[int], player: int) -> float:
    mine = board.count(player)
    theirs = board.count(_OPPONENT[player])
    if mine > theirs:
        return 1.0
    if mine == theirs:
        return 0.5
    return 0.0

class MCTSNode:
    __slots__ = ('board', 'player', 'parent', 'children', 'visits', 'total_reward', 'move', 'mover', 'untried')

    def __init__(self, board: List[int], player: int, parent: Optional['MCTSNode']=None, move: Optional[int]=None, mover: Optional[int]=None) -> None:
        self.board = board
        self.player = player
        self.parent = parent
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.total_reward = 0.0
        self.move = move
        self.mover = mover
        moves = _legal_moves(board, player)
        if moves:
            self.untried: List[int] = moves
        elif _has_moves(board, _OPPONENT[player]):
            self.untried = [_PASS]
        else:
            self.untried = []

    @property
    def is_terminal(self) -> bool:
        return not self.untried and (not self.children)

    def expand(self, move: int) -> 'MCTSNode':
        if move == _PASS:
            child_board = self.board
        else:
            child_board = self.board[:]
            _apply_inplace(child_board, move, self.player)
        child = MCTSNode(child_board, _OPPONENT[self.player], parent=self, move=move, mover=self.player)
        self.children.append(child)
        return child

def _best_uct_child(node: MCTSNode, c: float) -> MCTSNode:
    log_n = math.log(node.visits)
    best: Optional[MCTSNode] = None
    best_score = -math.inf
    for child in node.children:
        score = child.total_reward / child.visits + c * math.sqrt(log_n / child.visits)
        if score > best_score:
            best, best_score = (child, score)
    assert best is not None
    return best

def _rollout(board: List[int], player: int, rng: random.Random) -> List[int]:
    b = board[:]
    consecutive_passes = 0
    while consecutive_passes < 2:
        moves = _legal_moves(b, player)
        if moves:
            _apply_inplace(b, moves[rng.randrange(len(moves))], player)
            consecutive_passes = 0
        else:
            consecutive_passes += 1
        player = _OPPONENT[player]
    return b

def _backpropagate(node: Optional[MCTSNode], final_board: List[int]) -> None:
    while node is not None:
        node.visits += 1
        node.total_reward += _reward(final_board, node.mover)
        node = node.parent

def _tree_depth(root: MCTSNode) -> int:
    depth = 0
    stack = [(root, 0)]
    while stack:
        node, d = stack.pop()
        depth = max(depth, d)
        stack.extend(((ch, d + 1) for ch in node.children))
    return depth

def _run(flat_board: List[int], player: int, iterations: int, rng: random.Random, c: float) -> Tuple[MCTSNode, int, int, int]:
    root = MCTSNode(flat_board, player, mover=_OPPONENT[player])
    tree_size = 1
    simulations = 0
    nodes_visited = 0
    if not root.untried or root.untried == [_PASS]:
        return (root, simulations, tree_size, nodes_visited)
    for _ in range(iterations):
        node = root
        path_length = 1
        while not node.untried and node.children:
            node = _best_uct_child(node, c)
            path_length += 1
        if node.untried:
            move = node.untried.pop(rng.randrange(len(node.untried)))
            node = node.expand(move)
            tree_size += 1
            path_length += 1
        nodes_visited += path_length
        final_board = _rollout(node.board, node.player, rng)
        simulations += 1
        _backpropagate(node, final_board)
    return (root, simulations, tree_size, nodes_visited)

def _choose_move(root: MCTSNode) -> Tuple[Optional[int], float]:
    visits: Dict[int, int] = {ch.move: ch.visits for ch in root.children}
    value: Dict[int, float] = {ch.move: ch.total_reward / ch.visits for ch in root.children if ch.visits}
    legal = _legal_moves(root.board, root.player)
    if not legal:
        return (None, 0.0)
    best = max(legal, key=lambda sq: (visits.get(sq, 0), -sq))
    return (best, value.get(best, 0.0))

def get_best_move(board: Sequence[Sequence[int]], player: int, iterations: int=1000, seed: Optional[int]=None, exploration: float=EXPLORATION_CONSTANT) -> Tuple[Optional[Move], Dict[str, int]]:
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 1:
        raise ValueError('iterations harus integer >= 1')
    if player not in _OPPONENT:
        raise ValueError('player harus BLACK atau WHITE')
    rng = random.Random(seed)
    root, simulations, tree_size, nodes_visited = _run(_to_flat(board), player, iterations, rng, exploration)
    sq, _ = _choose_move(root)
    stats: Dict[str, int] = {'nodes_visited': nodes_visited, 'nodes_expanded': tree_size - 1, 'max_depth_reached': _tree_depth(root), 'simulations': simulations, 'tree_size': tree_size}
    move = None if sq is None else divmod(sq, _N)
    return (move, stats)