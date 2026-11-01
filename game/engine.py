from .board import Board, BLACK, WHITE, EMPTY, SIZE, create_board

class GameEngine: 
    def __init__(self):
        self.board = Board()
        self.current_player = Board.BLACK

    # Mengambil pemain yang sedang bermain 
    def get_current_player(self):
        return self.current_player

    # Mengambil langkah pemain saat ini yang valid
    def get_valid_moves(self):
        return self.board.get_valid_moves(self.current_player)

    # Memeriksa apakah permainan sudah berakhir
    def is_game_over(self):
        black_moves = self.board.get_valid_moves(Board.BLACK)
        white_moves = self.board.get_valid_moves(Board.WHITE)

        return (self.board.is_full() or (len(black_moves)==0 and len (white_moves)==0))
    
    # Menjalankan langkah pemain saat ini
    def play_move(self, row, col):
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
    def must_pass(self):
        if self.is_game_over():
            return False
        
        return len(self.get_valid_moves()) == 0

    # Melewati giliran jika tidak ada langkah valid
    def pass_turn(self):
        if self.is_game_over():
            raise ValueError("Permainan Telah Berakhir")

        if not self.must_pass():
            raise ValueError("Pemain masih memiliki langkah valid!")
        
        self.current_player = self.board.get_opponent(self.current_player)
    

    # Menentukan pemenang berdasarkan jumlah bidak
    def get_winner(self):
        if not self.is_game_over():
            return None

        score = self.board.get_score()

        if score[Board.BLACK] > score[Board.WHITE]:
            return Board.BLACK
        elif score[Board.WHITE] > score[Board.BLACK]:
            return Board.WHITE
        else:
            return "DRAW"

    # Mengambil score permainan dari dua bidak 
    def get_score(self):
        return self.board.get_score()


# ---------------------------------------------------------------------------
# API fungsional untuk algoritma AI dan eksperimen (alphabeta, mcts, benchmark,
# tournament). Papan = list[list[int]]: kosong 0, hitam 1, putih -1.
# Semua fungsi TIDAK memodifikasi papan input. Class GameEngine di atas tidak
# diubah dan tetap dipakai oleh GUI.
# ---------------------------------------------------------------------------

# Mengambil lawan dari pemain (1 <-> -1)
def get_opponent(player):
    if player == BLACK:
        return WHITE
    if player == WHITE:
        return BLACK
    raise ValueError("Player harus BLACK (1) atau WHITE (-1)")


# Mencari bidak lawan yang terbalik jika player meletakkan bidak di (row, col)
def get_captured_discs(board, row, col, player):
    if not (0 <= row < SIZE and 0 <= col < SIZE) or board[row][col] != EMPTY:
        return []

    opponent = get_opponent(player)
    captured = []

    for dr, dc in Board.DIRECTIONS:
        r, c = row + dr, col + dc
        line = []

        while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == opponent:
            line.append((r, c))
            r += dr
            c += dc

        if line and 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
            captured.extend(line)

    return captured


# Mengambil semua langkah valid (row, col), terurut dari baris lalu kolom
def get_valid_moves(board, player):
    get_opponent(player)
    return [
        (row, col)
        for row in range(SIZE)
        for col in range(SIZE)
        if get_captured_discs(board, row, col, player)
    ]


# Memeriksa apakah player punya minimal satu langkah valid
def has_valid_move(board, player):
    get_opponent(player)
    return any(
        get_captured_discs(board, row, col, player)
        for row in range(SIZE)
        for col in range(SIZE)
    )


# Menjalankan langkah dan mengembalikan papan BARU (papan input tidak berubah)
def apply_move(board, row, col, player):
    captured = get_captured_discs(board, row, col, player)
    if not captured:
        raise ValueError("Langkah tidak valid")

    new_board = [line[:] for line in board]
    new_board[row][col] = player
    for r, c in captured:
        new_board[r][c] = player

    return new_board


# Permainan selesai jika kedua pemain tidak punya langkah valid
def is_terminal(board):
    return not has_valid_move(board, BLACK) and not has_valid_move(board, WHITE)


# Pemain berikutnya setelah `player` bermain:
# lawan jika punya langkah, jika tidak `player` lagi (lawan pass), None jika terminal
def get_next_player(board, player):
    opponent = get_opponent(player)
    if has_valid_move(board, opponent):
        return opponent
    if has_valid_move(board, player):
        return player
    return None


# Score sebagai tuple (jumlah hitam, jumlah putih)
def get_score(board):
    black = sum(cell == BLACK for row in board for cell in row)
    white = sum(cell == WHITE for row in board for cell in row)
    return black, white


# Pemenang: 1 (hitam), -1 (putih), 0 (seri), None jika permainan belum selesai
def get_winner(board):
    if not is_terminal(board):
        return None

    black, white = get_score(board)
    if black > white:
        return BLACK
    if white > black:
        return WHITE
    return 0