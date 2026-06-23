"""AI opponents for Crab Checkers."""

from __future__ import annotations

import math
import random

from crabcheckers.content import get_stake
from crabcheckers.rules import (
    BOARD_SIZE,
    Move,
    PLAYER_A,
    PLAYER_B,
    apply_move,
    check_winner,
    legal_moves,
    opponent,
)

WIN_SCORE = 100_000


def choose_move(
    board: tuple[str, ...],
    player: str,
    stake_key: str = "mid",
    rng: random.Random | None = None,
) -> Move | None:
    rng = rng or random
    stake = get_stake(stake_key)
    moves = legal_moves(board, player)
    if not moves:
        return None
    if stake.depth <= 0:
        return rng.choice(moves)
    _, move = minimax(
        board=board,
        current_player=player,
        ai_player=player,
        depth=stake.depth,
        alpha=-math.inf,
        beta=math.inf,
    )
    return move or rng.choice(moves)


def minimax(
    board: tuple[str, ...],
    current_player: str,
    ai_player: str,
    depth: int,
    alpha: float,
    beta: float,
) -> tuple[float, Move | None]:
    winner = check_winner(board)
    if winner:
        if winner == ai_player:
            return WIN_SCORE + depth, None
        return -WIN_SCORE - depth, None
    if depth == 0:
        return evaluate_board(board, ai_player), None

    moves = legal_moves(board, current_player)
    if not moves:
        if opponent(current_player) == ai_player:
            return WIN_SCORE + depth, None
        return -WIN_SCORE - depth, None

    maximizing = current_player == ai_player
    best_move = None
    ordered_moves = order_moves(board, moves, ai_player)

    if maximizing:
        value = -math.inf
        for move in ordered_moves:
            score, _ = minimax(
                apply_move(board, move),
                opponent(current_player),
                ai_player,
                depth - 1,
                alpha,
                beta,
            )
            if score > value:
                value, best_move = score, move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move

    value = math.inf
    for move in ordered_moves:
        score, _ = minimax(
            apply_move(board, move),
            opponent(current_player),
            ai_player,
            depth - 1,
            alpha,
            beta,
        )
        if score < value:
            value, best_move = score, move
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value, best_move


def order_moves(board: tuple[str, ...], moves: list[Move], ai_player: str) -> list[Move]:
    return sorted(
        moves,
        key=lambda move: evaluate_board(apply_move(board, move), ai_player),
        reverse=True,
    )


def evaluate_board(board: tuple[str, ...], player: str) -> float:
    foe = opponent(player)
    winner = check_winner(board)
    if winner == player:
        return WIN_SCORE
    if winner == foe:
        return -WIN_SCORE

    score = 0.0
    score += (len(legal_moves(board, player)) - len(legal_moves(board, foe))) * 4
    score += line_score(board, player) - line_score(board, foe)
    score += center_score(board, player) - center_score(board, foe)
    return score


def line_score(board: tuple[str, ...], player: str) -> float:
    score = 0.0
    lines = list(board)
    lines.extend("".join(board[row][col] for row in range(BOARD_SIZE)) for col in range(BOARD_SIZE))
    for line in lines:
        for start in range(BOARD_SIZE - 3):
            window = line[start : start + 4]
            own = window.count(player)
            empty = window.count("o")
            if own == 4:
                score += 10_000
            elif own == 3 and empty == 1:
                score += 150
            elif own == 2 and empty == 2:
                score += 25
            elif own == 1 and empty == 3:
                score += 3
    return score


def center_score(board: tuple[str, ...], player: str) -> float:
    score = 0.0
    center_cells = {(2, 2), (2, 3), (3, 2), (3, 3)}
    near_center_rows = {2, 3}
    near_center_cols = {2, 3}
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != player:
                continue
            if (row, col) in center_cells:
                score += 5
            elif row in near_center_rows or col in near_center_cols:
                score += 2
    return score


def player_label(player: str) -> str:
    return "A" if player == PLAYER_A else "B" if player == PLAYER_B else player.upper()

