"""Verify experiment controls, dispatch, retained results and CSV downloads."""
import csv
import io
from pathlib import Path

from streamlit.testing.v1 import AppTest

from experiments import ui


def _app():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=15).run()
    app.radio(key="page").set_value("Eksperimen").run()
    assert not app.exception
    return app


def _click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_benchmark_controls_csv_and_rerun(monkeypatch):
    calls = []

    def fake_benchmark(algorithm, board, player, parameter, repetitions, seed):
        calls.append((algorithm, player, parameter, repetitions, seed))
        return [{"algorithm": algorithm, "parameter": parameter, "repetition": i,
                 "execution_time_ms": i + 1.0, "peak_memory_bytes": 1024,
                 "nodes_visited": 2, "nodes_expanded": 1, "max_depth_reached": 1}
                for i in range(repetitions)]

    monkeypatch.setattr(ui, "benchmark", fake_benchmark)
    app = _app()
    assert not calls
    app.number_input(key="bench_depth").set_value(2)
    app.number_input(key="bench_iterations").set_value(10)
    app.number_input(key="bench_repetitions").set_value(2)
    app.number_input(key="bench_seed").set_value(7)
    app.selectbox(key="bench_scenario").select("midgame")
    _click(app, "Jalankan benchmark")
    assert [(c[0], c[2:]) for c in calls] == [("alphabeta", (2, 2, 7)), ("mcts", (10, 2, 7))]
    result = app.session_state["benchmark_result"]
    assert len(result["rows"]) == 4
    assert all(row["scenario"] == "midgame" for row in result["rows"])
    exported = list(csv.DictReader(io.StringIO(ui._csv_bytes(result["rows"]).decode("utf-8-sig"))))
    assert len(exported) == 4 and exported[0]["parameter"] == "2"
    app.run()
    app.radio(key="page").set_value("Permainan").run()
    app.radio(key="page").set_value("Eksperimen").run()
    assert len(calls) == 2 and app.session_state["benchmark_result"] == result
    assert len(app.get("download_button")) == 1


def test_tournament_dispatch_and_no_results_file_overwrite(monkeypatch):
    calls = []

    def fake_tournament(**kwargs):
        calls.append(kwargs)
        assert Path(kwargs["output"]).parent.exists()
        return [{"game": index, "winner_algorithm": winner, "black_score": 40,
                 "white_score": 24, "duration_seconds": 1.0}
                for index, winner in enumerate(("alphabeta", "mcts", "draw", "alphabeta"))]

    monkeypatch.setattr(ui, "tournament", fake_tournament)
    app = _app()
    app.number_input(key="tourney_pairs").set_value(2)
    app.number_input(key="tourney_depth").set_value(1)
    app.number_input(key="tourney_iterations").set_value(3)
    app.number_input(key="tourney_seed").set_value(9)
    _click(app, "Jalankan tournament")
    assert len(calls) == 1
    assert {key: value for key, value in calls[0].items() if key != "output"} == {
        "pairs": 2, "depth": 1, "iterations": 3, "seed": 9}
    assert Path(calls[0]["output"]).resolve() != Path("results/tournament.csv").resolve()
    assert [metric.value for metric in app.metric] == ["2", "1", "1"]
    assert len(app.get("download_button")) == 1
    app.run()
    assert len(calls) == 1


def test_empty_selection_and_failed_run_show_errors(monkeypatch):
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("contoh kegagalan")

    monkeypatch.setattr(ui, "benchmark", fail)
    app = _app()
    app.multiselect(key="bench_algorithms").set_value([])
    _click(app, "Jalankan benchmark")
    assert not calls and "Pilih minimal" in app.error[0].value
    app.multiselect(key="bench_algorithms").set_value(["mcts"])
    _click(app, "Jalankan benchmark")
    assert calls == [1] and "contoh kegagalan" in app.error[0].value
    assert "benchmark_result" not in app.session_state


def test_real_small_experiments_and_game_survives_navigation():
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=15).run()
    app.button(key="cell_2_3").click().run()
    board = [row[:] for row in app.session_state["board"]]
    app.radio(key="page").set_value("Eksperimen").run()
    app.number_input(key="bench_depth").set_value(1)
    app.number_input(key="bench_iterations").set_value(1)
    app.number_input(key="bench_repetitions").set_value(1)
    _click(app, "Jalankan benchmark")
    assert len(app.session_state["benchmark_result"]["rows"]) == 2
    app.number_input(key="tourney_depth").set_value(1)
    app.number_input(key="tourney_iterations").set_value(1)
    _click(app, "Jalankan tournament")
    assert len(app.session_state["tournament_result"]["rows"]) == 2
    assert len(app.get("download_button")) == 2
    app.radio(key="page").set_value("Permainan").run()
    assert app.session_state["board"] == board
    assert not app.exception
