# Crab Checkers — "Play POV" Animation Design

- **Date:** 2026-05-30
- **Status:** Approved (design); implementation pending Blender MCP setup
- **Author:** Claude (brainstormed with user)
- **Scope owner files:** `tools/blender/generate_assets.py`, `src/main.js`, `public/models/*.glb`, `assets/blender/source/*.blend`

## North Star

Let the player sit in the chair and *play a real round of Crab Checkers from the POV camera* against **Patient Bear**, an opponent that visibly breathes, thinks, reaches across the table to move a crab, and reacts to winning and losing. The board game is unchanged; the win is making the opponent and the tokens feel alive from the seat.

## Goals (this v1 slice)

- POV becomes the default **play** camera (not just a cinematic mood camera).
- One fully animated hero opponent: **Patient Bear**.
- A rigged, lightly-polished Bear with a full named clip set.
- A shared crab-token rig (red + blue) with movement/feedback clips.
- A "performance director" in the three.js app that maps game events → animation clips.
- Everything reproducible headlessly via `npm run assets:blender` (live MCP edits captured as deterministic `bpy` code, not lost).

## Non-Goals (deferred to v2)

- The other four avatars (Hat, Lantern Keeper, Pearl Diver, Velvet Widow). Once the Bear rig + clips are proven, cloning the rig and re-timing per character is fast.
- Full sculpt / retopo / UV / texture-paint upgrade of the Bear (better as a later manual Blender pass).
- New gameplay rules, modifiers, or AI changes. Pure presentation layer.

## The Experience

- **Camera:** seated POV — low eye-level, slight downward tilt. Board fills the lower third; Bear's torso + head + paws fill the upper-center across the table; warm lamp key light. Tactical view remains available on a key for precision, but POV is the default during play.
- **Interaction (unchanged):** click a crab, click a highlighted destination (plus existing keyboard/drag controls). The player never has to leave the seat.
- **Perspective note:** Bear is the **opponent**. Player *wins the round* → Bear plays `lose`. Player *loses the round* → Bear plays `win`. (Easy to invert by accident — call it out in code.)

## Technical Approach

### Rig method: parented hierarchy + transform keyframes (NOT a skinned armature)

The current Bear is loose primitive objects (spheres/cubes) with no hierarchy, so nothing can move. We restructure into a **parented joint hierarchy** with empties as pivots and animate via object **TRS keyframes**:

```
bear_root
├─ bear_torso              (belly breathing via subtle scale)
│  ├─ bear_head
│  │  ├─ bear_ear_L / bear_ear_R   (twitch)
│  │  └─ (shape keys: blink, brow)
│  ├─ bear_shoulder_R → bear_upperarm_R → bear_forearm_R → bear_paw_R
│  └─ bear_shoulder_L → bear_upperarm_L → bear_forearm_L → bear_paw_L
└─ (mesh parts parented to the nearest joint)
```

Why over skinned weights: robust, reproducible in Python, exports to glTF as clean **node-animation tracks** that three.js plays directly via `AnimationMixer`, no weight-painting failure modes, and rigid toy-parts suit the stylized look. Softness comes from subtle squash-and-stretch (scale) on the torso/paws, not mesh deformation.

### Fidelity: rig + light polish

Keep the warm toy look. While rigging, refine the Bear's forms (cleaner joined silhouette, rounder paws, consistent joint pivots) and add two shape keys (`blink`, `brow`). Animation-first; clearly better than the current placeholder; fast to author live over MCP.

### Coordinate / scale contract (from BLENDER_ASSET_BRIEF.md)

- Runtime `.glb`, working `.blend`. Y-up after import into three.js. Board cells ≈ `1.04` three.js units. PBR/glTF-safe materials.

## Bear Clip Set

Named glTF actions (timings at 24 fps, approximate):

| Clip | Length | Loop | Trigger | Personality |
|------|--------|------|---------|-------------|
| `idle` | ~4.0s (96f) | yes | default / between turns | deep belly breathing (torso scale), slow head sway, occasional ear twitch + blink |
| `think` | ~3.0s (72f) | yes | while AI is searching | leans in, paw to muzzle, brow lowers, weight shift |
| `reach_start` | ~0.6s (14f) | no | move chosen | anticipation pull-back before the reach |
| `reach_move` | ~0.8s (20f) | no | after reach_start | arm travels out over the board; paw aligned in code to the source square (procedural target) |
| `reach_release` | ~0.6s (14f) | no | crab arrives | paw press sets the crab, then arm retracts to table |
| `win` | ~2.5s (60f) | no | Bear wins round (player loses) | slow satisfied nod, paws spread, ears perk |
| `lose` | ~2.5s (60f) | no | Bear loses round (player wins) | shoulders sag, head drops, long belly exhale, paw over eyes |
| `draft_card` | ~1.5s (36f) | no | modifier draft screen | head tilt + paw gesture toward the offered modifier |

The reach is a **generic authored arm motion**; the three.js side positions the paw/target over the actual chosen square so one clip serves any move (authored personality + procedural aim).

