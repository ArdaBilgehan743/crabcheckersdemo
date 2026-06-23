"""Pure rules for Crab Checkers.

The board is represented as a tuple of six strings. Each character is:

- ``a`` for player A
- ``b`` for player B
- ``o`` for an empty square
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

BOARD_SIZE = 6
WIN_LENGTH = 4
EMPTY = "o"
PLAYER_A = "a"
PLAYER_B = "b"
PLAYERS = (PLAYER_A, PLAYER_B)

START_BOARD = (
    "boaboa",
    "oooooo",
    "aoooob",
    "booooa",
    "oooooo",
    "aobaob",
)

DIRS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


@dataclass(frozen=True, slots=True)
class Move:
    row: int
    col: int
    direction: str


def normalize_board(board: Iterable[Iterable[str]] | Iterable[str]) -> tuple[str, ...]:
    """Return an immutable board tuple from old list-based or new tuple boards."""
    rows = []
    for row in board:
        rows.append("".join(row))
    if len(rows) != BOARD_SIZE or any(len(row) != BOARD_SIZE for row in rows):
        raise ValueError(f"Crab Checkers boards must be {BOARD_SIZE}x{BOARD_SIZE}")
    return tuple(rows)


def opponent(player: str) -> str:
    if player == PLAYER_A:
        return PLAYER_B
    if player == PLAYER_B:
        return PLAYER_A
    raise ValueError(f"unknown player: {player!r}")


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def get_cell(board: tuple[str, ...], row: int, col: int) -> str:
    return board[row][col]


def compute_destination(
    board: tuple[str, ...],
    row: int,
    col: int,
    direction: str,
) -> tuple[int, int] | None:
    """Return the final square when a crab slides in ``direction``."""
    if direction not in DIRS or not in_bounds(row, col):
        return None

    dr, dc = DIRS[direction]
    nr, nc = row, col
    moved = False
    while True:
        r2, c2 = nr + dr, nc + dc
        if not in_bounds(r2, c2):
            break
        if board[r2][c2] != EMPTY:
            break
        nr, nc = r2, c2
        moved = True
    return (nr, nc) if moved else None


def legal_moves(board: tuple[str, ...], player: str) -> list[Move]:
    moves: list[Move] = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == player:
                for direction in DIRS:
                    if compute_destination(board, row, col, direction):
                        moves.append(Move(row, col, direction))
    return moves


def legal_destinations(
    board: tuple[str, ...],
    row: int,
    col: int,
) -> dict[str, tuple[int, int]]:
    return {
        direction: dest
        for direction in DIRS
        if (dest := compute_destination(board, row, col, direction))
    }


def move_for_destination(
    board: tuple[str, ...],
    row: int,
    col: int,
    destination: tuple[int, int],
) -> Move | None:
    for direction, dest in legal_destinations(board, row, col).items():
        if dest == destination:
            return Move(row, col, direction)
    return None


def apply_move(board: tuple[str, ...], move: Move) -> tuple[str, ...]:
    player = board[move.row][move.col]
    if player not in PLAYERS:
        raise ValueError("cannot move from an empty square")
    destination = compute_destination(board, move.row, move.col, move.direction)
    if not destination:
        raise ValueError(f"illegal move: {move}")

    rows = [list(row) for row in board]
    dest_row, dest_col = destination
    rows[move.row][move.col] = EMPTY
    rows[dest_row][dest_col] = player
    return tuple("".join(row) for row in rows)


def check_winner(board: tuple[str, ...]) -> str | None:
    streaks = (PLAYER_A * WIN_LENGTH, PLAYER_B * WIN_LENGTH)
    for row in board:
        for streak in streaks:
            if streak in row:
                return streak[0]

    for col in range(BOARD_SIZE):
        column = "".join(board[row][col] for row in range(BOARD_SIZE))
        for streak in streaks:
            if streak in column:
                return streak[0]
    return None


def terminal_result(board: tuple[str, ...], current_player: str) -> str | None:
    """Return ``a``, ``b``, or ``draw`` when the current state is terminal."""
    winner = check_winner(board)
    if winner:
        return winner
    if not legal_moves(board, current_player):
        return opponent(current_player)
    return None


def position_key(board: tuple[str, ...], current_player: str) -> tuple[tuple[str, ...], str]:
    return board, current_player


def is_repetition_draw(
    position_counts: Mapping[tuple[tuple[str, ...], str], int],
    board: tuple[str, ...],
    current_player: str,
    threshold: int = 3,
) -> bool:
    return position_counts[position_key(board, current_player)] >= threshold


def cell_name(row: int, col: int) -> str:
    return f"{chr(ord('a') + col)}{row + 1}"


def move_notation(board: tuple[str, ...], move: Move) -> str:
    destination = compute_destination(board, move.row, move.col, move.direction)
    if destination is None:
        return f"{cell_name(move.row, move.col)} ?"
    return f"{cell_name(move.row, move.col)} {move.direction} {cell_name(*destination)}"
