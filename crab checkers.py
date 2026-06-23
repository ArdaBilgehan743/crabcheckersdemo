import pygame
import sys

# --- Configuration ---
CELL_SIZE = 80
BOARD_ROWS = BOARD_COLS = 6
MARGIN = 20
INFO_WIDTH = 200
WINDOW_WIDTH = CELL_SIZE * BOARD_COLS + INFO_WIDTH + 2 * MARGIN
WINDOW_HEIGHT = CELL_SIZE * BOARD_ROWS + 2 * MARGIN
FPS = 30

# Colors
BG_COLOR = (245, 222, 179)    # wheat
GRID_COLOR = (160, 82, 45)    # sienna
A_COLOR = (200, 50, 50)       # red-ish
B_COLOR = (50, 50, 200)       # blue-ish
HIGHLIGHT_COLOR = (34, 139, 34)
ARROW_COLOR = (34, 139, 34)
DISABLED_COLOR = (200, 200, 200)
TEXT_COLOR = (20, 20, 20)

# Directions
DIRS = {
    "up":    (-1,  0),
    "down":  ( 1,  0),
    "left":  ( 0, -1),
    "right": ( 0,  1),
}

# Arrow button positions
ARROW_BUTTONS = {
    "up":    pygame.Rect(MARGIN + BOARD_COLS*CELL_SIZE + 60, MARGIN + 20, 40, 40),
    "down":  pygame.Rect(MARGIN + BOARD_COLS*CELL_SIZE + 60, MARGIN + 100, 40, 40),
    "left":  pygame.Rect(MARGIN + BOARD_COLS*CELL_SIZE + 20, MARGIN + 60, 40, 40),
    "right": pygame.Rect(MARGIN + BOARD_COLS*CELL_SIZE + 100, MARGIN + 60, 40, 40),
}

# Restart button
RESTART_BUTTON = pygame.Rect(
    MARGIN + BOARD_COLS*CELL_SIZE + INFO_WIDTH//2 - 50,
    MARGIN + 260, 100, 40
)

# --- Initial Game State ---
initial_grid = [
    list("boaboa"),
    list("oooooo"),
    list("aoooob"),
    list("booooa"),
    list("oooooo"),
    list("aobaob"),
]

def reset_game():
    global grid, current_player, selected_crab, drag_start, drag_pos, game_over, winner
    grid = [row.copy() for row in initial_grid]
    current_player = 'a'
    selected_crab = None
    drag_start = None
    drag_pos = None
    game_over = False
    winner = None

# Set up the game
reset_game()

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

def compute_destination(r, c, dr, dc):
    nr, nc = r, c
    while True:
        nr2, nc2 = nr + dr, nc + dc
        if not (0 <= nr2 < BOARD_ROWS and 0 <= nc2 < BOARD_COLS):
            break
        if grid[nr2][nc2] != 'o':
            break
        nr, nc = nr2, nc2
    return (nr, nc) if (nr, nc) != (r, c) else None

def scan_win():
    global game_over, winner
    for r in range(BOARD_ROWS):
        row = ''.join(grid[r])
        if 'aaaa' in row:
            game_over, winner = True, 'A'
            return
        if 'bbbb' in row:
            game_over, winner = True, 'B'
            return
    for c in range(BOARD_COLS):
        col = ''.join(grid[r][c] for r in range(BOARD_ROWS))
        if 'aaaa' in col:
            game_over, winner = True, 'A'
            return
        if 'bbbb' in col:
            game_over, winner = True, 'B'
            return

