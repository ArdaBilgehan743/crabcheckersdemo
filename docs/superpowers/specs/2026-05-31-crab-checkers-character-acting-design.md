# Crab Checkers — Character Acting Pass ("Liar's Bar" feel, pass 2)

- **Date:** 2026-05-31
- **Status:** Approved; implementing
- **Goal:** Give the Patient Bear *presence and tension* — it watches you, stares you down, reacts, gloats — the way Liar's Bar opponents do.
- **Owner files:** `tools/blender/...` (live Blender), `public/models/avatar-bear.glb`, `src/main.js`

## New / upgraded Bear clips (Blender)
- **`stare`** (loop) — intense lean-in, locked stare, narrowed eyes (eye scale.y down), slow breath. The "reading you" tell.
- **`smug`** (one-shot → idle) — chin up, slow confident bob, chest puffed. Played when the Bear is ahead / just built a threat.
- **`flinch`** (one-shot → stare) — quick recoil + blink + ears back. The Bear *noticing* a dangerous move.
- **`idle` upgrade** — richer micro-life: occasional glance down at the board and back up, paw shift, double-blink, weight shifts. Re-authored to replace the current idle.

Re-export `avatar-bear.glb` with all clips via `export_animation_mode='NLA_TRACKS'`. (Reload `avatar-bear.blend` first — the live scene was cleared to build the crab.)

## Reaction logic (three.js director)
- **Bear's turn:** `stare` (stare-down beat) → reach, instead of plain think.
- **Player forms an open three** (`countOpenThrees(PLAYER_A)` increased after the player's move): Bear `flinch` → `stare`.
- **Bear builds an open three / is ahead** (`countOpenThrees(PLAYER_B)` increased): Bear `smug`.
- **Otherwise:** richer `idle`.
- Keep existing win/lose/draft/reach behavior.

## Procedural eye-contact (three.js, stretch)
- Cache the cloned Bear's `bear_j_head` node; after `mixer.update`, slerp the head a fraction toward facing the live POV camera, layered over the playing clip, clamped to a small cone. If the rig orientation fights it, fall back to the `stare` clip for the eye-contact read. Subtle eye nudge optional.

## Success criteria
- [ ] Bear stares you down before moving; flinches when you threaten; gloats when ahead; idle feels alive (never frozen).
- [ ] `avatar-bear.glb` re-exports with the new named clips; loads with no errors.
- [ ] `npm run verify:3d` still passes (desktop + mobile); atmosphere + existing anims intact.
- [ ] (Stretch) the Bear visibly watches the camera in POV.

## Risks
- Procedural head-track vs. clip-driven head rotation: apply gaze AFTER mixer update as a partial slerp so the clip still reads; descope to `stare` clip if it conflicts.
- New clips must chain back to idle/stare via the existing `onAvatarActionFinished` map (extend it).
- Reaction spam: debounce so reactions don't retrigger every frame; trigger on state-change only.
