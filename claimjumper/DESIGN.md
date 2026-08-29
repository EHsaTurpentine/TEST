# CLAIMJUMPER — design notes

## Correction

An earlier version of this file described a Donkey-Kong-style climbing
game, built on nothing but the `v7_GDD.md` addendum (which only lists
deltas and assumes a base game already exists) after the real v1–v6 code
was believed lost. That guess was wrong — the real `claimjumper_6.html`
browser build later turned up and is now `claimjumper/index.html`. This
file replaces the incorrect one with what the real game actually is.

## What CLAIMJUMPER actually is

A single-screen spearfishing arcade game. The player stands on a river
platform/trestle, aims a spear with the mouse (arrow keys/A-D as a
fallback), holds Space or clicks to charge a throw, and releases to spear
fish swimming past for points. Six waves (`WAVES` array), each harder than
the last. 3 lives, 3 credits (continues), streak bonuses, a session-wide
species/catch trophy row, title/wave-intro/tally/continue/end screens.

**Miners** are the hazard, not the goal: rival claim-jumpers posted on the
platform who throw rocks at the player (getting hit costs a life), or —
the separate "jumper" (rival-angler) variant — just steal a fish instead
of throwing anything. A distinct **vinegar-miner**, scheduled to appear on
one of waves 3–6, throws a vinegar bottle instead of a rock.

A **progressive spear-buff system** (`BUFFS`/`BUFF_PRIORITY`/`hasBuff`) is
fully implemented in the code but deliberately disabled at the source
(`G.buffsAvail` is never populated, so every buff branch falls through to
its unbuffed default) — this is the "dormant buff-drop system" the v7 doc
lists as out of scope, not a bug.

Art is mostly real sprites embedded as base64 (`SPR_DATA` /
`SPR_MINER_DATA` / etc.: player figure, miner, spear, fish, sky/pool/
scene/deck/trestle backgrounds) with vector-drawn fallbacks if a sprite
fails to decode. The one asset not embedded, `claimjumper-images/qr.png`
(shown on the end-credits panel), isn't in this repo — the game already
degrades gracefully to "QR UNAVAILABLE" without it.

## What's actually wired to `engine/` so far

Only the fixed-timestep game loop. The original hand-rolled accumulator
(`let lastT=...; acc=...; function frame(now){...}; requestAnimationFrame`)
is replaced with `engine/core/loop.js`'s `GameLoop`, configured with the
exact same 30Hz step and 6-updates-per-frame cap the original used
(`STEP_MS=1000/30`, `iter<6`) — a drop-in swap, not a rewrite. Everything
else (input handling, physics, rendering, the `G.mode` string state
machine, audio) is untouched.

This was a deliberately narrow, low-risk first pass: this file is a large
(2300-line), carefully tuned, already-working game — full of comments
documenting specific bugs found and fixed (e.g. a mouse-vs-keyboard aim
race) and deliberately-chosen constants (e.g. `MOVE_SPEED = 1.6 // was
1.1 -- snappier dodge`). Rewriting its input handling or state machine
onto `engine/Input`/`engine/StateMachine` for architectural purity risked
regressing behavior that's already right, for no functional gain — so
that wasn't done.

## v7's skin system (implemented)

Rock-spawn miners (`type==='rock'`) now get a `skin` field chosen from a
wave-gated pool (`rockSkinPool()`, v7 §1.2 verbatim: waves 1–2
Rock-Thrower only, 3–4 add Archer, 5–6 add Prospector); vinegar-spawn
miners always get `skin:'soldier'`. The `'jumper'` (rival-angler) miner
stays unskinned and untouched, per v7 §4.

