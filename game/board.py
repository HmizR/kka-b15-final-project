"""Papan Othello dan API list-of-lists untuk integrasi."""

EMPTY = 0
BLACK = 1
WHITE = -1
BOARD_SIZE = 8
Move = tuple[int, int]
BoardState = list[list[int]]


class Board:
    """Pembungkus papan untuk antarmuka GameEngine yang sudah ada."""
    SIZE = 8
    EMPTY = EMPTY
    BLACK = BLACK
    WHITE = WHITE

    # Untuk Arah Pemeriksaan
    DIRECTIONS = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    # Membuat papan kosong 8 x 8
    def __init__(self) -> None:
        """Buat posisi awal Othello."""
        self.grid = [[self.EMPTY for _ in range(self.SIZE)] for _ in range (self.SIZE) ]

        # posisi awal dari permainan othello
        self.grid[3][3] = self.WHITE
        self.grid[3][4] = self.BLACK
        self.grid[4][3] = self.BLACK
        self.grid[4][4] = self.WHITE


    # Memeriksa apakah koordinat berada di dalam papan
    def is_inside(self, row: int, col: int) -> bool:
        """Periksa batas koordinat papan."""
        return ( 0 <= row < self.SIZE and 0 <= col < self.SIZE)


    # Membalik warna lawan
    def get_opponent(self, player: int) -> int:
        """Kembalikan lawan atau tolak pemain tidak valid."""
        if player == self.BLACK:
            return self.WHITE
        if player == self.WHITE:
            return self.BLACK
        raise ValueError("Player Tidak Valid")

    # Mencari seluruh bidak yang warnanya bisa dibalik
    def get_captured_discs(self, row: int, col: int, player: int) -> list[Move]:
        """Temukan seluruh flip, terurut berdasarkan koordinat."""
        opponent = self.get_opponent(player)
        if not self.is_inside(row,col):
            return []
        if self.grid[row][col] != self.EMPTY:
            return []

        captured = []

        for dr, dc in self.DIRECTIONS:
            r = row  + dr
            c = col + dc

            direction_captured = []

            # Mencari bidak lawan secara berurutan
            while(self.is_inside(r,c) and self.grid[r][c] == opponent):
                direction_captured.append((r,c))
                r += dr
                c += dc

            # Bidak lawan harus diakhiri dengan bidak sendiri (Menjepit)
            if (direction_captured and self.is_inside(r,c) and self.grid[r][c] == player):
                captured.extend(direction_captured)
        return sorted(captured)

    # Memeriksa apakah langkah pemain valid atau tidak
    def is_valid_move(self, row: int, col: int, player: int) -> bool:
        """Periksa legalitas langkah; pemain tidak valid ditolak."""
        return len(self.get_captured_discs(row,col,player)) > 0

    # Mengambil semua langkah yang valid
    def get_valid_moves(self, player: int) -> list[Move]:
        """Kembalikan langkah legal dalam urutan koordinat."""
        self.get_opponent(player)
        valid_moves = []


        for row in range (self.SIZE):
            for col in range(self.SIZE):
                if self.is_valid_move(row,col,player):
                    valid_moves.append((row,col))
        return valid_moves

    # Menempatkan bidak dan membalik bidak lawan.
    def apply_move(self, row: int, col: int, player: int) -> list[Move]:
        """Ubah instance ini dan kembalikan flip untuk GameEngine lama.

        API fungsional game.engine.apply_move mengembalikan salinan papan.
        """
        if not self.is_valid_move(row, col, player):
            raise ValueError("Langkah Anda Tidak Valid")

        captured = self.get_captured_discs(row,col,player)

        # Meletakkan bidak pemain 
        self.grid[row][col] = player

        # Membalik seluruh bidak lawan yang terjepit
        for r, c in captured:
            self.grid[r][c] = player

        return captured

    # Menghitung score melalui bidak (hitam atau putih) pemain
    def get_score(self) -> dict[int, int]:
        """Kembalikan skor per warna untuk antarmuka kelas lama."""
        black_score = 0
        white_score = 0

        for row in self.grid:
            for cell in row:
                if cell == self.BLACK:
                    black_score += 1
                elif cell == self.WHITE:
                    white_score += 1

        return {self.BLACK : black_score, self.WHITE: white_score }

    # Memeriksa apakah papan sudah penuh?
    def is_full(self) -> bool:
        """Periksa apakah semua kotak terisi."""
        return all(cell != self.EMPTY for row in self.grid for cell in row)

    # Menampilkan papan ke terminal
    def display(self) -> None:
        """Tampilkan papan bila diminta secara eksplisit."""
        print("  0 1 2 3 4 5 6 7")
        for i, row in enumerate(self.grid):
            print(i , end=" ")

            for cell in row:
                print ({self.BLACK: "B", self.WHITE: "W", self.EMPTY: "."}[cell], end=" ")

            print()

    @classmethod
    def from_grid(cls, grid: BoardState) -> "Board":
        """Bungkus grid tanpa menyalin; pemanggil menentukan kepemilikannya."""
        instance = cls.__new__(cls)
        instance.grid = grid
        return instance


def create_board() -> BoardState:
    """Kembalikan papan awal 8x8 berisi 0, 1, dan -1."""
    return Board().grid


def copy_board(board: BoardState) -> BoardState:
    """Salin papan beserta barisnya agar perubahan tidak memengaruhi asal."""
    return [row[:] for row in board]



    











