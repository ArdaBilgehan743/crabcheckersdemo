# Crab Checkers

Crab Checkers is becoming a 3D roguelike strategy game about characterful table duels. The original 6x6 sliding-piece rules still drive the board, but the new primary prototype uses Three.js: players choose a character and stake, see the board from a POV camera, watch table avatars make moves, and draft modifier cards between won rounds.

## Run The 3D Prototype

```bash
npm install
npm run dev -- --port 5173
```

Then open `http://127.0.0.1:5173/`.

## Generate Blender Assets

Blender source assets and runtime `.glb` models can be regenerated with:

```bash
npm run assets:blender
```

This writes editable Blender sources to `assets/blender/source/` and runtime models to `public/models/`.

## Run The Pygame Prototype

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

The older Python scripts are still kept as prototypes and research tools.

## Rules

- Player A uses red crabs and Player B uses blue crabs.
- On your turn, choose one of your crabs and slide it up, down, left, or right.
- A crab slides as far as it can until the board edge or another crab blocks it.
- The first player to make four crabs in a horizontal or vertical row wins.
- If the same board position with the same player to move appears three times, the game is a draw.
- If a player has no legal move, the other player wins.

## Controls

- Drag a crab in a direction to slide it.
- Click a crab, then click a highlighted destination.
- Click the small arrow buttons near highlighted destinations.
- Use keyboard arrows to move a selected crab.
- Use `Tab` to cycle the keyboard cursor through your crabs.
- Use `Space` to select or clear the keyboard cursor selection.
- Use `H` for a hint, `U` for undo, `R` to restart, `M` to mute, and `Esc` to return to the menu.

## Modes

- `Vs AI`: play against the computer.
- `2 Players`: local player-vs-player.
- `Easy Stake`: random legal AI moves.
- `Mid Stake`: shallow minimax.
- `Hard Stake`: deeper minimax.

## 3D Direction

- `Low Tide`, `Red Tide`, and `Black Tide` act as stake choices.
- Winning a solo round opens a modifier draft.
- Current modifiers include movement, economy, risk, and vision changes like `Reef Drift`, `Side Step`, `Pearl Bank`, `Black Pearl`, and `Tide Chart`.
- If every modifier has been collected, the draft becomes a cache reward instead of showing an empty screen.
- Camera modes include tactical play view, player POV, table overview, and rival POV.
- Characters are stylized 3D table avatars that reach toward the board as moves happen.

## Verify

```bash
npm run assets:blender
npm run build
npm run verify:3d
./.venv/bin/python -m unittest discover -s tests
```
