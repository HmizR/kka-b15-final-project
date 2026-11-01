"""Aturan Othello: kelas lama dan API fungsional tanpa mutasi input."""
from game.board import BLACK, EMPTY, WHITE, Board, BoardState, Move, copy_board

class GameEngine:
    """Kelola permainan interaktif menggunakan instance papan sendiri."""
    def __init__(self) -> None:
        """Mulai permainan dengan giliran hitam."""
        self.board = Board()
        self.current_player = Board.BLACK

    # Mengambil pemain yang sedang bermain 
    def get_current_player(self) -> int:
        """Kembalikan pemain aktif."""
        return self.current_player

    # Mengambil langkah pemain saat ini yang valid
    def get_valid_moves(self) -> list[Move]:
        """Kembalikan langkah legal pemain aktif."""
        return self.board.get_valid_moves(self.current_player)

    # Memeriksa apakah permainan sudah berakhir
    def is_game_over(self) -> bool:
        """Periksa apakah kedua pemain tidak dapat bergerak."""
        black_moves = self.board.get_valid_moves(Board.BLACK)
        white_moves = self.board.get_valid_moves(Board.WHITE)

        return (self.board.is_full() or (len(black_moves)==0 and len (white_moves)==0))
    
    # Menjalankan langkah pemain saat ini
    def play_move(self, row: int, col: int) -> list[Move]:
        """Jalankan langkah, lalu pindah giliran; pass tersedia lewat pass_turn."""
        if self.is_game_over():
            raise ValueError("Permainan Sudah Berakhir")
        if not self.board.is_valid_move(row,col, self.current_player):
            raise ValueError("Langkah tidak valid")

        # Menjalankan langkah pada papan
        captured = self.board.apply_move(row, col, self.current_player)

        # pergantian giliran
        self.current_player = self.board.get_opponent(self.current_player)

        return captured

    # Memeriksa apakah pemain saat ini harus pass.
    def must_pass(self) -> bool:
        """Periksa kebutuhan pass pada permainan yang belum selesai."""
        if self.is_game_over():
            return False
        
        return len(self.get_valid_moves()) == 0

    # Melewati giliran jika tidak ada langkah valid
    def pass_turn(self) -> None:
        """Pindahkan giliran hanya ketika pemain tidak dapat bergerak."""
        if self.is_game_over():
            raise ValueError("Permainan Telah Berakhir")

        if not self.must_pass():
            raise ValueError("Pemain masih memiliki langkah valid!")
        
        self.current_player = self.board.get_opponent(self.current_player)
    

    # Menentukan pemenang berdasarkan jumlah bidak
    def get_winner(self) -> int:
        """Kembalikan pemenang terminal, atau EMPTY untuk seri."""
        if not self.is_game_over():
            raise ValueError("Permainan belum berakhir")

        score = self.board.get_score()

        if score[Board.BLACK] > score[Board.WHITE]:
            return Board.BLACK
        elif score[Board.WHITE] > score[Board.BLACK]:
            return Board.WHITE
        else:
            return Board.EMPTY

    # Mengambil score permainan dari dua bidak 
    def get_score(self) -> dict[int, int]:
        """Kembalikan skor dictionary untuk pemakai kelas lama."""
        return self.board.get_score()


def get_flips(board: BoardState, row: int, col: int, player: int) -> list[Move]:
    """Kembalikan flip terurut tanpa mengubah papan."""
    return Board.from_grid(board).get_captured_discs(row, col, player)


def get_valid_moves(board: BoardState, player: int) -> list[Move]:
    """Kembalikan semua langkah legal terurut tanpa mengubah papan."""
    return Board.from_grid(board).get_valid_moves(player)


def apply_move(board: BoardState, row: int, col: int, player: int) -> BoardState:
    """Jalankan langkah pada salinan papan; langkah ilegal ditolak."""
    result = Board.from_grid(copy_board(board))
    result.apply_move(row, col, player)
    return result.grid


def has_valid_move(board: BoardState, player: int) -> bool:
    """Periksa apakah pemain mempunyai langkah legal."""
    return bool(get_valid_moves(board, player))


def is_terminal(board: BoardState) -> bool:
    """Permainan selesai ketika kedua pemain tidak memiliki langkah legal."""
    return not has_valid_move(board, BLACK) and not has_valid_move(board, WHITE)


def get_next_player(board: BoardState, current_player: int) -> int | None:
    """Tentukan giliran setelah langkah, termasuk pass lawan dan terminal."""
    opponent = Board.from_grid(board).get_opponent(current_player)
    if has_valid_move(board, opponent):
        return opponent
    if has_valid_move(board, current_player):
        return current_player
    return None


def get_score(board: BoardState) -> tuple[int, int]:
    """Kembalikan jumlah bidak (hitam, putih)."""
    scores = Board.from_grid(board).get_score()
    return scores[BLACK], scores[WHITE]


def get_winner(board: BoardState) -> int:
    """Kembalikan BLACK, WHITE, atau EMPTY; tolak posisi nonterminal."""
    if not is_terminal(board):
        raise ValueError("Permainan belum berakhir")
    black, white = get_score(board)
    return BLACK if black > white else WHITE if white > black else EMPTY
