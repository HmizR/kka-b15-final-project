"""Streamlit presentation for the existing serial experiment runners."""
import csv
import io
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.benchmark import benchmark
from experiments.scenarios import get_scenarios
from experiments.tournament import tournament


def _csv_bytes(rows: list[dict]) -> bytes:
    buffer = io.StringIO(newline="")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _benchmark_results(result: dict) -> None:
    import pandas as pd
    import streamlit as st

    st.subheader("Hasil benchmark terakhir")
    st.caption("Konfigurasi hasil tersimpan; perubahan input berlaku setelah menjalankan eksperimen lagi.")
    st.json(result["config"], expanded=False)
    frame = pd.DataFrame(result["rows"])
    frame["peak_memory_kib"] = frame["peak_memory_bytes"] / 1024
    summary = frame.groupby("algorithm", sort=False).agg(
        waktu_rata_rata_ms=("execution_time_ms", "mean"),
        waktu_median_ms=("execution_time_ms", "median"),
        waktu_std_ms=("execution_time_ms", "std"),
        memori_rata_rata_kib=("peak_memory_kib", "mean"),
        memori_maksimum_kib=("peak_memory_kib", "max"),
    ).fillna(0)
    st.dataframe(summary, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.markdown("**Rata-rata waktu (ms)**")
        st.bar_chart(summary[["waktu_rata_rata_ms"]])
    with right:
        st.markdown("**Rata-rata peak memory (KiB)**")
        st.bar_chart(summary[["memori_rata_rata_kib"]])
    with st.expander("Statistik pencarian"):
        st.caption("Nodes visited kedua algoritma memiliki definisi komputasi berbeda; jangan disamakan langsung.")
        st.dataframe(frame.groupby("algorithm")[["nodes_visited", "nodes_expanded", "max_depth_reached"]].mean(),
                     use_container_width=True)
    st.markdown("**Data setiap pengulangan**")
    st.dataframe(frame.drop(columns="peak_memory_kib"), use_container_width=True, hide_index=True)
    st.download_button("Unduh CSV benchmark", _csv_bytes(result["rows"]),
                       "benchmark.csv", "text/csv", key="download_benchmark")


def _tournament_results(result: dict) -> None:
    import pandas as pd
    import streamlit as st

    st.subheader("Hasil tournament terakhir")
    st.json(result["config"], expanded=False)
    rows = result["rows"]
    counts = {name: sum(row["winner_algorithm"] == name for row in rows)
              for name in ("alphabeta", "mcts", "draw")}
    for column, name, label in zip(st.columns(3), counts, ("Alpha-Beta menang", "MCTS menang", "Seri")):
        column.metric(label, counts[name])
    st.caption(f"{len(rows)} pertandingan · Total durasi: {sum(row['duration_seconds'] for row in rows):.2f} detik")
    st.bar_chart(pd.DataFrame({"Jumlah pertandingan": counts}))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button("Unduh CSV tournament", _csv_bytes(rows),
                       "tournament.csv", "text/csv", key="download_tournament")


def render_experiments() -> None:
    """Render explicit-run forms and retain results across Streamlit reruns."""
    import streamlit as st

    st.title("Eksperimen Othello")
    st.caption("Ukur performa pencarian dan bandingkan hasil pertandingan dengan konfigurasi yang tercatat.")
    benchmark_tab, tournament_tab = st.tabs(["Benchmark", "Tournament"])
    with benchmark_tab:
        st.subheader("Benchmark pencarian")
        st.write("Jalankan satu atau kedua algoritma pada posisi yang sama. Setiap pengulangan memakai salinan papan identik.")
        with st.form("benchmark_form"):
            algorithms = st.multiselect("Algoritma", ["alphabeta", "mcts"],
                                        default=["alphabeta", "mcts"], key="bench_algorithms")
            scenario = st.selectbox("Skenario", ["opening", "midgame", "endgame"], key="bench_scenario")
            left, right = st.columns(2)
            depth = int(left.number_input("Depth Alpha-Beta", min_value=1, value=4, step=1, key="bench_depth"))
            iterations = int(right.number_input("Iterations MCTS", min_value=1, value=500, step=1, key="bench_iterations"))
            repetitions = int(left.number_input("Pengulangan per algoritma", min_value=1, value=30, step=1, key="bench_repetitions"))
            seed = int(right.number_input("Seed benchmark", min_value=0, value=42, step=1, key="bench_seed"))
            run = st.form_submit_button("Jalankan benchmark", type="primary")
        st.caption(f"Pekerjaan: {len(algorithms) * repetitions} pencarian, dijalankan serial.")
        st.caption("Waktu mencakup pemanggilan AI dengan tracemalloc aktif. Memori adalah peak alokasi Python terlacak, bukan RSS. Parameter besar membutuhkan waktu lebih lama.")
        if run:
            if not algorithms:
                st.error("Pilih minimal satu algoritma.")
            else:
                progress = st.progress(0, text="Menyiapkan benchmark...")
                try:
                    position = get_scenarios()[scenario]
                    rows = []
                    with st.spinner("Benchmark sedang berjalan..."):
                        for index, algorithm in enumerate(algorithms):
                            progress.progress(index / len(algorithms), text=f"Mengukur {algorithm}...")
                            records = benchmark(algorithm, position["board"], position["player"],
                                                depth if algorithm == "alphabeta" else iterations,
                                                repetitions, seed)
                            rows.extend({**row, "scenario": scenario, "player": position["player"]} for row in records)
                    st.session_state.benchmark_result = {"config": {
                        "algorithms": algorithms, "scenario": scenario, "depth": depth,
                        "iterations": iterations, "repetitions": repetitions, "seed": seed,
                        "player": position["player"]}, "rows": rows}
                    progress.progress(1.0, text="Benchmark selesai")
                except Exception as exc:
                    progress.empty()
                    st.error(f"Benchmark gagal: {exc}")
        if "benchmark_result" in st.session_state:
            _benchmark_results(st.session_state.benchmark_result)

    with tournament_tab:
        st.subheader("Alpha-Beta vs MCTS")
        st.write("Setiap pasangan terdiri dari dua pertandingan dengan warna ditukar dan seed dasar yang sama.")
        with st.form("tournament_form"):
            left, right = st.columns(2)
            depth = int(left.number_input("Depth Alpha-Beta", min_value=1, value=4, step=1, key="tourney_depth"))
            iterations = int(right.number_input("Iterations MCTS", min_value=1, value=500, step=1, key="tourney_iterations"))
            pairs = int(left.number_input("Pasangan pertandingan", min_value=1, value=1, step=1, key="tourney_pairs"))
            seed = int(right.number_input("Seed tournament", min_value=0, value=42, step=1, key="tourney_seed"))
            run = st.form_submit_button("Jalankan tournament", type="primary")
        st.caption(f"Pekerjaan: {pairs * 2} pertandingan penuh, dijalankan serial.")
        st.caption("Seed MCTS: seed + indeks pasangan × 1000 + indeks keputusan MCTS. Eksperimen dapat membutuhkan beberapa menit.")
        if run:
            try:
                with st.spinner(f"Menjalankan {pairs * 2} pertandingan..."):
                    # Reuse the runner's CSV contract without overwriting research files.
                    with TemporaryDirectory(prefix="othello-tournament-") as directory:
                        rows = tournament(pairs=pairs, depth=depth, iterations=iterations,
                                          seed=seed, output=Path(directory) / "tournament.csv")
                st.session_state.tournament_result = {"config": {
                    "pairs": pairs, "depth": depth, "iterations": iterations, "seed": seed}, "rows": rows}
            except Exception as exc:
                st.error(f"Tournament gagal: {exc}")
        if "tournament_result" in st.session_state:
            _tournament_results(st.session_state.tournament_result)
