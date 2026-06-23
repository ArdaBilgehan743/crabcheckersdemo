# Crab Checkers Gameplay Upgrade Plan

This document is the working plan for polishing Crab Checkers into a cleaner, more complete game. It should guide implementation, keep scope visible, and capture the design choices that need the user's vision before larger changes land.

## Current Snapshot

- The game is a 6x6 sliding-piece alignment game built with Pygame.
- The win condition is four same-color crabs in a horizontal or vertical line.
- Human-vs-human and human-vs-AI exist as separate scripts.
- Core rule logic is duplicated across multiple files.
- AI experiments exist for minimax, MCTS, random simulation, and opening evaluation.
- The UI is functional but minimal: drag pieces, restart, basic turn text.

## Implementation Direction

Build toward one polished playable app with clean shared game logic:

- One importable rules module for board state, legal moves, move application, win/draw checks, and notation.
- One AI module for random, minimax, and eventually MCTS players.
- One Pygame app entry point with selectable modes and difficulty.
- Small test coverage for the pure rules and AI helpers.
- Optional simulation tools that import the shared rules instead of duplicating them.

## Vision Decisions

- Visual direction: character-first indie board game, inspired by the uploaded sketch of two distinct table-side players sitting around a board.
- Main menu direction: the player should choose characters before starting, with the chosen characters visually sitting at or framing the board.
- Pivot: the game should become a 3D roguelike strategy game, not just a polished 2D board game.
- The player should see the table from a POV/cinematic 3D camera while characters physically make the moves.
- The current Pygame version is now treated as a rules/prototype branch, while the new primary experience should be a Three.js build.
- Board: keep the current 6x6 board for now.
- Rules: keep horizontal/vertical four-in-a-row wins for the first cleanup pass.
- Draws: add official draw handling.
- Main modes: support both local two-player and player-vs-AI.
- Controls: support drag, click-to-move, arrow buttons, and keyboard controls.
- AI difficulty: present choices like "stakes" or difficulty tiers, initially Easy, Mid, and Hard.
- Future direction: explore a Balatro-like indie structure where characters, joker-style modifiers, stakes, and run choices can change movement or scoring rules.

## 3D Roguelike Direction

- [x] Build a Three.js prototype as the new primary playable direction.
- [x] Show the board on a 3D table with a player-side POV camera.
- [x] Put selected characters around the board as stylized 3D table avatars.
- [x] Animate the active character reaching toward the board when a move happens.
- [x] Animate crab tokens sliding across the 3D board.
- [x] Add camera modes:
  - Player POV.
  - Table overview.
  - Opponent POV / cinematic.
- [x] Add roguelike run structure:
  - Start a run.
  - Choose a character.
  - Choose a stake.
  - Win rounds.
  - Draft modifier cards between rounds.
  - Lose and restart the run.
- [x] Add modifier cards that actually alter rules.
  - Reef Drift: crabs may stop early.
  - Side Step: limited diagonal slides.
  - Tide Lens: show stronger preview/hint information.
- [ ] Keep the base 6x6 Crab Checkers rule readable before adding heavier twists.

## Core Cleanup Tasks

- [ ] Rename scripts with spaces or confusing names.
  - `crab checkers.py` should become a normal entry point such as `main.py`.
  - `import pygame.py` should be removed or renamed after confirming whether it is just a duplicate of `vsai.py`.
- [x] Extract shared game rules into a reusable module.
- [ ] Update all scripts to import the shared rules.
- [ ] Fix known script issues.
  - `minimax_selfplay.py` calls `play_minimax(depth=8,max_turns=100)`, but `play_minimax` currently does not accept `max_turns`.
  - MCTS currently appears to mutate/reassign `namedtuple` nodes in a way that likely prevents tree statistics from persisting correctly.
- [x] Add `requirements.txt` with `pygame`.
- [x] Add a README with rules, controls, game modes, and run commands.
- [x] Add basic tests for destination calculation, legal moves, move application, win checks, and draw/repetition checks.

## Gameplay Polish Tasks

- [x] Add a main menu or start panel.
  - Human vs Human.
  - Human vs AI.
  - AI vs AI / watch mode remains pending.
  - Difficulty selection.
- [x] Add character selection before game start.
- [x] Show selected characters sitting beside or framing the board.
- [x] Add future-ready data structures for character powers and modifier cards, even if powers are disabled at first.
- [x] Move side selection into the Pygame UI instead of terminal input.
- [x] Highlight selected crab clearly.
- [x] Highlight all legal destination squares for the selected crab.
- [x] Show a ghost destination while dragging.
- [x] Animate slides to the final square.
- [x] Add clear invalid-move feedback.
- [x] Add move history with readable notation.
- [x] Add undo.
- [ ] Add restart confirmation or an intentional reset flow.
- [x] Add win overlay with winner, final move count, restart, and menu options.
- [x] Add draw detection and visible draw messaging.
- [x] Add board coordinates for easier move discussion.
- [x] Add optional keyboard controls.
- [x] Add simple sound effects with a mute toggle.
- [x] Improve visual identity with crab-themed pieces, stronger board contrast, and polished typography.

## AI Upgrade Tasks

- [x] Add AI difficulty levels.
  - Easy Stake: random legal move.
  - Mid Stake: shallow minimax.
  - Hard: deeper minimax with stronger heuristic.
  - Experimental: MCTS after the implementation is fixed.
