import { applyMove, checkWinner, countOpenThrees, legalMoves, opponent } from './rules.js';

const WIN_SCORE = 100000;

export function chooseAiMove(board, player, modifiers, depth, rng = Math.random) {
  const moves = legalMoves(board, player, modifiers);
  if (moves.length === 0) return null;
  if (depth <= 0) return moves[Math.floor(rng() * moves.length)];
  const [, move] = minimax(board, player, player, modifiers, depth, -Infinity, Infinity);
  return move ?? moves[0];
}

export function chooseHint(board, player, modifiers) {
  const [, move] = minimax(board, player, player, modifiers, 2, -Infinity, Infinity);
  return move;
}

function minimax(board, current, aiPlayer, modifiers, depth, alpha, beta) {
  const winner = checkWinner(board);
  if (winner === aiPlayer) return [WIN_SCORE + depth, null];
  if (winner && winner !== aiPlayer) return [-WIN_SCORE - depth, null];
  if (depth === 0) return [evaluate(board, aiPlayer, modifiers), null];

  const moves = legalMoves(board, current, modifiers);
  if (moves.length === 0) {
    return opponent(current) === aiPlayer ? [WIN_SCORE + depth, null] : [-WIN_SCORE - depth, null];
  }

  let best = null;
  if (current === aiPlayer) {
    let value = -Infinity;
    for (const move of moves) {
      const [score] = minimax(applyMove(board, move), opponent(current), aiPlayer, modifiers, depth - 1, alpha, beta);
      if (score > value) {
        value = score;
        best = move;
      }
      alpha = Math.max(alpha, value);
      if (alpha >= beta) break;
    }
    return [value, best];
  }

  let value = Infinity;
  for (const move of moves) {
    const [score] = minimax(applyMove(board, move), opponent(current), aiPlayer, modifiers, depth - 1, alpha, beta);
    if (score < value) {
      value = score;
      best = move;
    }
    beta = Math.min(beta, value);
    if (alpha >= beta) break;
  }
  return [value, best];
}

function evaluate(board, player, modifiers) {
  const foe = opponent(player);
  const winner = checkWinner(board);
  if (winner === player) return WIN_SCORE;
  if (winner === foe) return -WIN_SCORE;
  const mobility = legalMoves(board, player, modifiers).length - legalMoves(board, foe, modifiers).length;
  const threats = countOpenThrees(board, player) - countOpenThrees(board, foe);
  return mobility * 4 + threats * 120 + centerScore(board, player) - centerScore(board, foe);
}

function centerScore(board, player) {
  let score = 0;
  for (let row = 0; row < board.length; row += 1) {
    for (let col = 0; col < board[row].length; col += 1) {
      if (board[row][col] !== player) continue;
      score += 4 - Math.abs(2.5 - row) - Math.abs(2.5 - col);
    }
  }
  return score;
}
