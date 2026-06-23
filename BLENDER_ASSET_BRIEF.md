# Crab Checkers 3D: Blender Asset Brief

This is the production brief for replacing the current Three.js primitive placeholders with professional Blender-made assets.

## Export Format

- Runtime format: `.glb`.
- Working source: `.blend`.
- Coordinate expectation: Y-up after import into Three.js.
- Scale: board cells are roughly `1.04` Three.js units wide.
- Use PBR materials compatible with glTF.
- Texture formats: PNG or JPEG.
- Bake normal, ambient occlusion, and roughness where useful.

## Folder Structure

```text
assets/blender/
  characters/
  props/
  tokens/
  source/
public/models/
  avatar-bear.glb
  avatar-hat.glb
  avatar-lantern.glb
  crab-red.glb
  crab-blue.glb
  table-room.glb
  board-6x6.glb
```

## Current Generated Asset Set

The project now includes a Blender background generator:

```bash
npm run assets:blender
```

It creates the first production-pass procedural Blender sources and exports:

- `avatar-bear.blend` / `avatar-bear.glb`
- `avatar-hat.blend` / `avatar-hat.glb`
- `avatar-lantern.blend` / `avatar-lantern.glb`
- `avatar-diver.blend` / `avatar-diver.glb`
- `avatar-widow.blend` / `avatar-widow.glb`
- `crab-red.blend` / `crab-red.glb`
- `crab-blue.blend` / `crab-blue.glb`
- `board-6x6.blend` / `board-6x6.glb`
- `table-room.blend` / `table-room.glb`

These are real Blender-authored assets, but they are still a first generator pass. The next quality jump is hand-sculpting, retopology, UVs, texture painting, and authored animation clips in Blender.

## Character Deliverables

Each character should include:

- Clean silhouette readable from the game camera.
- Rigged upper body, head, and arm/hand controls.
- Idle animation loop.
- Reach animation.
- Move-confirm animation.
- Lose reaction.
- Win reaction.
- Optional facial shape keys or eye controls.

### Patient Bear

- Large soft bear-like table player.
- Broad shoulders, gentle face, large paws.
- Should read as defensive and patient.
- Materials: warm fur, worn vest or table-player clothing.

### The Hat

- Mysterious hat-wearing strategist.
- Slim silhouette, strong hat shape, sly posture.
- Should read as tricky and sharp.
- Materials: dark felt hat, coat, pale hands.

### Lantern Keeper

- Smaller occult table host.
- Carries or wears lantern details.
- Should read as observant, strange, and calm.
- Materials: brass, glass, warm emissive lantern core.

### Pearl Diver

- Human gambler with goggles, sea-worn coat, and pearl-bag details.
- Should read as agile, risky, and charming.

### Velvet Widow

- Elegant human rival with veil, sharp silhouette, and precise hands.
- Should read as dangerous, controlled, and readable from table cameras.

## Token Deliverables

### Crab Tokens

- Two color variants: red and blue.
- Painted tabletop-token look, not realistic seafood.
- Rounded toy-like body.
- Tiny eye stalks and claws.
- Should remain readable from Tactical view.
- Target animation:
  - Slide.
  - Hop/settle.
  - Threat wiggle.
  - Win pulse.

## Board And Table Deliverables

### Board

- 6x6 board.
- Raised squares or carved grid.
- Materials: cloth, painted wood, or lacquered tabletop.
- Strong square readability under warm lighting.
- Must not be too noisy visually.

### Table Room

- Table, lamp, surrounding darkness, small props.
- Props may include shells, cards/modifiers, cup, score markers.
- Must leave the board unobstructed in Tactical view.

## Animation List

Required first-pass clips:

```text
idle
think
reach_start
reach_move
reach_release
win
lose
draft_card
```

The current prototype can use simple code-driven hand IK, but final assets should include authored animation clips for personality.

## Style Rules

- Avoid generic asset-store realism.
- Avoid ultra-low-poly placeholder style.
- Use exaggerated readable forms.
- Keep colors warm and muted with red/blue gameplay accents.
- Use material contrast: wood, cloth, shell, brass, painted token, fur/fabric.
- Build for readable gameplay first, cinematic beauty second.

## Technical Budgets

Early target budgets:

- Main character: 20k-45k triangles each.
- Crab token: 1k-4k triangles each.
- Board: 5k-15k triangles.
- Room/table props: 20k-50k triangles total.
- Texture sets: start at 1k or 2k; reserve 4k only for hero assets.

These can move after profiling, but they are a sane target for web delivery.

## Acceptance Checklist

- [ ] `.blend` source included.
- [ ] `.glb` export included.
- [ ] Model imports into Three.js without scale surprises.
- [ ] Materials survive glTF export.
- [ ] Animations appear as named clips.
- [ ] Character silhouettes are readable in Tactical and POV cameras.
- [ ] Board remains playable with HUD visible.
- [ ] Asset license is clear and project-safe.

## Research Notes

- glTF is designed for efficient runtime delivery of 3D scenes and models.
- Blender's glTF exporter supports meshes, materials, textures, cameras, lights, extras, and animation.
- Blender glTF exports support object transform, pose bone, and shape key animation, which fits the character/hand animation needs.

## Sources Used

- [Khronos glTF overview](https://www.khronos.org/gltf/)
- [Blender glTF 2.0 manual](https://docs.blender.org/manual/en/4.0/addons/import_export/scene_gltf2.html)
