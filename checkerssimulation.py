#!/usr/bin/env python3
import random
from collections import defaultdict
import sys

BOARD_SIZE = 6
initial_grid = [
    list("boaboa"),
    list("oooooo"),
    list("aoooob"),
    list("booooa"),
    list("oooooo"),
    list("aobaob"),
]
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def compute_destination(grid, r, c, dr, dc):
    nr, nc = r, c
    while True:
        nr2, nc2 = nr + dr, nc + dc
        if not (0 <= nr2 < BOARD_SIZE and 0 <= nc2 < BOARD_SIZE): break
        if grid[nr2][nc2] != 'o': break
        nr, nc = nr2, nc2
    return (nr, nc) if (nr, nc) != (r, c) else None

def get_moves(grid, player):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] == player:
                for dr, dc in DIRS:
                    if compute_destination(grid, r, c, dr, dc):
                        moves.append((r, c, dr, dc))
    return moves

def apply_move(grid, move):
    r, c, dr, dc = move
    dest = compute_destination(grid, r, c, dr, dc)
    new_grid = [row.copy() for row in grid]
    if dest:
        nr, nc = dest
        new_grid[nr][nc] = new_grid[r][c]
        new_grid[r][c] = 'o'
    return new_grid

def check_win(grid):
    for r in range(BOARD_SIZE):
        row = ''.join(grid[r])
        if 'aaaa' in row: return 'a'
        if 'bbbb' in row: return 'b'
    for c in range(BOARD_SIZE):
        col = ''.join(grid[r][c] for r in range(BOARD_SIZE))
        if 'aaaa' in col: return 'a'
        if 'bbbb' in col: return 'b'
    return None

def simulate_game(max_turns=200):
    grid = [row.copy() for row in initial_grid]
    current = 'a'
    history = defaultdict(int)
    for _ in range(max_turns):
        key = (tuple(map(tuple, grid)), current)
        history[key] += 1
        if history[key] >= 3:
            return 'draw'
        moves = get_moves(grid, current)
        if not moves:
            return 'b' if current=='a' else 'a'
        grid = apply_move(grid, random.choice(moves))
        winner = check_win(grid)
        if winner:
            return winner
        current = 'b' if current=='a' else 'a'
    return 'draw'

if __name__ == "__main__":
    N = 1000
    results = {'a': 0, 'b': 0, 'draw': 0}
    for i in range(N):
        results[simulate_game()] += 1
        if i and i % 100 == 0:
            print(f"{i} games…", end="\r", file=sys.stderr)

    print("\nFinal results:")
    print(f"A wins: {results['a']} ({results['a']/N*100:.1f}%)")
    print(f"B wins: {results['b']} ({results['b']/N*100:.1f}%)")
    print(f"Draws:  {results['draw']} ({results['draw']/N*100:.1f}%)")
