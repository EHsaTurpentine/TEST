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

## v7.1 wave rename — real historical checkpoints

Renamed the five waves to real years, matched 1:1 to the five backgrounds:
`15,000 YEARS AGO`, `1066 A.D.`, `1492 A.D.`, `1776 A.D.`, `1863 A.D.`. This
sets up v7's plan (new Firefly backgrounds depicting the *same* river
valley at each of these points, showing environmental impact accumulating
over time) — the player should recognize it's one place across a long
span, not five unrelated locations.

**Cut from 6 waves to 5, folding the cut wave's difficulty into the
final one.** The game previously had 6 waves but only 5 backgrounds, so
wave 6 quietly looped back to wave 1's art — fine when backgrounds were
decorative, but incompatible with a real forward-moving timeline (going
from 1863 back to 15,000 years ago on wave 6 makes no sense). The user
had 5 real dates, one per background, so wave 6 (`THE LAST RUN`) was cut
outright rather than inventing a 6th date. Its difficulty wasn't just
dropped: the new final wave (1863) keeps 1863's own `poolR:262` (the
"channel diverted by mining" narrowing — thematically the right visual
for the last, most industrialized wave anyway) but takes wave 6's harder
`h`/`jitter`/`minerFirst`/`gap` values and a species-weight blend of the
two, so the endgame doesn't get easier just because a wave disappeared.

Three other spots referenced the old 6-wave assumption directly and
needed updating alongside the `WAVES` array itself (most of the
wave-scaling code already read `WAVES.length` dynamically and needed no
change):
- `scheduleVinegar()`'s candidate wave list (`[3,4,5,6]` → `[3,4,5]`) and
  fallback clamp.
