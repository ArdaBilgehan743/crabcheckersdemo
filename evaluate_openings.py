#!/usr/bin/env python3
import random
from collections import defaultdict

# Board size & initial setup
N = 1000            # playouts per opening move
BOARD = 6
initial_grid = [
    list("boaboa"),
    list("oooooo"),
    list("aoooob"),
    list("booooa"),
    list("oooooo"),
    list("aobaob"),
]
DIRS = {
    'up':    (-1, 0),
    'down':  ( 1, 0),
    'left':  ( 0,-1),
    'right': ( 0, 1),
}

def compute_dest(grid, r, c, dr, dc):
    nr, nc = r, c
    while True:
        nr2, nc2 = nr+dr, nc+dc
        if not (0 <= nr2 < BOARD and 0 <= nc2 < BOARD): 
            break
        if grid[nr2][nc2] != 'o': 
            break
        nr, nc = nr2, nc2
    return (nr,nc) if (nr,nc) != (r,c) else None

def get_moves(grid, player):
    out = []
    for r in range(BOARD):
        for c in range(BOARD):
            if grid[r][c] == player:
                for d,(dr,dc) in DIRS.items():
                    if compute_dest(grid, r, c, dr, dc):
                        out.append((r,c,d))
    return out

def apply_move(grid, move):
    r,c,d = move
    dr,dc = DIRS[d]
    dest = compute_dest(grid, r, c, dr, dc)
    new = [row.copy() for row in grid]
    if dest:
        nr,nc = dest
        new[nr][nc] = new[r][c]
        new[r][c]   = 'o'
    return new

def check_win(grid):
    # horizontal
    for row in grid:
        s = ''.join(row)
        if 'aaaa' in s: return 'a'
        if 'bbbb' in s: return 'b'
    # vertical
    for c in range(BOARD):
        col = ''.join(grid[r][c] for r in range(BOARD))
        if 'aaaa' in col: return 'a'
        if 'bbbb' in col: return 'b'
    return None

def simulate(grid, turn):
    """Random‐play from (grid,turn), draw on 3× repetition or no moves."""
    g = [row.copy() for row in grid]
    player = turn
    seen = defaultdict(int)
    for _ in range(200):
        key = (tuple(map(tuple,g)), player)
        seen[key] += 1
        if seen[key] >= 3: 
            return 'draw'
        moves = get_moves(g, player)
        if not moves: 
            return 'b' if player=='a' else 'a'
        g = apply_move(g, random.choice(moves))
        w = check_win(g)
        if w: 
            return w
        player = 'b' if player=='a' else 'a'
    return 'draw'

# --- Main evaluation ---
openings = get_moves(initial_grid, 'a')
results = []
for move in openings:
    stats = {'a':0, 'b':0, 'draw':0}
    # apply first‐move for A
    g1 = apply_move(initial_grid, move)
    # simulate
    for _ in range(N):
        out = simulate(g1, 'b')
        stats[out] += 1
    r, c, d = move
    move_name = f"{r+1}{chr(c+97)} → {d}"
    results.append({
        'move':     move_name,
        'A win %':  stats['a']/N*100,
        'B win %':  stats['b']/N*100,
        'Draw %':   stats['draw']/N*100,
    })

# sort by A’s winning chance
results.sort(key=lambda x: x['A win %'], reverse=True)

# Print nicely
print(f"{'Move':8}  {'A win':>6}  {'B win':>6}  {'Draw':>6}")
print("-"*30)
for row in results:
    print(f"{row['move']:8}  {row['A win %']:6.1f}%  {row['B win %']:6.1f}%  {row['Draw %']:6.1f}%")
