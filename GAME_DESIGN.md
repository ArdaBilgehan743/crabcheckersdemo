# Crab Checkers 3D: Roguelike Strategy Design

## North Star

Crab Checkers should feel like sitting across from strange, memorable opponents at a small table where the board is simple, but the run becomes increasingly unstable through character powers, stakes, and modifier cards.

The game is not just "checkers in 3D." The target is a roguelike table duel with:

- A readable 6x6 strategy board.
- Characters who physically make moves.
- A tactical camera for clean play.
- Cinematic POV cameras for mood.
- Run-based escalation inspired by roguelike deckbuilders.
- Professional Blender-made characters, table props, tokens, and animations.

## Research Notes

- Balatro succeeds by making a familiar base game mutate through game-changing jokers and escalating stakes. The useful lesson is not "copy poker," but "simple core plus explosive modifiers."
- Inscryption is useful as a table-presence reference: the opponent, room, lighting, and between-game space matter as much as the cards.
- Three.js Raycaster-style picking is the right interaction base, but board games need forgiving hit targets because cinematic cameras make precise picking harder.
- glTF/GLB is the right runtime asset format for web 3D. It supports meshes, materials, textures, cameras, lights, skinning, and keyframe animation from Blender.

## Core Game Loop

1. Start a run.
2. Choose a character.
3. Choose a stake.
4. Play a Crab Checkers round.
5. Win to draft a modifier.
6. Repeat with escalating pressure.
7. Lose the run and restart with better knowledge.

## Moment-To-Moment Play

- The board remains a 6x6 slide-to-block grid.
- The player selects a crab, then selects a valid destination.
- The active table character reaches forward and moves the crab.
- The camera defaults to Tactical view for clarity.
- Player POV, table overview, and rival POV are cinematic modes, not the default precision mode.

## Camera Design

### Tactical View

Purpose: play the game cleanly.

- Default in active rounds.
- High, slightly tilted angle.
- Board dominates the frame.
- Large invisible hit targets sit above destinations.

### Player POV

Purpose: fantasy and mood.

- Lower angle from the player's seat.
- Shows opponent and board depth.
- Good for animations and round starts.

### Table View

Purpose: readable overview.

- Higher camera for strategy inspection.
- Useful when modifiers increase move complexity.

### Rival POV

Purpose: cinematic tension.

- Used during rival turns, boss/stake moments, and end screens.

## Characters

### Patient Bear

Role: defensive anchor.

Possible power:

- **Heavy Paw:** once per round, lock one crab from being moved by modifiers.
- **Hibernate:** if Bear blocks a three-in-a-row threat, gain a shell.

### The Hat

Role: trickster tempo.

Possible power:

- **Side Glance:** once per round, create one diagonal slide.
- **Sleight:** after drafting a modifier, reroll one offered modifier.

### Lantern Keeper

Role: information and foresight.

Possible power:

- **Lantern Tell:** selected crabs reveal the strongest legal destination.
- **Warm Read:** see one rival threat before it forms.

## Modifier Design

Modifiers should be small rule-benders that create build identity.

### Movement Modifiers

- **Reef Drift:** crabs may stop on any empty square along a slide.
- **Side Step:** diagonal slides are legal.
- **Hook Claw:** once per round, pull a crab one square before sliding.

### Information Modifiers

- **Tide Lens:** selecting a crab marks a strong destination.
- **Lantern Oil:** hints also show opponent threats.

### Economy Modifiers

- **Crab Chorus:** forming three-in-a-row earns a shell.
- **Undertow:** after a round win, start the next round with one bonus shell.
- **Pearl Bank:** round wins give extra shells.
- **Center Reef:** moving into the center earns a shell.
- **Corner Cache:** moving into a corner earns two shells.
- **First Blood Tide:** the first player move of each round earns a shell.

### Risk Modifiers

- **Blood Moon Tide:** both players get diagonal slides, but the rival moves first next round.
- **Cracked Board:** one random square becomes blocked each round.
- **Black Pearl:** wins pay more, but the rival searches deeper.

### Draft Fallback

When the player has collected every modifier, the reward screen must never be empty. It becomes a cache choice that pays shells or raises the tide.

## Stakes

### Low Tide

- Forgiving AI.
- More modifier choices.
- Clear hints.

### Red Tide

- Standard AI.
- Normal modifier choices.
- Standard draw rules.

### Black Tide

- Stronger AI.
- Fewer modifier choices.
- Future boss rules can appear.

## Professional Art Direction

The target is "premium stylized tabletop noir," not generic low-poly.

- Handcrafted 3D characters with strong silhouettes.
- Warm lantern lighting.
- Slightly eerie room, but not full horror.
- Tactile materials: worn wood, painted crab tokens, cloth board, brass lamp, inked props.
- Character designs should keep the uploaded sketch's spirit: big readable personalities around a board.

## Prototype Priorities

1. Keep the board interaction clean.
2. Replace primitives with GLB assets.
3. Add character-specific powers.
4. Add a map/ante sequence.
5. Add opponent behavior and tells.
6. Add sound, haptics-like camera shakes, and table reactions.

## Sources Used

- [Balatro official site](https://www.playbalatro.com/)
- [PlayStation Blog: Inscryption overview](https://blog.playstation.com/2022/07/07/psychological-horrors-stack-in-devilish-deck-builder-inscryption/)
- [Three.js docs](https://threejs.org/docs/)
- [Khronos glTF overview](https://www.khronos.org/gltf/)
- [Blender glTF 2.0 manual](https://docs.blender.org/manual/en/4.0/addons/import_export/scene_gltf2.html)
