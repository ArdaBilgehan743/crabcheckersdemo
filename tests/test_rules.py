from __future__ import annotations

import unittest
from collections import Counter

from crabcheckers.rules import (
    Move,
    START_BOARD,
    apply_move,
    check_winner,
    compute_destination,
    is_repetition_draw,
    legal_moves,
    move_for_destination,
    move_notation,
    position_key,
)


class RulesTest(unittest.TestCase):
    def test_compute_destination_slides_until_blocked_or_edge(self) -> None:
        self.assertEqual(compute_destination(START_BOARD, 0, 2, "down"), (4, 2))
        self.assertEqual(compute_destination(START_BOARD, 2, 0, "right"), (2, 4))
        self.assertEqual(compute_destination(START_BOARD, 5, 0, "up"), (4, 0))
        self.assertIsNone(compute_destination(START_BOARD, 0, 0, "up"))

    def test_start_position_has_legal_moves_for_both_players(self) -> None:
        self.assertEqual(len(legal_moves(START_BOARD, "a")), 12)
        self.assertEqual(len(legal_moves(START_BOARD, "b")), 12)

    def test_apply_move_returns_new_board(self) -> None:
        moved = apply_move(START_BOARD, Move(0, 2, "down"))
        self.assertEqual(moved[0][2], "o")
        self.assertEqual(moved[4][2], "a")
        self.assertEqual(START_BOARD[0][2], "a")

    def test_move_for_destination_and_notation(self) -> None:
        move = move_for_destination(START_BOARD, 0, 2, (4, 2))
        self.assertEqual(move, Move(0, 2, "down"))
        self.assertEqual(move_notation(START_BOARD, move), "c1 down c5")

    def test_check_winner_horizontal_and_vertical(self) -> None:
        self.assertEqual(check_winner(("aaaaoo", "oooooo", "oooooo", "oooooo", "oooooo", "bbbbbo")), "a")
        self.assertEqual(check_winner(("booooo", "booooo", "booooo", "booooo", "oooooo", "aaooao")), "b")

    def test_threefold_repetition_draw_helper(self) -> None:
        counts = Counter()
        key = position_key(START_BOARD, "a")
        counts[key] = 2
        self.assertFalse(is_repetition_draw(counts, START_BOARD, "a"))
        counts[key] = 3
        self.assertTrue(is_repetition_draw(counts, START_BOARD, "a"))


if __name__ == "__main__":
    unittest.main()
