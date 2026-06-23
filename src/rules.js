export const BOARD_SIZE = 6;
export const EMPTY = 'o';
export const PLAYER_A = 'a';
export const PLAYER_B = 'b';

export const START_BOARD = [
  'boaboa',
  'oooooo',
  'aoooob',
  'booooa',
  'oooooo',
  'aobaob',
];

const BASE_DIRECTIONS = {
  up: [-1, 0],
  down: [1, 0],
  left: [0, -1],
  right: [0, 1],
};

const DIAGONAL_DIRECTIONS = {
  upLeft: [-1, -1],
  upRight: [-1, 1],
  downLeft: [1, -1],
  downRight: [1, 1],
};

export function cloneBoard(board) {
  return board.map((row) => row.slice());
}

export function opponent(player) {
  return player === PLAYER_A ? PLAYER_B : PLAYER_A;
}

export function inBounds(row, col) {
  return row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE;
}

export function hasModifier(modifiers, key) {
  return modifiers.includes(key);
}

export function directionMap(modifiers = []) {
  return hasModifier(modifiers, 'side_step')
    ? { ...BASE_DIRECTIONS, ...DIAGONAL_DIRECTIONS }
    : BASE_DIRECTIONS;
}

export function destinationsFor(board, row, col, direction, modifiers = []) {
  const dirs = directionMap(modifiers);
  if (!dirs[direction] || !inBounds(row, col) || board[row][col] === EMPTY) return [];
  const [dr, dc] = dirs[direction];
  const destinations = [];
  let nr = row;
  let nc = col;
  while (true) {
    const nextRow = nr + dr;
    const nextCol = nc + dc;
    if (!inBounds(nextRow, nextCol) || board[nextRow][nextCol] !== EMPTY) break;
    nr = nextRow;
    nc = nextCol;
    destinations.push({ row: nr, col: nc });
  }
  if (destinations.length === 0) return [];
  if (hasModifier(modifiers, 'reef_drift')) return destinations;
  if (hasModifier(modifiers, 'tide_chart')) {
    const middle = destinations[Math.floor((destinations.length - 1) / 2)];
    const final = destinations.at(-1);
    return middle === final ? [final] : [middle, final];
  }
  return [destinations.at(-1)];
}

export function legalMoves(board, player, modifiers = []) {
  const moves = [];
  const dirs = Object.keys(directionMap(modifiers));
  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let col = 0; col < BOARD_SIZE; col += 1) {
      if (board[row][col] !== player) continue;
      for (const direction of dirs) {
        for (const to of destinationsFor(board, row, col, direction, modifiers)) {
          moves.push({ row, col, direction, to });
        }
      }
    }
  }
  return moves;
}

export function applyMove(board, move) {
  const next = cloneBoard(board);
  const player = next[move.row][move.col];
  next[move.row] = replaceAt(next[move.row], move.col, EMPTY);
  next[move.to.row] = replaceAt(next[move.to.row], move.to.col, player);
  return next;
}

function replaceAt(row, col, value) {
  return row.slice(0, col) + value + row.slice(col + 1);
}

export function checkWinner(board) {
  const streaks = ['aaaa', 'bbbb'];
  for (const row of board) {
    for (const streak of streaks) {
      if (row.includes(streak)) return streak[0];
    }
  }
  for (let col = 0; col < BOARD_SIZE; col += 1) {
    let line = '';
    for (let row = 0; row < BOARD_SIZE; row += 1) line += board[row][col];
    for (const streak of streaks) {
      if (line.includes(streak)) return streak[0];
    }
  }
  return null;
}

export function countOpenThrees(board, player) {
  let count = 0;
  const lines = [...board];
  for (let col = 0; col < BOARD_SIZE; col += 1) {
    let line = '';
    for (let row = 0; row < BOARD_SIZE; row += 1) line += board[row][col];
    lines.push(line);
  }
  for (const line of lines) {
    for (let start = 0; start <= BOARD_SIZE - 4; start += 1) {
      const window = line.slice(start, start + 4);
      if (window.split(player).length - 1 === 3 && window.includes(EMPTY)) count += 1;
    }
  }
  return count;
}

export function boardKey(board, player) {
  return `${board.join('/')}|${player}`;
}

export function cellName(row, col) {
  return `${String.fromCharCode(97 + col)}${row + 1}`;
}

export function moveNotation(move) {
  return `${cellName(move.row, move.col)} -> ${cellName(move.to.row, move.to.col)}`;
}