def draw_board():
    screen.fill(BG_COLOR)
    # grid lines
    for i in range(BOARD_ROWS+1):
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN, MARGIN + i*CELL_SIZE),
                         (MARGIN + BOARD_COLS*CELL_SIZE, MARGIN + i*CELL_SIZE), 3)
    for j in range(BOARD_COLS+1):
        pygame.draw.line(screen, GRID_COLOR,
                         (MARGIN + j*CELL_SIZE, MARGIN),
                         (MARGIN + j*CELL_SIZE, MARGIN + BOARD_ROWS*CELL_SIZE), 3)
    # pieces
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            if grid[r][c] != 'o':
                # skip original spot while dragging
                if selected_crab and drag_start == (r, c):
                    continue
                color = A_COLOR if grid[r][c] == 'a' else B_COLOR
                cx = MARGIN + c*CELL_SIZE + CELL_SIZE//2
                cy = MARGIN + r*CELL_SIZE + CELL_SIZE//2
                pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE//2 - 10)
    # draw dragging crab at mouse
    if drag_pos and selected_crab:
        r, c = selected_crab
        color = A_COLOR if current_player == 'a' else B_COLOR
        mx, my = drag_pos
        pygame.draw.circle(screen, color, (mx, my), CELL_SIZE//2 - 10)
    # highlight selected crab
    if selected_crab and not drag_start:
        r, c = selected_crab
        rect = pygame.Rect(MARGIN + c*CELL_SIZE+2, MARGIN + r*CELL_SIZE+2,
                           CELL_SIZE-4, CELL_SIZE-4)
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, rect, 4)
    # draw arrows (optional)
    for d, rect in ARROW_BUTTONS.items():
        playable = False
        if selected_crab and not game_over:
            dr, dc = DIRS[d]
            r, c = selected_crab
            dest = compute_destination(r, c, dr, dc)
            playable = bool(dest)
        color = ARROW_COLOR if playable else DISABLED_COLOR
        cx, cy = rect.center
        if d == 'up':
            pts = [(cx, cy-12), (cx-12, cy+8), (cx+12, cy+8)]
        elif d == 'down':
            pts = [(cx, cy+12), (cx-12, cy-8), (cx+12, cy-8)]
        elif d == 'left':
            pts = [(cx-12, cy), (cx+8, cy-12), (cx+8, cy+12)]
        else:
            pts = [(cx+12, cy), (cx-8, cy-12), (cx-8, cy+12)]
        pygame.draw.polygon(screen, color, pts)
    # restart button
    pygame.draw.rect(screen, GRID_COLOR, RESTART_BUTTON)
    pygame.draw.rect(screen, BG_COLOR, RESTART_BUTTON.inflate(-4, -4))
    rt = font.render("Restart", True, TEXT_COLOR)
    screen.blit(rt, rt.get_rect(center=RESTART_BUTTON.center))
    # status
    status = f"Turn: {'A' if current_player=='a' else 'B'}"
    if game_over:
        status = f"{winner} wins!"
    txt = font.render(status, True, TEXT_COLOR)
    screen.blit(txt, (MARGIN + BOARD_COLS*CELL_SIZE + 10, MARGIN + 200))

def get_cell(pos):
    x, y = pos
    if (MARGIN <= x < MARGIN + BOARD_COLS*CELL_SIZE and
        MARGIN <= y < MARGIN + BOARD_ROWS*CELL_SIZE):
        return ((y - MARGIN)//CELL_SIZE, (x - MARGIN)//CELL_SIZE)
    return None

# --- Main Loop ---
while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # mouse down
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if RESTART_BUTTON.collidepoint(ev.pos):
                reset_game()
            else:
                cell = get_cell(ev.pos)
                if cell and not game_over:
                    r, c = cell
                    if grid[r][c] == current_player:
                        drag_start = cell
                        selected_crab = cell
                        drag_pos = ev.pos

        # mouse motion (update drag)
        elif ev.type == pygame.MOUSEMOTION and drag_start:
            drag_pos = ev.pos

        # mouse up (end drag)
        elif ev.type == pygame.MOUSEBUTTONUP and drag_start and not game_over:
            end_cell = get_cell(ev.pos)
            start_r, start_c = drag_start
            if end_cell and end_cell != drag_start:
                er, ec = end_cell
                dr_d = er - start_r
                dc_d = ec - start_c
                if abs(dr_d) > abs(dc_d):
                    dir_key = 'down' if dr_d > 0 else 'up'
                else:
                    dir_key = 'right' if dc_d > 0 else 'left'
                dr, dc = DIRS[dir_key]
                dest = compute_destination(start_r, start_c, dr, dc)
                if dest:
                    grid[start_r][start_c] = 'o'
                    rr, cc = dest
                    grid[rr][cc] = current_player
                    scan_win()
                    current_player = 'b' if current_player == 'a' else 'a'
            drag_start = None
            drag_pos = None
            selected_crab = None

    draw_board()
    pygame.display.flip()
    clock.tick(FPS)
