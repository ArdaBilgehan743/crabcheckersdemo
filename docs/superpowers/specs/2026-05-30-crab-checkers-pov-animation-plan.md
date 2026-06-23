# Crab Checkers — "Play POV" Animation: Implementation Plan

Companion to `2026-05-30-crab-checkers-pov-animation-design.md`. This is the build order. Each phase ends with an explicit verification step.

## Conventions (match the existing pipeline — important)

- **Authoring axis:** existing assets are authored **Y-up inside Blender** (height = +Y; board lies in the X–Z plane). The Bear and crab rigs MUST follow the same convention so they stay consistent with `board-6x6.glb` / `table-room.glb` scale and the current `src/main.js` loader. Do not "fix" it to Z-up.
- **Scale:** board cell ≈ `1.04` units. Bear base at Y≈0, head ≈ Y 1.5–2.0, facing +Z (toward the player seat / board).
- **Naming:** joints as empties `bear_j_<name>` (e.g. `bear_j_shoulder_R`); meshes `bear_<part>`; crab `crab_<part>`, `crab_j_<name>`.
- **Actions:** one named Action per clip, stashed to an NLA track per object so the glTF exporter (`export_animation_mode='ACTIONS'`) emits each as a separate named clip.
- **Verification tool:** `get_viewport_screenshot` (Blender) + `npm run build` / `npm run verify:3d` (web). 3D art has no unit tests; the screenshot IS the test.

## Phase 0 — Tools live ✅
Blender MCP connected; `get_scene_info` returns the scene. Done.

## Phase 1 — Patient Bear rig (parented hierarchy + light polish)
- Clear scene; rebuild the Bear's parts at the existing make_bear() coordinates, with refined forms (rounder paws, cleaner joined silhouette).
- Create joint **empties** at neck, both shoulders, elbows, wrists; parent mesh parts to the nearest joint; parent joints into the chain `bear_root → torso → (head→ears), (shoulder→upperarm→forearm→paw)×2`.
- Materials per the brief: warm fur, cream muzzle, worn red vest, ink, shell buttons.
- Shape keys on the head: `blink`, `brow`.
- **Verify:** screenshot front + 3/4; confirm hierarchy via `get_object_info`; test-rotate a shoulder empty and confirm the whole arm follows, then reset.

## Phase 2 — Bear animation actions
Author each as a named Action (keyframe joint rotations + torso/paw scale squash):
`idle` (loop), `think` (loop), `reach_start`, `reach_move`, `reach_release`, `win`, `lose`, `draft_card`. Stash each to NLA.
- **Verify:** scrub each action to mid-frame, screenshot, confirm the pose reads.

## Phase 3 — Crab token rig + actions
- Rebuild crab (body→claws, eye-stalks, legs) with joint empties; one rig, exported as `crab-red` and `crab-blue` (material swap).
- Actions: `slide` (loop), `hop_settle`, `threat_wiggle` (loop), `win_pulse` (loop).
- **Verify:** screenshot mid-action.

## Phase 4 — Export
- Save `.blend` to `assets/blender/source/`; export `.glb` to `public/models/` with `export_animation_mode='ACTIONS'`, `export_apply` (careful with shape keys — don't apply modifiers that break them).
- **Verify:** load the GLB headlessly (or via a tiny node/three check) and list animation names; confirm all clips present.

## Phase 5 — Reproducibility
- Fold the rig + animation authoring into `tools/blender/generate_assets.py` as deterministic functions (`rig_bear()`, `anim_bear_*()`, `rig_crab()`, `anim_crab_*()`); switch export to `export_animation_mode='ACTIONS'`.
- **Verify:** `npm run assets:blender` regenerates the animated GLBs headlessly with the same clip names.

## Phase 6 — three.js wiring (POV + performance director)
- Make POV the default play camera; keep Tactical on a key.
- Add an `AnimationMixer` per avatar + per crab; build a `PerformanceDirector` mapping game events → clips (see spec). Remember: player wins → Bear plays `lose`.
- **Verify:** `npm run build` + `npm run verify:3d`; manual full-round playthrough in POV (idle→think→reach→slide→hop→win/lose).

## Risks (carried from spec)
- Reach aiming: generic clip + procedural paw target; fall back to small forearm/paw IK if it misses.
- Blender 5.1 glTF exporter: confirm `export_animation_mode='ACTIONS'` flag at first export.
- `src/main.js` event hooks: confirm turn/move/round/draft events are reachable for the director.
- Y-up authoring: keep it; verify the Bear lands at the right scale/orientation next to the existing board in the web app.