- `drawMiner`/`drawVinegarMiner` check `SKINS[m.skin]` first and draw the
  flat PNG (`drawMinerSkin`) in place of the sprite-sheet body when it's
  loaded, falling back to the existing rendering unchanged otherwise —
  same "never hard-fail on an asset problem" pattern the file already
  uses elsewhere. These are single static throwing-pose illustrations,
  not a walk-cycle sheet, so a skinned miner holds the same pose through
  walk/stand/wind rather than animating — a deliberate simplification
  given the assets on hand, not a bug.
- `throwRock` branches on `m.skin==='archer'` for a shorter, lower-gravity
  arc (flatter/faster per v7 §1.3); Rock-Thrower and Prospector share the
  original arc unchanged (Prospector is a plain rock-hit equivalent per
  §1.4). Verified directly: same target, archer's throw comes out faster
  and with less vertical drop than rockthrower/prospector, which are
  identical to each other.
- Thrown-object color is tagged by skin too (gray rock / pale streak for
  archer / gold for prospector's gem) so the different arcs read clearly
  in flight, not just in the arc math.
- Verified with Playwright: skin pool per wave matches the table exactly,
  archer's arc is measurably faster/flatter than rockthrower's (confirmed
  identical to prospector's), and all four skins render at a sane size,
  correctly oriented toward the player, with no console errors.

Images are loaded from `claimjumper/assets/` (already sourced, described
above) independently of the base `SPR` sprite pipeline, so a missing skin
file degrades to the original generic miner rather than breaking anything.

## Level backgrounds (now wired in)

The five level-background stills are used as the WAVE INTRO card's
backdrop, one per wave (cycling: wave 1 = Mountain Vista, 2 = Rocky Cliff,
3 = Esmeralda, 4 = Pine Grove, 5 = Junction Bar, 6 wraps back to Mountain
Vista) via `waveBackdrop()`, replacing `drawWaveIntro()`'s call to
`drawSky()` when a backdrop is loaded.

They are deliberately **not** used as the live `PLAY` scene's background.
`PLAY`'s water, bank, platform, and miners are all laid out against
`drawSky()`'s single scene image at exact pixel coordinates (`WATER_Y`,
`BANK_X`, etc.) — swapping that image per wave would misalign everything
drawn on top of it. `drawSky()` itself is untouched; `PLAY` looks exactly
as it did before. `WAVEINTRO` is just centered text over a full-bleed
backdrop, so it was the safe place to actually show this art.

Verified with Playwright: each wave (1-5, and 6 wrapping to 1's image)
shows a distinct real background on its intro card, and the live PLAY
screen's scene art is byte-for-byte the same as before this change.

## Player figure and tower (real reference art)

The user supplied original concept art (predating this whole build) showing
the intended player design: a spearfisher on a wooden fishing tower with
diamond-net siding, throwing a trident. `claimjumper/assets/player_tower.png`
and `player_character.png` are cut from it (background removed via a local
flood-fill script, since this session's sandbox can't reach Adobe's
background-removal API — no story here beyond "no network path", the cutout
quality is the same either way) and wired into `drawPlatform()`/`drawFigure()`
ahead of the existing sprite/vector fallbacks, same "degrade gracefully if
an asset never loads" pattern as everywhere else in this file.

**Tower**: a straight asset swap. `drawPlatform()` stretches it vertically
only, anchored at the player's foot point, so its base reaches the water
regardless of the current wave's platform height — mirrors the old
tiled-trestle approach's goal (fit any wave height) with one image instead
of a repeated bay unit.

**Character — superseded, see below.** The single-pose cutout described in
the original version of this section (`player_character.png`, dampened
whole-body rotation to approximate aim angle) has been replaced. It's kept
here in git history only; the file itself was deleted once the real
angle-bucket set arrived.

## Player figure — six-pose angle-bucket set (real fix, not the workaround)

The user followed up with `MAIN_SPRITE_WITH_SPEAR.zip`: six purpose-made,
pre-cut (already transparent, no extraction needed) poses spanning the
aim range — `figure_up_soft`, `figure_level`, `figure_down_soft`,
`figure_down_mid`, `figure_down_hard`, `figure_down_steep` — a real
equivalent to the old `SPR.figImg` aim-bucket sprite sheet, replacing the
dampened-rotation approximation entirely.

`PLAYER_FIG_SPECS` assigns each pose an angle evenly spread across the
game's actual 8–88° range in the set's naming order (8, 24, 40, 56, 72,
88) rather than back-measuring the art's rendered angle, which proved too
imprecise to trust from pixel inspection alone. Each pose has its own
`anchorX`/`anchorY` (measured per-file — the six images aren't cropped to
a shared coordinate system, so a single shared anchor would have
misaligned several of them) marking its planted-foot point.
`nearestPlayerFigBucket(angle)` picks the closest pose each frame, same
snapping idea as the old `nearestFigBucket`.

The weapon is baked into each pose (same as before), so the `drawPlay()`
spear-suppression checks now key off `PLAYER_FIG_BUCKETS.length > 0`
instead of the old single-image check.

Verified with Playwright at all six bucket angles plus an in-between
angle (confirming snapping), and across idle/moving/charging/flight/
recovering states: feet stay planted on the platform at every angle, pose
progression from shallow to steep reads naturally, exactly one weapon
visible in every state, no console errors.

## Miners' spawn pier (real reference art)

The user also supplied a small reference image of the miners' pier — a
wooden post-and-plank they stand on/spawn from. Extracted the same way as
the player/tower art (local flood-fill, connected-component cleanup) into
`claimjumper/assets/miner_pier.png`, and wired into `drawMinerPier()` ahead
of the old procedural plank-and-legs, same graceful-fallback pattern.

This one's a straight swap with no angle/animation complications — the
pier is purely decorative (per the file's own existing comment, "drawn
every frame regardless of whether a miner is present"), so it's just
anchored at the plank's near top corner and centered on the same x the old
procedural pier occupied. Verified with a real miner standing on it: feet
land cleanly on the plank, no positioning mismatch, no console errors.

## Polish round: alignment, visibility, and per-wave scenes

A round of feedback after playing the art integrations live, addressed
together:

**Tower ghost-feet fix.** `player_tower.png`'s original character-erasure
box (from the very first extraction pass) cut off a few pixels short of
the actual feet, leaving two small skin-toned fragments sitting on the
platform surface — visible as stray feet from "someone" who wasn't there.
Found by cropping and checkering the exact region, erased directly, and
the asset re-verified clean end to end.

**Spear-to-reticle alignment.** `PLAYER_FIG_SPECS` now also carries
`renderAngle` — each pose's own actual baked-in throw angle (roughly hand-
to-tip, measured by inspection), separate from `angle` (the assigned
bucket-selection label spread across 8-88). The six poses' real angles
only span about -14 to +26 degrees regardless of bucket, well short of
the game's range, so at extreme aim the weapon barely visually moves while
the reticle sweeps the full 80 degrees. `drawFigure()` now applies a small
corrective rotation — `target angle - bucket.renderAngle`, capped at
±20° — around the same planted-foot pivot already used for the six-bucket
system. The cap matters: an *uncapped* rotation is exactly the
single-pose-plus-rotation approach two commits back that read as the
character collapsing forward: ±20° is comfortably inside the ±15° that
was already confirmed clean, only reached at the largest realistic
residuals.

**Reticle redesign.** The old aim mark was a plain 6px gold X with no
outline — invisible against anything gold or light. `drawReticle()`
(new, by `drawSpear()`) draws a ring + four outward ticks in two passes —
a dark halo then bright gold, the same two-pass idiom `haloText()` already
uses for on-screen text — so it reads against sky, water, and rock alike.

**Pier bulk-up.** The pier reference photo only showed a bare post, which
read as much thinner than the tower even after scaling. Rather than
invent structure that isn't in the source, cropped a net-braced leg
section directly from `player_tower.png` (`miner_pier_legs.png`) and draw
it under the post, continuing it down toward the water — guaranteed
visual-family match since it's literally the same source art, not just a
similar style.

**Backgrounds are now the live `PLAY` scene, not just `WAVEINTRO`.**
Reverses the caveat two sections up. `drawSky()` now checks
`waveBackdrop()` before `SPR.sceneImg`, and since `drawPlay()` already
calls `drawSky()` first, this was the entire change needed to make each
wave's background the actual playing field — `drawWater()`'s existing
"scene backdrop already painted this region" skip (previously keyed only
off `SPR.sceneImg`) now also recognizes `waveBackdrop()`, and
`drawCanyonWalls()`'s corner rock-accent (shaped for the *original*
scene's specific composition) is skipped when a wave backdrop is active,
since it would just sit as a mismatched wedge over a different photo.
Checked the water-line position in all five background images against
`WATER_Y` first — all close enough that fish/miners/platform/tower still
read as grounded in the new water. Verified: waves 2 and 4 render visibly
distinct real backgrounds during actual `PLAY`, not just their intro
cards.

**Per-wave tower/pier position + tilt.** `startWave()` now rolls
`G.towerCx`/`G.towerRot` (±8px / ±6°) and `G.pierCx`/`G.pierRot` (±15px /
±8°) once per wave. `drawPlatform()`/`drawMinerPier()` rotate around each
structure's own anchor point (the player's planted foot for the tower, the
plank's near corner for the pier) rather than the image's own center, so
the player/miner — drawn separately, deliberately *not* rotated — still
reads as standing on the tilted structure instead of floating off it.
Deliberately does not touch any actual gameplay coordinate (`OBS_X`,
`PLAYER_MIN`/`PLAYER_MAX`, the miners' spawn `tx` range) — only where the
art is drawn, so movement, spawning, and hit-detection are unaffected.
Verified via real wave progression (not just direct state edits): waves 1
and 2 land on genuinely different rolled positions/rotations, and a miner
placed on wave 2's repositioned pier still stands on it correctly.

## Remaining assets

`claimjumper-images/qr.png` (the end-panel QR code) is in place — decodes
to `https://ehsaturpentine.github.io/ENGINE/engineer/`. No open items left.

## v7.1 cleanup pass (post-park)

Two rough edges found while getting v6 ready for the next iteration:

**Leftover on-screen debug text.** The archer-skin-load diagnostic
(`SKINS R✓ A✗ P✓ S✓`, added to `drawTitle()` to read load state on a phone
with no devtools) was left in place after the bug was actually diagnosed
and fixed. Removed — it was explicitly marked `TEMPORARY` in a comment but
never cleaned up.

**Procedural bank fill breaking the photo illusion in later waves.**
`drawPlay()` called `drawBank()` (a flat `PAL.rockLt` rectangle, tuned for
the pre-backdrop procedural scene) in two places: once whenever
`G.w.poolR < 336` (only true for wave 5 `CHANNEL DIVERTED`, poolR 262, and
wave 6 `THE LAST RUN`, poolR 300 — every earlier wave holds poolR at 336),
and once unconditionally at the bottom of every wave. Both painted a solid
rock-colored patch directly over the photo backdrop. The earlier per-wave
verification pass never caught this because its Playwright script forced
synthetic wave state with `poolR:336` hardcoded for every wave it tested —
never exercising the real wave 5/6 data. All three sites (`drawBank`
before `drawWater`, `drawBank` after, and the horizon stroke line, which
was still gated on the old `SPR.sceneImg` flag instead of `waveBackdrop()`)
are now skipped whenever a wave backdrop is active. `G.w.poolR` still
narrows the fish-spawn/pool bounds for difficulty — only the visible fill
was removed. Verified via Playwright against the real `WAVES` table
entries for wave 5 and wave 6 (not synthetic overrides), plus a wave 1
re-check to confirm no regression from dropping the always-on bottom
strip.
