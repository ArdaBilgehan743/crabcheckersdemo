#!/usr/bin/env python3
import math

# --- Board & rules (same as before) ---
BOARD = 6
initial_grid = [
    list("boaboa"),
    list("oooooo"),
    list("aoooob"),
    list("booooa"),
    list("oooooo"),
    list("aobaob"),
]
DIRS = {'up':(-1,0), 'down':(1,0), 'left':(0,-1), 'right':(0,1)}

def compute_dest(grid, r, c, dr, dc):
    nr, nc = r, c
    while True:
        nr2, nc2 = nr+dr, nc+dc
        if not (0<=nr2<BOARD and 0<=nc2<BOARD): break
        if grid[nr2][nc2] != 'o': break
        nr, nc = nr2, nc2
    return (nr,nc) if (nr,nc)!=(r,c) else None

def get_moves(grid, player):
    out=[]
    for r in range(BOARD):
        for c in range(BOARD):
            if grid[r][c]==player:
                for d,(dr,dc) in DIRS.items():
                    if compute_dest(grid, r,c,dr,dc):
                        out.append((r,c,d))
    return out

def apply_move(grid, move):
    r,c,d = move; dr,dc=DIRS[d]
    dest=compute_dest(grid,r,c,dr,dc)
    new=[row.copy() for row in grid]
    if dest:
        nr,nc=dest
        new[nr][nc]=new[r][c]
        new[r][c]  ='o'
    return new

def check_win(grid):
    for row in grid:
        s=''.join(row)
        if 'aaaa' in s: return 'a'
        if 'bbbb' in s: return 'b'
    for c in range(BOARD):
        s=''.join(grid[r][c] for r in range(BOARD))
        if 'aaaa' in s: return 'a'
        if 'bbbb' in s: return 'b'
    return None

# --- Heuristic evaluation ---
def heuristic(grid):
    # mobility + center‐control heuristic
    a_moves=len(get_moves(grid,'a'))
    b_moves=len(get_moves(grid,'b'))
    score = (a_moves - b_moves) * 10
    # reward having crabs in middle two rows
    for r in (2,3):
        for c in range(BOARD):
            if grid[r][c]=='a': score += 1
            if grid[r][c]=='b': score -= 1
    return score

# --- Minimax with α–β pruning ---
def minimax(grid, player, depth, α, β):
    winner = check_win(grid)
    if winner=='a': return 10000, None
    if winner=='b': return -10000, None
    if depth==0:
        return heuristic(grid), None

    moves = get_moves(grid, player)
    if not moves:
        # no legal moves → opponent wins
        return ( -10000 if player=='a' else 10000 ), None

    best_move = None
    if player=='a':
        val = -math.inf
        for m in moves:
            g2 = apply_move(grid, m)
            v,_ = minimax(g2, 'b', depth-1, α, β)
            if v>val:
                val, best_move = v, m
            α = max(α, val)
            if β<=α: break
        return val, best_move
    else:
        val = math.inf
        for m in moves:
            g2 = apply_move(grid, m)
            v,_ = minimax(g2, 'a', depth-1, α, β)
            if v<val:
                val, best_move = v, m
            β = min(β, val)
            if β<=α: break
        return val, best_move

# --- Self‐play using Minimax ---
def print_board(grid):
    for row in grid:
        print(''.join(row))
    print()

def play_minimax(depth=4):
    grid = [row.copy() for row in initial_grid]
    player = 'a'
    while True:
        score, move = minimax(grid, player, depth, -math.inf, math.inf)
        if move is None:
            print(f"{player.upper()} has no moves → draw or loss.")
            break
        grid = apply_move(grid, move)
        print(f"{player.upper()} → {move} (score {score})")
        print_board(grid)
        w = check_win(grid)
        if w:
            print("🏆 Winner:", w.upper())
            break
        player = 'b' if player=='a' else 'a'

if __name__=="__main__":
    play_minimax(depth=8,max_turns=100)