- [x] Improve the heuristic.
  - Reward immediate wins.
  - Block opponent immediate wins.
  - Reward three-in-a-row threats.
  - Reward flexible mobility.
  - Reward central control only if it helps the actual strategy.
- [x] Add AI thinking status.
- [x] Add optional hint button using the same AI engine.
- [ ] Cache or speed up opening evaluation tools.
- [ ] Use simulations to test whether the starting position is fair.

## Balance And Rules Tasks

- [x] Decide the official draw rule.
- [x] Decide whether repeated positions are forbidden, drawn, or allowed.
- [x] Implement draw after three repeated positions with the same side to move.
- [ ] Test whether the current starting layout favors B.
- [ ] Consider alternate starting layouts if balance remains uneven.
- [ ] Consider optional rule variants.
  - Diagonal wins.
  - Five-in-a-row on larger boards.
  - Obstacles or shells.
  - Timed turns.
  - Best-of series scoring.

## Character And Modifier Ideas

These are future-facing ideas inspired by the requested Balatro-like direction. They should be implemented after the base game is stable.

- Characters:
  - The Bear: slow, defensive, maybe earns a bonus when blocking a line.
  - The Hat Player: slippery, tactical, maybe previews extra legal moves or gains one altered slide per round.
  - Future characters can have passive powers, one-use powers, or personality-specific AI behavior.
- Joker-style modifiers:
  - Reef Drift: once per game, a crab may stop early instead of sliding all the way.
  - Shell Shield: one selected crab cannot be moved by modifier effects for a round.
  - Tide Turn: reverse the board orientation or swap turn order rules for one turn.
  - Side Step: allow one diagonal slide as a special move.
  - Crab Chorus: forming three-in-a-row creates a temporary bonus.
- Stakes:
  - Easy Stake: forgiving AI, visible hints, no extra penalties.
  - Mid Stake: stronger AI, hints optional, standard draw rules.
  - Hard Stake: deeper AI, fewer assists, maybe future modifier penalties.

## Suggested Milestones

### Milestone 1: Clean Foundation

- Extract rules.
- Rename entry points.
- Add requirements and README.
- Add tests for core rules.

### Milestone 2: One Complete Playable App

- Combine human-vs-human and human-vs-AI into one app.
- Add mode selection, side selection, restart, win/draw overlays.
- Add legal move highlighting and invalid-move feedback.
- Add character selection placeholders and selected-character panels.

### Milestone 3: Better Feel

- Add animations, ghost destinations, move history, undo, and board coordinates.
- Improve colors, typography, spacing, and piece styling.

### Milestone 4: Smarter Opponents

- Add difficulty levels.
- Improve minimax heuristic.
- Fix or replace MCTS.
- Add hint mode.

### Milestone 5: Balance Pass

- Run simulations across starting layouts and AI levels.
- Tune the default board if needed.
- Document official rules.

## Vision Questions

Answering these will shape the game before implementation gets too opinionated.

1. What should the vibe be: cute beach/crab board game, clean abstract strategy game, arcade-y, or something else?
2. Should the game stay on a 6x6 board, or do you want support for 8x8 or custom board sizes later?
3. Should wins stay horizontal/vertical only, or should diagonals count too?
4. Should repeated positions become a draw after three repeats, be prevented, or be allowed?
5. Do you want the main experience to be local two-player, player vs AI, or both equally important?
6. Should the AI feel beatable and fun, or should the hardest mode try to be genuinely ruthless?
7. Do you want playful crab graphics and sound effects, or a quieter minimalist look?
8. Should moves use drag only, click-piece-then-destination, arrow buttons, keyboard controls, or all of them?
9. Do you want undo to work against the AI, and if yes, should one undo reverse both the player move and AI response?
10. Should there be timed turns or a casual untimed mode only?
11. Do you want a scoreboard across multiple rounds?
12. Is the current red-vs-blue color identity good, or do you want named crab teams/themes?
13. Should I preserve the existing scripts as research tools, or fold everything into a cleaner package and remove duplicates?
14. Do you want packaging later, such as a double-clickable Mac app?
15. What matters most for the first pass: cleanup, visual polish, smarter AI, or extra game features?

## Answered Vision Questions

1. The desired vibe is based on the uploaded sketch: two characterful players sitting around a board, with the game beginning from character choice.
2. Keep the current 6x6 board for now, with room to evolve later.
3. Keep the current win condition for now.
4. Repeated positions should produce draws.
5. Local two-player and player-vs-AI both matter.
6. AI should use Balatro-like stakes/difficulty choices: Easy, Mid, Hard.
7. The visual direction should be characterful and indie rather than purely abstract.
8. Support all controls: drag, click, arrows, and keyboard.
9. Undo behavior still needs a final decision for AI games.
10. Timed turns are still undecided.
11. Scoreboard across rounds is still undecided.
12. Teams/themes are still open.
13. Cleanup approach is still open, but the first implementation should make a clean package while preserving old experiments unless removal is explicitly approved.
14. Packaging can be considered later.
15. First pass should combine cleanup, gameplay polish, draw support, both main modes, and stake-style AI difficulty.

## First Pass Recommendation

Start with Milestone 1 and Milestone 2. That gives the project a clean base and one enjoyable game loop before deeper AI and balance work.
