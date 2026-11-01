"""Streamlit Othello UI. Run with python -m streamlit run app.py."""
from experiments.common import search


def main() -> None:
    """Render the board and process only explicitly requested AI turns."""
    import streamlit as st
    st.set_page_config(page_title="Othello AI", page_icon="⚫")
    page = st.sidebar.radio("Halaman", ["Permainan", "Eksperimen"], key="page")
    if page == "Eksperimen":
        from experiments.ui import render_experiments
        render_experiments()
        return
    st.title("Othello — Adversarial Search")
    try:
        from game.board import create_board
        from game.engine import (apply_move, get_next_player, get_score,
                                 get_valid_moves, get_winner, is_terminal)
        from algorithms.alphabeta import get_best_move as _alphabeta
        from algorithms.mcts import get_best_move as _mcts
    except ImportError as exc:
        st.error("Modul anggota 1–3 belum lengkap. Lengkapi Game Engine, Alpha-Beta, dan MCTS sesuai kontrak API.")
        st.code(str(exc))
        return

    with st.sidebar:
        st.header("Pengaturan permainan baru")
        mode = st.selectbox("Mode", ["Human vs Human", "Human vs AI", "AI vs AI"])
        human = st.selectbox("Warna manusia", [1, -1], format_func=lambda p: "Hitam" if p == 1 else "Putih") if mode == "Human vs AI" else 1
        settings = {}
        for player, label in ((1, "Hitam"), (-1, "Putih")):
            is_ai = mode == "AI vs AI" or (mode == "Human vs AI" and player != human)
            algorithm = st.selectbox(f"Algoritma {label}", ["alphabeta", "mcts"], key=f"algo_{player}", disabled=not is_ai)
            depth = st.number_input(f"Depth {label}", min_value=1, value=4, step=1, key=f"depth_{player}")
            iterations = st.number_input(f"Iterations {label}", min_value=1, value=500, step=1, key=f"iter_{player}")
            settings[player] = {"ai": is_ai, "algorithm": algorithm,
                                "parameter": int(depth if algorithm == "alphabeta" else iterations)}
        seed = int(st.number_input("Seed MCTS", min_value=0, value=42, step=1))
        new_game = st.button("New Game", use_container_width=True)
        reset = st.button("Reset", use_container_width=True)
        st.caption("New Game menerapkan pengaturan di atas. Reset mengulang konfigurasi permainan aktif.")

    state = st.session_state
    if "board" not in state or new_game or reset:
        if "config" not in state or new_game:
            state.config = {"players": settings, "seed": seed, "mode": mode}
        state.board = create_board()
        state.player = 1
        state.last_stats = None
        state.last_ai = None
        state.placements = 0
        state.notice = ""

    board, player = state.board, state.player
    terminal = is_terminal(board)
    if not terminal and not get_valid_moves(board, player):
        state.notice = f"{'Hitam' if player == 1 else 'Putih'} pass karena tidak memiliki langkah legal."
        state.player = -player
        player = state.player
    black_score, white_score = get_score(board)
    st.write(f"**Hitam: {black_score} · Putih: {white_score}**")
    st.caption(f"Mode aktif: {state.config['mode']}")
    if state.notice:
        st.info(state.notice)
    if terminal:
        winner = get_winner(board)
        st.success("Seri!" if winner == 0 else f"Pemenang: {'Hitam' if winner == 1 else 'Putih'}")
    else:
        st.write(f"Giliran: **{'Hitam' if player == 1 else 'Putih'}**")
    config = state.config["players"][player]
    legal = get_valid_moves(board, player) if not terminal else []

    def play(move: tuple[int, int]) -> None:
        next_board = apply_move(state.board, *move, state.player)
        next_player = get_next_player(next_board, state.player)
        state.notice = ""
        if next_player == state.player:
            state.notice = "Lawan pass karena tidak memiliki langkah legal."
        state.board = next_board
        if next_player is not None:
            state.player = next_player
        state.placements += 1

    symbols = {1: "⚫", -1: "⚪", 0: " "}
    headings = st.columns(9)
    for col in range(8):
        headings[col + 1].markdown(f"**{chr(65 + col)}**")
    for row in range(8):
        cells = st.columns(9)
        cells[0].write(str(row + 1))
        for col in range(8):
            enabled = not terminal and not config["ai"] and (row, col) in legal
            label = "🟢" if enabled else symbols[board[row][col]]
            if cells[col + 1].button(label, key=f"cell_{row}_{col}", disabled=not enabled,
                                      use_container_width=True, help=f"{chr(65 + col)}{row + 1}"):
                play((row, col))
                st.rerun()
    if not terminal and not config["ai"]:
        st.caption("🟢 menandai langkah legal.")
    if not terminal and config["ai"]:
        # Explicit stepping prevents reruns from repeating expensive searches.
        if st.button("Jalankan giliran AI", type="primary"):
            with st.spinner("AI sedang mencari langkah..."):
                move, stats = search(config["algorithm"], [r[:] for r in board], player,
                                     config["parameter"], state.config["seed"] + state.placements)
            if move not in legal:
                st.error(f"AI mengembalikan langkah ilegal: {move!r}")
            else:
                state.last_stats = stats
                state.last_ai = config["algorithm"]
                play(move)
                st.rerun()
    if state.last_stats is not None:
        st.subheader(f"Statistik AI terakhir ({state.last_ai})")
        st.json(state.last_stats)


if __name__ == "__main__":
    main()
