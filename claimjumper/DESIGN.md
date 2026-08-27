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

**Character**: not a straight swap, because the existing system needs to
show continuous aim angle (mouse-driven, core to the gameplay) and the new
reference is a single static throwing pose at one angle — the old system
handled this with discrete pre-rendered angle-bucket sprites, which this
new art doesn't have equivalents of. Tried rotating the whole cutout
rigidly around the planted foot point to track aim angle; at even a
modest ~37° delta from the art's own baked-in angle it read as the
character collapsing forward, not aiming (confirmed empirically via
screenshots, not just reasoned about — also ruled out canvas image-smoothing
blur as the cause before concluding it was the rotation itself). Landed on
a **dampened rotation** (`0.2×` the real angle delta) — enough for a subtle
lean toward the throw, verified clean at both ends of the actual 8-88°
aim range and at the default angle, without the collapsing-forward look.
The aim reticle already shown on screen carries the precise aim feedback;
this is a cosmetic assist, not the primary indicator.

The weapon is baked into the character art (same as the old sprite path),
so the separate procedural spear draw in `drawPlay()` is suppressed
whenever either sprite path is active — extended, not just reused, since
the old suppression check only looked at `SPR.figImg` and would have
double-drawn a spear in the (unlikely) case that loads but this new art
doesn't. Verified idle/moving/charging/flight/recovering states all render
with exactly one weapon visible, no console errors.

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

## Remaining assets

`claimjumper-images/qr.png` (the end-panel QR code) is in place — decodes
to `https://ehsaturpentine.github.io/ENGINE/engineer/`. No open items left.
