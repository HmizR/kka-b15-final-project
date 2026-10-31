"""Infrastructure tests run now; real integration runs once members 1–3 land."""
import csv
import importlib
from pathlib import Path
import sys
import tracemalloc
from types import ModuleType

import pytest

from experiments.benchmark import benchmark, save_csv
from experiments.tournament import tournament


@pytest.fixture
def fake_ais(monkeypatch):
    """Provide API-compatible algorithms without implementing teammates' AI."""
    calls = []
    for name in ("alphabeta", "mcts"):
        module = ModuleType(f"algorithms.{name}")

        def ai(board, player, _name=name, **kwargs):
            calls.append((_name, [row[:] for row in board], player, kwargs))
            move = (0, 0) if board[0][0] == 0 else (0, 1)
            board[0][0] = 99  # Verify caller isolation, even with a misbehaving AI.
            return move, {"nodes_visited": 2, "nodes_expanded": 1,
                          "max_depth_reached": 1, "extra_metric": 7}

        module.get_best_move = ai
        monkeypatch.setitem(sys.modules, f"algorithms.{name}", module)
    return calls


def test_benchmark_copies_seeds_metrics_and_csv(fake_ais, tmp_path):
    board = [[0] * 8 for _ in range(8)]
    rows = benchmark("mcts", board, 1, 100, repetitions=3, seed=42)
    assert [call[3]["seed"] for call in fake_ais] == [42, 43, 44]
    assert all(call[1] == board for call in fake_ais)
    assert board == [[0] * 8 for _ in range(8)]
    assert not tracemalloc.is_tracing()
    assert all(row["execution_time_ms"] >= 0 and row["peak_memory_bytes"] >= 0 for row in rows)
    assert [row["repetition"] for row in rows] == [0, 1, 2]
    assert all(row["extra_metric"] == 7 for row in rows)
    path = tmp_path / "nested" / "benchmark.csv"
    save_csv(rows, path)
    with path.open(encoding="utf-8", newline="") as handle:
        assert len(list(csv.DictReader(handle))) == 3


def test_alphabeta_dispatch(fake_ais):
    benchmark("alphabeta", [[0] * 8 for _ in range(8)], -1, 4, 1)
    assert fake_ais[0][3] == {"depth": 4}


@pytest.mark.parametrize("kwargs", [{"algorithm": "bad"}, {"parameter": 0},
                                     {"repetitions": 0}, {"player": 0}])
def test_benchmark_validation(kwargs):
    arguments = dict(algorithm="mcts", board=[[0] * 8 for _ in range(8)],
                     player=1, parameter=1)
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        benchmark(**arguments)


def test_benchmark_cleans_tracing_on_failure(monkeypatch):
    module = ModuleType("algorithms.mcts")

    def fail(*args, **kwargs):
        raise RuntimeError("search failed")

    module.get_best_move = fail
    monkeypatch.setitem(sys.modules, "algorithms.mcts", module)
    with pytest.raises(RuntimeError, match="search failed"):
        benchmark("mcts", [[0] * 8 for _ in range(8)], 1, 1, 1)
    assert not tracemalloc.is_tracing()


def test_tournament_balance_pass_seed_and_csv(fake_ais, monkeypatch, tmp_path):
    # Script a two-placement game where WHITE initially must pass.
    board_module = ModuleType("game.board")
    engine = ModuleType("game.engine")
    board_module.create_board = lambda: [[0, 0]]
    engine.is_terminal = lambda board: board[0][1] != 0
    engine.get_valid_moves = lambda board, player: ([] if player == -1 else
                                                   [(0, 0)] if board[0][0] == 0 else [(0, 1)])

    def apply(board, row, col, player):
        result = [r[:] for r in board]
        result[row][col] = player
        return result

    engine.apply_move = apply
    engine.get_next_player = lambda board, player: None if engine.is_terminal(board) else player
    engine.get_score = lambda board: (2, 0)
    engine.get_winner = lambda board: 1
    monkeypatch.setitem(sys.modules, "game.board", board_module)
    monkeypatch.setitem(sys.modules, "game.engine", engine)
    output = tmp_path / "matches.csv"
    records = tournament(pairs=2, depth=1, iterations=1, seed=42, output=output)
    assert [r["black_algorithm"] for r in records] == ["alphabeta", "mcts"] * 2
    assert [r["mcts_seed"] for r in records] == [42, 42, 1042, 1042]
    assert all(r["moves"] == 2 and r["black_score"] == 2 for r in records)
    assert [c[3]["seed"] for c in fake_ais if c[0] == "mcts"] == [42, 43, 1042, 1043]
    assert output.is_file()