- The final-wave tally message, which hardcoded the old wave name
  ("ENTER — THE LAST RUN IS DONE") — now name-agnostic ("...THE FINAL RUN
  IS DONE") so it doesn't reference a wave name that no longer exists.
- A comment documenting the miss-chance curve's endpoint, which named
  "wave 6" explicitly even though the code itself already scaled off
  `WAVES.length`.

Verified via Playwright: all 5 wave-intro cards show the correct
year/name in order, and the final-wave tally screen no longer mentions
"THE LAST RUN".

## v7.1 enemy pier cleanup

User feedback: "the enemy platform/fishing ladder... looks bad in
comparison to the main sprite." Three real, distinct problems, not one:

**Leftover background-removal artifacts.** `miner_pier.png`'s original
extraction (from a small, low-detail reference photo -- nowhere near the
tower reference's production value) left three thin strips of the
source's sky-blue background still opaque: two 1-2px horizontal streaks
sticking out to the left at the plank/post joint, and an isolated 1px
line further down. Confirmed by color (uniform sky-blue, not wood) and
by connectivity (no gradient into the wood -- a flood-fill boundary
artifact, not intentional shading). Cleared by zeroing alpha along each
streak from the image edge inward, stopping at the wood outline, rather
than a blanket color-key (the legitimate base splash uses similar blues,
so a global mask would have eaten it too).

**Miner floating above the plank -- wrong anchor point.** `anchorX/
anchorY` (the point in `miner_pier.png` that lands at `WATER_Y`, matching
where `drawMinerSkin()`/`drawMinerSprite()` plant a miner's feet) was
`(61, 23)` -- 23 is near the TOP of the post, nowhere near the plank at
all. Re-measured empirically against a live-spawned miner (not just read
off the PNG's alpha channel, which pointed at the plank's far/back edge,
not the near corner a character actually stands on) -- `anchorY=68` lands
the feet flush on the plank surface. Verified across multiple `rock`-type
skins (targetH differs per skin but the render is always bottom-anchored
at `WATER_Y`, so all align identically) and multiple random per-wave
`pierRot` tilts.

**Miner spawning at the pier's OLD fixed position -- a real regression
from the per-wave pier randomization added earlier.** `spawnMiner()`/
`spawnVinegarMiner()`'s `tx` (stand point) and initial `x` (walk-in start)
were fixed absolute values (`rnd(356,392)`, `x:404`, etc.), tuned around
the pier's old constant x≈370. Once `startWave()` started rolling a
random `G.pierCx` per wave, nothing carried that roll to the miners --
they'd walk to the OLD fixed spot regardless of where that wave's pier
actually rendered, reading as standing on nothing on any wave whose roll
moved the pier away from ~370. Same bug also lived in `updateMiners()`'s
`state==='gone'` re-entry (`m.x=404` again) and in `maybeSpawnVinegar()`/
`startWave()`'s `G.wave===6` checks, both dead since the 5-wave cut above
(silently disabled the GDD §7.1 second-vinegar-miner stretch feature) --
switched to `G.wave===WAVES.length`. All four spots now compute relative
to `G.pierCx`, with the same spread as before, so a miner always tracks
wherever that wave's pier actually rolled.

**What wasn't changed, and why.** Considered rebuilding the plank+post
crop entirely from a fresh crop of `player_tower.png` (to close the
remaining production-value gap with the tower/legs, which already reuse
that source) rather than just cleaning up the existing crop. Every
candidate region tried (both the left and right corner posts) had its own
uncleaned background residue outside the area the original tower
extraction actually needed for gameplay -- background removal there would
be a real re-do of that original extraction pass, not a quick reuse, and
tangled with a rope-net pattern that a naive flood-fill damages (tolerant
enough to clear the residual sky pulls blue-shaded net cells with it too).
Deferred rather than rushed; the cleanup above fixes the concrete defects
(artifacts, floating miner, wrong-position miner) without that larger
asset-extraction risk. A `jumper`-type miner (the rival-angler, which
never gets a skin -- see `spawnMiner()`'s own comment) still floats above
the pier in the same way the skinned miners used to: it renders through a
completely separate legacy sprite-atlas path (`drawMinerSprite`,
`SPR_MINER_DATA.minerAtlas.feetCentre`) that predates this session and
wasn't touched here -- flagged, not fixed, since it's a pre-existing
miner-sprite calibration issue rather than anything about the pier
itself.

## v7.2 art refresh — Firefly-generated skins and pier

User supplied a new batch of art (`TRANSPARENT_SPRITES_CLAIMJUMPER.zip`,
generated in Firefly): standalone rockthrower/prospector, an archer and a
soldier each composited standing on a plank, and the plank/a small
netted mini-tower on their own. Getting the actual files took several
rounds -- inline pasted images in chat never landed on disk this session
(checked `/root/.claude/uploads/`, confirmed empty after two attempts,
including a re-attach); only a real zip upload worked. Noted since it'll
recur: **pasted chat images ≠ file access, even when the tool literally
sees them** -- ask for a zip/file upload if real pixel access is needed.

**Firefly's "transparent background" is a picture of a checkerboard, not
real alpha.** All 6 source PNGs loaded as flat RGB (`img.mode == 'RGB'`),
with an actual rendered checkerboard pattern as pixel content standing in
for transparency -- not a filename or convention issue, a real gap
between what Firefly exports and what "transparent PNG" means. This is
exactly the same category of problem as the original tower/pier
extraction earlier in this project (real photos with real backgrounds),
just from an AI generator instead of a camera. Converted locally:
classified any pixel as background if it's both low-saturation
(`max(r,g,b)-min(r,g,b) <= 8`) and bright (`min(r,g,b) >= 220`) --
matching the checker's actual measured tones (~232/~251, always
near-neutral gray) -- applied as a **direct per-pixel test, not a
border-seeded flood fill**. Flood-fill was tried first and looked like it
was eating real content (the bow's open interior, the gap between the
archer's legs went solid white instead of checkered); turned out those
really were background pixels, just in pockets fully enclosed by the
character's own silhouette (inside the bow, between the legs) that a
border-only flood fill can never reach. The direct per-pixel classifier
handles enclosed pockets and border-connected background identically,
and is simpler.

That classifier alone still left ~10,000 scattered single-pixel specks
per image (a faint texture/gradient in Firefly's "checkerboard" that
occasionally fell just outside the tolerance) -- cleaned with a
connected-component pass (`scipy.ndimage.label`), dropping any opaque
blob under ~250px. Below that size the dropped components were
confirmed to be noise, not small legitimate details (verified visually
per-image after filtering, not just by pixel count).

**Asset mapping** (worth recording since the source zip's filenames are
just Firefly's own prompt text, not descriptive of role):
- `rockthrower.png`, `prospector.png` — direct swaps, standalone
  character art, no code changes needed (tight bbox crop already matches
  `drawMinerSkin()`'s bottom-anchor-at-`WATER_Y` convention).
- `archer.png` — swapped for a *different* generation than the
  plank-composited one the user first showed inline (an
  "eliminate everything except the character" variant), since it's
  already standalone and needed no cropping-out step.
- `soldier.png` — no standalone version existed (only ever shown
  composited on the plank), so cropped the character out of that
  composite (row-boundary scan to find where the wide plank begins,
  plus a small manual patch for one stray post fragment poking into the
  crop, then a connected-components pass keeping only the character's
  own blob).
- New `miner_pier.png` — the plank piece from the structures-only image,
  replacing the old reference-photo crop. Re-measured anchorX/anchorY
  the same empirical way as the earlier fix (against a live-spawned
  miner, not just the alpha channel): anchorX=100, anchorY=64, scale=0.21.
  `miner_pier_legs.png` (reused tower-netting) is unchanged underneath it,
  just re-pointed at the new plank's front-post exit point
  (postBottomX=90, postBottomY=233).
- The mini-tower piece and the player-on-tower/soldier-on-plank preview
  composite were **not** used -- decided against introducing a second
  "which structure does this skin get" branch (some miners have their
  own baked-in plank, multiple miners can be on screen at once with
  different skins, only one shared pier position exists) in favor of one
  simple rule: all four skins are character-only art standing on the one
  shared, now much higher-quality, pier. Simpler and lower-risk than
  per-skin structure branching, and the visual result is close to
  equivalent.

Known minor imperfection, not fixed: the soldier's headlamp glow effect
lost some of its soft falloff to the background-removal pass (reads a
little blocky up close) since the glow's own soft edge legitimately
overlapped the checker's tolerance band. Left as is -- cosmetic only,
not worth the risk of a more aggressive touch-up damaging something else
this late in the pass.

Verified via Playwright: all four skins standing on the new pier with no
float gap, two miners with different skins on screen simultaneously
(spread across the real `spawnMiner()` tx range) both land correctly on
the plank, title screen and wave-intro unaffected, no console errors.

## v7.2 follow-up: player tower, pier "second tower", rockthrower facing

User feedback after playing the art-refresh live: the player's own
tower was still the OLD concept-art image (visible snow/mountain
ghosting and the earlier ghost-feet crop notch), the enemy pier's
reused tower-netting-legs read as a confusing second "fishing tower" on
the right side of the screen, and rockthrower was throwing away from
the player instead of at them.

**Player tower swapped to the Firefly mini-tower** (the structures-only
piece extracted alongside the pier plank, previously unused). Same
"stretch to fit the wave's platform height" mechanism in `drawPlatform()`
as before, just re-anchored: `anchorX=220, anchorY=142` (the new art's
deck surface, measured the same empirical way as the pier fixes).
Verified against a live-spawned player figure at wave 1 and wave 5 (the
two height extremes) -- feet land flush on the deck at both.

**Dropped the reused tower-leg crop under the enemy pier entirely**
(`miner_pier_legs.png`, deleted). It was cropped from the OLD tower art
now being retired, and its whole visual point (bulk up the plank so it
"looks more like the fishing tower," from much earlier feedback) is
exactly what read as wrong once there's a real, better-quality tower
back on the player's side -- two tower-style structures on screen reads
as two towers, not one tower plus a dock. The plank alone carries the
new art's own weight fine without it.

**Rockthrower was throwing right; miners must face left** (toward the
player, who's always on the tower at the left). Checked all four skins
individually against the source art: archer, prospector, and soldier
all already aimed/reached left, only rockthrower was mirrored wrong.
Fixed by flipping `rockthrower.png` itself horizontally (`PIL`
`FLIP_LEFT_RIGHT`) rather than adding per-skin mirroring logic to
`drawMinerSkin()` -- simpler, and consistent with how every other skin
is just drawn as-is with no code-level flip.

**Also caught and fixed a real transparency-conversion defect while
re-examining the new tower art closely**: the net's mesh holes had a
faint white haze instead of showing clean through-transparency (visible
zoomed in, easy to miss at normal scale) -- the checkerboard classifier's
brightness floor (`min(r,g,b) >= 220`) was too strict for pixels near a
soft shadow/gradient inside small enclosed net cells, leaving them
narrowly misclassified as real content. Loosened to `tol<=12, min>=190`
and reprocessed just the structures image (the only one with fine mesh
detail at that scale); re-checked the character skins against the same
issue and found them unaffected (their large solid-color regions don't
have the same boundary-precision problem). Re-verified with a bright
non-white checker composite (pink/cyan, not the misleading white the
Read tool defaults to) before and after.

**Found, not fixed**: at wave 5 (the tallest platform, `obsY=15`,
close to the very top of the canvas), the player figure renders mostly
or entirely above the visible canvas top edge. Confirmed via git history
that this happens identically with the OLD tower art too -- it's a
pre-existing framing issue unrelated to today's art swap (the player
figure's position is computed independently of which tower image is
used), not a regression. Flagged for a future pass rather than fixed
here, since it's out of scope for an art-consistency request and would
need its own investigation (cap wave height, shift the camera, or resize
the canvas).
