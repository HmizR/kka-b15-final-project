import unittest

from game import Board, GameEngine

class TestGameEngine(unittest.TestCase):

    # Membuat permainann baru sebelum setiap pengujian
    def setUp(self):
        self.game = GameEngine()


    # Menguji kondisi awal papan
    def test_initial_board(self):
        score = self.game.get_score()

        self.assertEqual(score[Board.BLACK], 2)
        self.assertEqual(score[Board.WHITE], 2)

        self.assertEqual(self.game.get_current_player(), Board.BLACK)

    # Menguji langkah valid pada awal permainan
    def test_initial_valid_moves(self):
        moves = self.game.get_valid_moves()

        expected = [ 
            (2, 3),
            (3, 2),
            (4, 5),
            (5, 4)
            ]
        self.assertEqual(set(moves), set(expected))

    # Menguji langkah yang diperbolehkan
    def test_valid_moves(self):
        self.assertTrue(self.game.board.is_valid_move())

    # Menguji langkah yang tidak boleh
    def test_invalid_move(self):
        self.assertFalse(self.game.board.is_valid_move(0,0,Board.BLACK))

    # Menguji penempatan dan pembalikan bidak
    def test_play_move(self):
        self.game.play_move(2,3)

        score = self.game.get_score()

        self.assertEqual(score[Board.BLACK], 4)
        self.assertEqual(score[Board.WHITE], 1)

        self.assertEqual(self.game.get_current_player(), Board.WHITE)

    # Menguji penolakan langkah ilegal
    def test_invalid_moves_raise_error(self):
        with self.assertRaises(ValueError):
            self.game.play_move(0,0)

    # Menguji kondisi awal permainan
    def test_game_not_over_initially(self):
        self.assertFalse(self.game.is_game_over())

    # Menguji perhitungan score awal
    def test_score(self):
        score = self.game.get_score()

        self.assertEqual(score, {Board.BLACK: 2, Board.WHITE: 2})

    # Menguji mekanisme melewati giliran
    def test_pass_turn(self):
        self.game.board.grid = [
            [Board.WHITE for _ in range(8)] for _ in range(8)]

        self.game.board.grid[0][0] = Board.EMPTY
        self.game.board.grid[0][1] = Board.BLACK
        self.game.board.grid[0][2] = Board.WHITE

        self.game.current_player = Board.BLACK

        self.assertTrue(self.game.must_pass())

        self.game.pass_turn()

        self.assertEqual((self.game.get_current_player()), Board.WHITE)

    # Menguji permainan ketika papan penuh
    def test_game_over_full_board(self):
        self.game.board.grid = [[Board.BLACK for _ in range(8)] for _ in range(8)]

        self.assertTrue(self.game.is_game_over())
        self.assertEqual(self.game.get_winner(), Board.BLACK)

if __name__ == "__main__":
        unittest.main()



