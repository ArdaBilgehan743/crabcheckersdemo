# Crab Checkers — Cinematic Atmosphere Pass ("Liar's Bar" feel, pass 1)

- **Date:** 2026-05-30
- **Status:** Approved (design); implementing
- **Goal:** Push the POV look toward *Liar's Bar*: dramatic single-lamp chiaroscuro, haze, and a film-grade post stack — the fastest, highest-ROI step toward that feel.
- **Owner files:** `src/main.js`, new `src/postfx.js`

## North Star

When you sit in the POV seat, the room should feel like a dim, smoky back-room table: one warm lamp carving light out of near-black, the Bear lit dramatically across the table, haze in the light, grain and vignette pulling you in. Moody — but the board stays readable enough to play.

## Scope

**In:** lighting rebuild, fake volumetric haze + dust, a post-processing stack (bloom, depth-of-field, vignette, film grain, chromatic aberration, color grade), desktop/mobile quality tiers, a whisper of handheld camera sway.

**Out (later passes):** PBR textures/materials, character acting/eye-contact, audio/juice, camera push-ins & reaction cuts, gameplay changes, new Blender assets.

## Design

### 1. Lighting rebuild (`setupLights`, `createRoom`)
- Lamp = dominant warm key (raise intensity/contrast, warm color); crush `AmbientLight` so the room falls to near-black; faint cool rim/back light for character separation; soften + enlarge shadow penumbra.
- A dedicated soft fill aimed at the board keeps POV **playable** (mood dark, board legible).
- Tighten fog so the room fades to black sooner.

### 2. Volumetric haze + dust (high tier only)
- Additive, soft "light shaft" cone mesh under the lampshade (fake god-ray), plus a few slow drifting dust-mote sprites near the lamp. Cheap; reads like volumetrics.

### 3. Post-processing (`src/postfx.js`)
- Implemented with **three's built-in `three/addons/postprocessing/*`** (EffectComposer + passes) — guaranteed compatible with the installed `three` (^0.181, bleeding-edge) and **adds no new dependency**. (This swaps the earlier pmndrs suggestion purely to avoid version-compat risk on a very new three; the effect stack is unchanged.)
- Pass order: `RenderPass` → `BokehPass` (DoF, high tier only) → `UnrealBloomPass` (bulb/highlights glow) → custom **Grade `ShaderPass`** (chromatic aberration + warm/teal color grade + vignette + animated film grain in one fullscreen shader) → `OutputPass` (ACES tone map + sRGB).
- High tier uses a 4× multisampled render target; low tier none.
- Grade shader outputs `alpha = 1.0` (protects `verify:3d`'s transparent-pixel check).

### 4. Quality tiers (`detectQuality`)
- Heuristic: small screen / coarse pointer / low `maxTextureSize` → **low**, else **high**.
- **High:** full stack incl. DoF + haze + MSAA.
- **Low:** bloom + grade(vignette/grain) only; no DoF, no haze, lower bloom resolution.
- Exposed as a forced override (so the desktop showcase can be confirmed and a low-end user can downgrade).

### 5. Camera life (`updateCamera`)
- Subtle handheld sway: low-amplitude time-based noise added to the POV camera position/target. Tactical/table/rival views get little or none. (Push-ins/reaction cuts deferred to the camera pass.)

### 6. Integration
- `main.js` builds the post chain after renderer/scene/camera, renders via `composer.render(dt)` with a try/guarded fallback to `renderer.render(scene, camera)` if composer init fails.
- `onResize` resizes composer + bloom/bokeh + grade resolution uniform.
- `animate()` advances the grain time uniform and the DoF focus toward the board.

## Success Criteria
- [ ] POV reads dramatically moodier (dark room, glowing lamp, haze, grain, vignette, graded) while the board stays clickable/readable.
- [ ] `npm run verify:3d` still passes on desktop **and** mobile (no console errors, canvas not flat, no transparent pixels).
- [ ] Desktop runs the full stack; mobile auto-drops DoF/haze and stays smooth.
- [ ] No gameplay/animation regressions; before/after POV screenshots captured.

## Risks
- **three 0.181 + addons:** built-in addons are version-matched, so low risk; if any pass API shifted, adjust imports.
- **verify:3d transparent-pixel assertion:** ensure final alpha = 1 (grade shader + opaque clear).
- **DoF tuning:** focus distance must track the board center, aperture subtle, or the board blurs.
- **Mobile perf:** gate DoF/haze/MSAA behind the high tier.
- **Bloom blowing out the warm scene:** use a threshold so only the bulb/bright highlights bloom.
