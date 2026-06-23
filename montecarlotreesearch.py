import random
import math
from collections import defaultdict, namedtuple
import pprint

# --- Game definitions (as before) ---
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
        if not (0 <= nr2 < BOARD and 0 <= nc2 < BOARD):
            break
        if grid[nr2][nc2] != 'o':
            break
        nr, nc = nr2, nc2
    return (nr,nc) if (nr,nc) != (r,c) else None

def get_moves(grid, player):
    moves = []
    for r in range(BOARD):
        for c in range(BOARD):
            if grid[r][c] == player:
                for d, (dr,dc) in DIRS.items():
                    if compute_dest(grid, r, c, dr, dc):
                        moves.append((r,c,d))
    return moves

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
        s = ''.join(grid[r][c] for r in range(BOARD))
        if 'aaaa' in s: return 'a'
        if 'bbbb' in s: return 'b'
    return None

# --- MCTS Implementation ---
Node = namedtuple('Node', 'state player visits wins parent move children')

def make_node(state, player, parent=None, move=None):
    return Node(state=state, player=player, visits=0, wins=0, parent=parent, move=move, children=[])

def uct_score(node, child, c=1.4):
    if child.visits == 0:
        return float('inf')
    return (child.wins/child.visits) + c*math.sqrt(math.log(node.visits)/child.visits)

def select(node):
    # selection: choose child with highest UCT until leaf
    while node.children:
        node = max(node.children, key=lambda c: uct_score(node, c))
    return node

def expand(node):
    # expand one untried move
    moves = get_moves(node.state, node.player)
    tried = {child.move for child in node.children}
    for m in moves:
        if m not in tried:
            next_state = apply_move(node.state, m)
            next_player = 'b' if node.player=='a' else 'a'
            child = make_node(next_state, next_player, parent=node, move=m)
            node.children.append(child)
            return child
    return node

def simulate(node):
    # random playout
    grid = [row.copy() for row in node.state]
    player = node.player
    for _ in range(200):
        w = check_win(grid)
        if w: return w
        moves = get_moves(grid, player)
        if not moves:
            return 'b' if player=='a' else 'a'
        grid = apply_move(grid, random.choice(moves))
        player = 'b' if player=='a' else 'a'
    return 'draw'

def backprop(node, winner):
    # backpropagate result
    while node:
        node = node._replace(visits=node.visits+1,
                             wins=node.wins + (1 if winner==node.player else 0))
        node = node.parent

def mcts(root, iterations=500):
    for _ in range(iterations):
        leaf = select(root)
        child = expand(leaf)
        result = simulate(child)
        backprop(child, result)
    # choose best child
    return max(root.children, key=lambda c: c.visits)

# --- Play two MCTS AIs against each other ---
def stringify(grid):
    return "\n".join("".join(row) for row in grid)

def play_selfplay(iters=300):
    # start from the initial position, A to move
    root = make_node(initial_grid, 'a')
    # record every (board, side_to_move) we’ve actually played
    history = { (tuple(map(tuple, initial_grid)), 'a') }

    while True:
        # run MCTS to fill out root.children
        mcts(root, iterations=iters)

        # sort children by visit count (best evidence)
        children_sorted = sorted(
            root.children,
            key=lambda c: c.visits,
            reverse=True
        )

        # pick the best child *not* in history
        chosen = None
        for child in children_sorted:
            key = (tuple(map(tuple, child.state)), child.player)
            if key not in history:
                chosen = child
                break

        # if they ALL repeat, declare a draw
        if chosen is None:
            print("All moves lead to repetition—declaring draw.")
            break

        # apply the chosen move
        move       = chosen.move
        new_state  = chosen.state
        next_turn  = chosen.player

        # pretty-print
        print(f"Player {root.player.upper()} plays {move}")
        for row in new_state:
            print(''.join(row))
        print()

        # check for a win
        winner = check_win(new_state)
        if winner:
            print("Winner:", winner.upper())
            break

        # record it so we never play it again
        history.add((tuple(map(tuple, new_state)), next_turn))

        # re-root the tree at that child
        root = make_node(new_state, next_turn)


play_selfplay(iters=300)