def test_scenario_generation_uses_engine_and_keeps_independent_snapshots(monkeypatch):
    from experiments.scenarios import get_scenarios
    board_module = ModuleType("game.board")
    engine = ModuleType("game.engine")
    board_module.create_board = lambda: [[0] * 8 for _ in range(8)]
    engine.is_terminal = lambda board: all(v != 0 for r in board for v in r)
    engine.get_valid_moves = lambda board, player: [(r, c) for r in range(8)
                                                    for c in range(8) if board[r][c] == 0]

    def apply(board, row, col, player):
        result = [r[:] for r in board]
        result[row][col] = player
        return result

    engine.apply_move = apply
    engine.get_next_player = lambda board, player: -player
    monkeypatch.setitem(sys.modules, "game.board", board_module)
    monkeypatch.setitem(sys.modules, "game.engine", engine)
    scenarios = get_scenarios()
    assert [len(scenarios[name]["moves"]) for name in ("opening", "midgame", "endgame")] == [0, 24, 50]
    assert scenarios["endgame"]["moves"][:24] == scenarios["midgame"]["moves"]
    scenarios["midgame"]["board"][0][0] = 99
    assert scenarios["opening"]["board"][0][0] == 0
    assert scenarios["endgame"]["board"][0][0] == 1


@pytest.fixture
def real_api():
    required = {
        "game.board": ["create_board"],
        "game.engine": ["apply_move", "get_next_player", "get_valid_moves", "is_terminal", "get_score", "get_winner"],
        "algorithms.alphabeta": ["get_best_move"], "algorithms.mcts": ["get_best_move"]}
    for name, functions in required.items():
        module = importlib.import_module(name)
        missing = [function for function in functions if not callable(getattr(module, function, None))]
        if missing:
            pytest.skip(f"Modul anggota 1–3 belum tersedia: {name}: {', '.join(missing)}")


def test_real_scenarios_replay_and_ai_contract(real_api):
    from experiments.scenarios import get_scenarios
    from experiments.common import search
    from game.board import create_board
    from game.engine import apply_move, get_next_player, get_valid_moves
    scenarios = get_scenarios()
    for name, placements in (("opening", 0), ("midgame", 24), ("endgame", 50)):
        scenario = scenarios[name]
        board, player = create_board(), 1
        assert len(scenario["moves"]) == placements
        for mover, move in scenario["moves"]:
            assert mover == player
            assert move in get_valid_moves(board, player)
            board = apply_move(board, *move, player)
            player = get_next_player(board, player)
        assert board == scenario["board"] and player == scenario["player"]
        original = [r[:] for r in board]
        for algorithm in ("alphabeta", "mcts"):
            move, stats = search(algorithm, board, player, 1, 42)
            legal = get_valid_moves(board, player)
            assert move in legal if legal else move is None
            assert board == original
            for key in ("nodes_visited", "nodes_expanded", "max_depth_reached"):
                assert isinstance(stats[key], int) and stats[key] >= 0


def test_real_full_tournament(real_api, tmp_path):
    records = tournament(depth=1, iterations=1, output=tmp_path / "real.csv")
    assert len(records) == 2
    assert all(0 < r["moves"] <= 60 for r in records)
    assert all(r["black_score"] + r["white_score"] <= 64 for r in records)


def test_ui_missing_dependencies_message():
    from streamlit.testing.v1 import AppTest
    from game import board
    if callable(getattr(board, "create_board", None)):
        pytest.skip("Missing-dependency screen only applies before engine integration")
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10).run()
    assert not app.exception
    assert "Modul anggota 1–3 belum lengkap" in app.error[0].value


@pytest.mark.parametrize("mode", ["Human vs Human", "Human vs AI", "AI vs AI"])
def test_ui_modes_reset_and_no_repeated_search(fake_ais, monkeypatch, mode):
    from streamlit.testing.v1 import AppTest
    board_module = ModuleType("game.board")
    engine = ModuleType("game.engine")
    board_module.create_board = lambda: [[0] * 8 for _ in range(8)]
    engine.is_terminal = lambda board: board[0][1] != 0
    engine.get_valid_moves = lambda board, player: ([(0, 0)] if board[0][0] == 0 else [(0, 1)])

    def apply(board, row, col, player):
        result = [r[:] for r in board]
        result[row][col] = player
        return result

    engine.apply_move = apply
    engine.get_next_player = lambda board, player: None if engine.is_terminal(board) else -player
    engine.get_score = lambda board: (sum(v == 1 for r in board for v in r),
                                      sum(v == -1 for r in board for v in r))
    engine.get_winner = lambda board: 0
    monkeypatch.setitem(sys.modules, "game.board", board_module)
    monkeypatch.setitem(sys.modules, "game.engine", engine)
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10).run()
    app.selectbox[0].select(mode).run()
    next(b for b in app.button if b.label == "New Game").click().run()
    assert not fake_ais  # Settings reruns never search.
    for turn in range(2):
        is_ai = mode == "AI vs AI" or (mode == "Human vs AI" and turn == 1)
        if is_ai:
            next(b for b in app.button if b.label == "Jalankan giliran AI").click().run()
        else:
            app.button(key=f"cell_0_{turn}").click().run()
        assert not app.exception
    assert app.success[0].value == "Seri!"
    calls = len(fake_ais)
    app.run()
    assert len(fake_ais) == calls
    next(b for b in app.button if b.label == "Reset").click().run()
    assert app.session_state["placements"] == 0
    assert app.session_state["player"] == 1
    assert not app.exception