## Crab Token Clip Set (shared red/blue rig)

Parent crab parts (body → claws, eye-stalks, legs) so they can articulate.

| Clip | Length | Loop | Trigger | Notes |
|------|--------|------|---------|-------|
| `slide` | ~0.5s (12f) | yes | token moving along a path | legs paddle + body leans into travel; code tweens world position, clip adds life |
| `hop_settle` | ~0.4s (10f) | no | token arrives on a square | small hop + squash landing |
| `threat_wiggle` | ~0.8s (20f) | yes | token is part of a 3-in-a-row threat | claws raise, eye-stalks waggle (a "tell") |
| `win_pulse` | ~1.0s (24f) | yes | tokens on the winning line | rhythmic glow/scale pulse |

## Performance Director (three.js, `src/main.js`)

A small module holding an `AnimationMixer` per avatar and per crab, plus an event→clip mapping. It subscribes to existing game events (or is called from the existing move/turn handlers):

- `onAITurnStart()` → Bear `think` (loop).
- `onAIMoveChosen(from, to, path)` → sequence: Bear `reach_start` → `reach_move` (paw target = world pos above `from`) → grab → crab `slide` while tweening token along `path` → on arrival: Bear `reach_release` + crab `hop_settle` → Bear back to `idle`.
- `onPlayerSelectCrab(crab)` → highlight; `threat_wiggle` if the crab is part of a threat.
- `onPlayerMove(from, to, path)` → crab `slide` along `path` → crab `hop_settle`.
- `onThreatFormed(crabs)` → each crab `threat_wiggle` (loop) until resolved.
- `onRoundEnd(playerWon, winningLine)` → Bear `playerWon ? 'lose' : 'win'`; winning-line crabs `win_pulse`.
- `onDraftScreen()` → Bear `draft_card`.

The director sequences one-shot clips by listening for `mixer` `finished` events (or clip-duration timers) and is the single place that owns "what is the table doing right now."

## Pipeline & Reproducibility

1. **Author live over Blender MCP** (user watches the viewport): build the Bear rig, keyframe each action, build the crab rig + actions.
2. **Capture as code:** every rig/animation step is encoded as deterministic `bpy` functions added to `tools/blender/generate_assets.py` (e.g. `rig_bear()`, `anim_bear_idle()`, `rig_crab()`, `anim_crab_slide()`), so `npm run assets:blender` regenerates the animated GLBs deterministically and headlessly. **Live MCP edits must not be the only copy.**
3. **Export:** save `.blend` to `assets/blender/source/`; export `.glb` to `public/models/` with `export_animation_mode='ACTIONS'` so every action becomes a separately-named glTF clip. Stash actions on NLA tracks where needed so the exporter emits them all.
4. **Load:** `src/main.js` reads `gltf.animations`, builds mixers, and indexes clips by name for the director.
5. **Verify:** `npm run build` + `npm run verify:3d` (POV render screenshot) + a manual full-round playthrough.

## File Touchpoints

- `tools/blender/generate_assets.py` — add rig + animation authoring; switch export to `export_animation_mode='ACTIONS'`.
- `public/models/avatar-bear.glb`, `crab-red.glb`, `crab-blue.glb` — regenerated with clips.
- `assets/blender/source/*.blend` — regenerated sources.
- `src/main.js` — POV-as-default camera; AnimationMixers; performance director.
- (read-only) `crabcheckers/rules.js`, `src/ai.js` — to find the right hook points for turn/move events.

## Success Criteria / Acceptance

- [ ] Sit in POV and play a full round vs Bear without leaving the seat.
- [ ] Bear visibly: idles (breathing), `think`s during AI search, `reach`es and moves a crab, reacts with `win`/`lose`.
- [ ] Crabs `slide` along their path and `hop_settle` on arrival; winning line `win_pulse`s.
- [ ] `avatar-bear.glb` imports with named clips (no scale surprises, Y-up).
- [ ] `npm run assets:blender` reproduces the animated GLBs headlessly (no manual-only steps).
- [ ] `npm run verify:3d` passes; web-smooth framerate.

## Risks / Open Questions

- **Reach aiming:** generic clip + procedural paw target should cover all squares; if the paw visibly misses, fall back to a short code-driven IK blend on the forearm/paw only.
- **Blender 5.1 glTF exporter:** confirm `export_animation_mode='ACTIONS'` flag name/behavior on this version during the first export; adjust if the API differs.
- **Event hooks:** confirm `src/main.js` exposes (or can cheaply expose) the turn/move/round/draft events the director needs.
- **Grab handoff:** simplest is to re-parent the crab to the paw during reach, or just time the token tween to the paw; pick whichever reads cleaner in POV.

## MCP Setup (precondition for build)

Blender 5.1.1, `uv`/`uvx`, and the `claude` CLI are all installed. Before the build phase the user will: install the `blender-mcp` addon in Blender, start its socket (BlenderMCP sidebar tab), run `claude mcp add blender -- uvx blender-mcp`, and restart Claude Code so the MCP tools load. Exact steps provided separately after this spec is approved.
