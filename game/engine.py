from .board import Board

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
