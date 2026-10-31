"""Serial time and Python allocation measurements, independent of Streamlit."""
import argparse
import csv
from pathlib import Path
import time
import tracemalloc

from experiments.common import Board


def benchmark(algorithm: str, board: Board, player: int, parameter: int,
              repetitions: int = 30, seed: int = 42) -> list[dict]:
    """Measure AI calls on identical board copies, with independent tracing."""
    if algorithm not in ("alphabeta", "mcts"):
        raise ValueError("algorithm must be alphabeta or mcts")
    if isinstance(parameter, bool) or not isinstance(parameter, int) or parameter < 1:
        raise ValueError("parameter must be a positive integer")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        raise ValueError("repetitions must be a positive integer")
    if player not in (1, -1):
        raise ValueError("player must be 1 or -1")
    if tracemalloc.is_tracing():
        raise RuntimeError("Stop existing tracemalloc tracing before benchmarking")
    # Resolve imports before timing and tracing the algorithm invocation.
    from importlib import import_module
    ai = import_module(f"algorithms.{algorithm}").get_best_move
    rows = []
    for repetition in range(repetitions):
        sample = [row[:] for row in board]
        kwargs = {"depth": parameter} if algorithm == "alphabeta" else {
            "iterations": parameter, "seed": seed + repetition}
        tracemalloc.start()
        try:
            started = time.perf_counter_ns()
            _, stats = ai(sample, player, **kwargs)
            elapsed = time.perf_counter_ns() - started
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        rows.append({**stats, "algorithm": algorithm, "parameter": parameter,
                     "repetition": repetition, "seed": seed + repetition if algorithm == "mcts" else None,
                     "execution_time_ms": elapsed / 1_000_000,
                     "peak_memory_bytes": peak})
    return rows


def save_csv(rows: list[dict], output: str | Path) -> None:
    """Write records including algorithm-specific fields as a UTF-8 CSV."""
    if not rows:
        raise ValueError("No records to save")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Run a reproducible benchmark from the project root."""
    from experiments.scenarios import get_scenarios
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("algorithm", choices=["alphabeta", "mcts"])
    parser.add_argument("--parameter", type=int, required=True)
    parser.add_argument("--scenario", choices=["opening", "midgame", "endgame"], default="opening")
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/benchmark.csv")
    args = parser.parse_args()
    scenario = get_scenarios()[args.scenario]
    rows = benchmark(args.algorithm, scenario["board"], scenario["player"],
                     args.parameter, args.repetitions, args.seed)
    save_csv([{**row, "scenario": args.scenario} for row in rows], args.output)


if __name__ == "__main__":
    main()
