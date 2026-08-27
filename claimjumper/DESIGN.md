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
platform who throw rocks (or dive in as a "jumper" variant) at the player;
getting hit costs a life. A separate **vinegar-miner** — scheduled to
appear on one of waves 3–6 — throws a vinegar bottle instead, a distinct
hazard from the plain rock hit.

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

## Open next steps (not yet done)

- **v7's skin system**: `v7_GDD.md` describes adding Rock-Thrower/Archer/
  Prospector as three interchangeable skins on the rock-spawn behavior
  (currently one generic miner look) and Miner/Soldier as the vinegar-
  spawn skin, wave-gated per its §1.2 table, plus Archer's distinct
  flatter/faster throw arc. The four character-skin PNGs and five level-
  background PNGs already sourced for this sit in `claimjumper/assets/`,
  unused by the game so far — that's a separate, larger change from the
  loop-swap done here and hasn't been started.
- `qr.png` for the end panel, if wanted.
