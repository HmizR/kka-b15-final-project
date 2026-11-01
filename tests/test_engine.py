import unittest
import pytest

from game import Board, GameEngine
from game.board import BLACK, WHITE, EMPTY, copy_board, create_board
from game.engine import (apply_move, get_flips, get_next_player, get_score,
                         get_valid_moves, get_winner, has_valid_move, is_terminal)


def test_functional_initial_board_and_independent_copy():
    board = create_board()
    assert len(board) == 8 and all(len(row) == 8 for row in board)
    assert {cell for row in board for cell in row} == {0, 1, -1}
    assert get_score(board) == (2, 2)
    assert get_valid_moves(board, BLACK) == [(2, 3), (3, 2), (4, 5), (5, 4)]
    assert get_valid_moves(board, WHITE) == [(2, 4), (3, 5), (4, 2), (5, 3)]
    clone = copy_board(board)
    clone[0][0] = BLACK
    assert board[0][0] == EMPTY and create_board() == board


def test_functional_apply_move_preserves_input():
    board = create_board()
    original = copy_board(board)
    assert get_flips(board, 2, 3, BLACK) == [(3, 3)]
    result = apply_move(board, 2, 3, BLACK)
    assert get_score(result) == (4, 1)
    assert get_next_player(result, BLACK) == WHITE
    assert board == original
    result[0][0] = BLACK
    assert board == original


def test_multidirectional_flips_are_sorted():
    board = [[EMPTY] * 8 for _ in range(8)]
    expected = []
    for dr, dc in Board.DIRECTIONS:
        board[3 + dr][3 + dc] = WHITE
        board[3 + 2 * dr][3 + 2 * dc] = WHITE
        board[3 + 3 * dr][3 + 3 * dc] = BLACK
        expected.extend([(3 + dr, 3 + dc), (3 + 2 * dr, 3 + 2 * dc)])
    original = copy_board(board)
    assert get_flips(board, 3, 3, BLACK) == sorted(expected)
    result = apply_move(board, 3, 3, BLACK)
    assert all(result[r][c] == BLACK for r, c in expected)
    assert board == original


@pytest.mark.parametrize("move", [(0, 0), (3, 3), (-1, 3), (8, 3), (2, 8)])
def test_illegal_moves_preserve_board(move):
    board = create_board()
    original = copy_board(board)
    assert get_flips(board, *move, BLACK) == []
    with pytest.raises(ValueError):
        apply_move(board, *move, BLACK)
    assert board == original


@pytest.mark.parametrize("player", [0, 2, -2, None, "B"])
def test_functional_invalid_player_rejected(player):
    board = create_board()
    for call in (lambda: get_flips(board, 2, 3, player),
                 lambda: get_flips(board, -1, 3, player),
                 lambda: get_flips(board, 3, 3, player),
                 lambda: get_valid_moves(board, player),
                 lambda: has_valid_move(board, player),
                 lambda: apply_move(board, 2, 3, player),
                 lambda: get_next_player(board, player)):
        with pytest.raises(ValueError):
            call()


def test_functional_pass_and_terminal_with_empty_squares():
    board = [[WHITE] * 8 for _ in range(8)]
    board[0][0], board[0][1] = EMPTY, BLACK
    assert not has_valid_move(board, BLACK)
    assert has_valid_move(board, WHITE)
    assert not is_terminal(board)
    assert get_next_player(board, WHITE) == WHITE
    assert get_next_player(board, BLACK) == WHITE
    with pytest.raises(ValueError):
        get_winner(board)
    terminal = [[BLACK] * 8 for _ in range(8)]
    terminal[0][0] = EMPTY
    assert is_terminal(terminal)
    assert get_next_player(terminal, BLACK) is None
    assert get_winner(terminal) == BLACK


def test_functional_winners_and_class_nonterminal_rejection():
    assert get_winner([[WHITE] * 8 for _ in range(8)]) == WHITE
    assert get_winner([[BLACK] * 4 + [WHITE] * 4 for _ in range(8)]) == EMPTY
    game = GameEngine()
    with pytest.raises(ValueError):
        game.get_winner()
    game.board.grid = [[BLACK] * 4 + [WHITE] * 4 for _ in range(8)]
    assert game.get_winner() == EMPTY

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
        self.assertTrue(self.game.board.is_valid_move(2,3,Board.BLACK))

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



