import pygame
import sys
import math

# Configuration
CELL_SIZE = 80
BOARD_SIZE = 6
MARGIN = 20
INFO_WIDTH = 200
WINDOW_WIDTH = CELL_SIZE * BOARD_SIZE + INFO_WIDTH + 2 * MARGIN
WINDOW_HEIGHT = CELL_SIZE * BOARD_SIZE + 2 * MARGIN
FPS = 30

# Colors
BG_COLOR = (245, 222, 179)
GRID_COLOR = (160, 82, 45)
A_COLOR = (200, 50, 50)
B_COLOR = (50, 50, 200)
TEXT_COLOR = (20, 20, 20)

# Directions
DIRS = { 'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1) }

# Restart button area
RESTART_BUTTON = pygame.Rect(
    WINDOW_WIDTH - INFO_WIDTH + (INFO_WIDTH - 100)//2,
    WINDOW_HEIGHT - 60,
    100, 40
)

# Initial board
START_GRID = [
    list("boaboa"),
    list("oooooo"),
    list("aoooob"),
    list("booooa"),
    list("oooooo"),
    list("aobaob"),
]

def compute_destination(grid, r, c, dr, dc):
    nr, nc = r, c
    moved = False
    while True:
        r2, c2 = nr + dr, nc + dc
        if not (0 <= r2 < BOARD_SIZE and 0 <= c2 < BOARD_SIZE):
            break
        if grid[r2][c2] != 'o':
            break
        nr, nc = r2, c2
        moved = True
    return (nr, nc) if moved else None

def get_moves(grid, player):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] == player:
                for d, (dr, dc) in DIRS.items():
                    if compute_destination(grid, r, c, dr, dc):
                        moves.append((r, c, d))
    return moves

def apply_move(grid, move):
    r, c, d = move
    dr, dc = DIRS[d]
    dest = compute_destination(grid, r, c, dr, dc)
    new = [row.copy() for row in grid]
    if dest:
        nr, nc = dest
        new[nr][nc] = new[r][c]
        new[r][c] = 'o'
    return new

def check_win(grid):
    for row in grid:
        s = ''.join(row)
        if 'aaaa' in s:
            return 'a'
        if 'bbbb' in s:
            return 'b'
    for c in range(BOARD_SIZE):
        s = ''.join(grid[r][c] for r in range(BOARD_SIZE))
        if 'aaaa' in s:
            return 'a'
        if 'bbbb' in s:
            return 'b'
    return None

def heuristic(grid):
    return len(get_moves(grid, 'a')) - len(get_moves(grid, 'b'))

AI_DEPTH = 4

def minimax(grid, player, depth, alpha, beta):
    w = check_win(grid)
    if w == 'a':
        return 1000, None
    if w == 'b':
        return -1000, None
    if depth == 0:
        return heuristic(grid), None
    moves = get_moves(grid, player)
    if not moves:
        return ((-1000, None) if player == 'a' else (1000, None))
    best_move = None
    if player == 'a':
        value = -math.inf
        for m in moves:
            val, _ = minimax(apply_move(grid, m), 'b', depth-1, alpha, beta)
            if val > value:
                value, best_move = val, m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for m in moves:
            val, _ = minimax(apply_move(grid, m), 'a', depth-1, alpha, beta)
            if val < value:
                value, best_move = val, m
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

def draw_board(grid, drag_start=None, drag_pos=None):
    screen.fill(BG_COLOR)
    for i in range(BOARD_SIZE+1):
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN, MARGIN + i*CELL_SIZE),
                         (MARGIN + BOARD_SIZE*CELL_SIZE, MARGIN + i*CELL_SIZE), 3)
    for j in range(BOARD_SIZE+1):
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN + j*CELL_SIZE, MARGIN),
                         (MARGIN + j*CELL_SIZE, MARGIN + BOARD_SIZE*CELL_SIZE), 3)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] != 'o':
                col = A_COLOR if grid[r][c]=='a' else B_COLOR
                cx = MARGIN + c*CELL_SIZE + CELL_SIZE//2
                cy = MARGIN + r*CELL_SIZE + CELL_SIZE//2
                pygame.draw.circle(screen, col, (cx, cy), CELL_SIZE//2 - 10)
    if drag_start and drag_pos:
        px, py = drag_pos
        color = A_COLOR if HUMAN_PLAYER=='a' else B_COLOR
        pygame.draw.circle(screen, color, (px, py), CELL_SIZE//2 - 10)
    pygame.draw.rect(screen, GRID_COLOR, RESTART_BUTTON)
    pygame.draw.rect(screen, BG_COLOR, RESTART_BUTTON.inflate(-4, -4))
    txt = font.render("Restart", True, TEXT_COLOR)
    screen.blit(txt, txt.get_rect(center=RESTART_BUTTON.center))
    pygame.display.flip()

def main():
    global HUMAN_PLAYER, AI_PLAYER
    HUMAN_PLAYER = ''
    while HUMAN_PLAYER not in ('a', 'b'):
        HUMAN_PLAYER = input("Choose side A(red) or B(blue) [a/b]: ").strip().lower()
    AI_PLAYER = 'b' if HUMAN_PLAYER=='a' else 'a'
    grid = [row.copy() for row in START_GRID]
    current_player = 'a'
    drag_start = None
    drag_pos = None
    game_over = False
    draw_board(grid)
    while True:
        if not game_over and current_player == AI_PLAYER:
            _, move = minimax(grid, AI_PLAYER, AI_DEPTH, -math.inf, math.inf)
            if move:
                grid = apply_move(grid, move)
                if check_win(grid):
                    print(f"{check_win(grid).upper()} wins!")
                    game_over = True
            current_player = HUMAN_PLAYER
            draw_board(grid)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if RESTART_BUTTON.collidepoint(ev.pos):
                    main(); return
                if not game_over and current_player == HUMAN_PLAYER:
                    x, y = ev.pos
                    if MARGIN <= x < MARGIN + BOARD_SIZE*CELL_SIZE and MARGIN <= y < MARGIN + BOARD_SIZE*CELL_SIZE:
                        r = (y - MARGIN)//CELL_SIZE
                        c = (x - MARGIN)//CELL_SIZE
                        if grid[r][c] == HUMAN_PLAYER:
                            drag_start = (r, c)
                            drag_pos = ev.pos
                            grid[r][c] = 'o'
            elif ev.type == pygame.MOUSEMOTION and drag_start:
                drag_pos = ev.pos
            elif ev.type == pygame.MOUSEBUTTONUP and drag_start:
                x, y = ev.pos
                sr, sc = drag_start
                er = (y - MARGIN)//CELL_SIZE
                ec = (x - MARGIN)//CELL_SIZE
                dr_d = er - sr
                dc_d = ec - sc
                if abs(dr_d) > abs(dc_d):
                    direction = 'down' if dr_d>0 else 'up'
                else:
                    direction = 'right' if dc_d>0 else 'left'
                dest = compute_destination(grid, sr, sc, *DIRS[direction])
                if dest:
                    nr, nc = dest
                    grid[nr][nc] = HUMAN_PLAYER
                    if check_win(grid):
                        print(f"{check_win(grid).upper()} wins!")
                        game_over = True
                    current_player = AI_PLAYER
                else:
                    grid[sr][sc] = HUMAN_PLAYER
                drag_start = None
                drag_pos = None
        clock.tick(FPS)
        draw_board(grid, drag_start, drag_pos)

if __name__ == '__main__':
    main()
