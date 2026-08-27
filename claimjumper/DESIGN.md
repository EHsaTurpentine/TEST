# CLAIMJUMPER — design notes (reconstructed baseline + v7)

The original v1–v6 GDDs were never committed and were lost when their chat
sessions ended. This file is a **from-scratch reconstruction** of the base
game (marked as such below) inferred from `CLAIMJUMPER_v7_GDD.md` — which is
only a decision-log addendum and assumes a base game already exists — plus
the delivered art. Treat anything below not cited to v7 as a judgment call,
open to correction.

Keeping this file up to date (instead of leaving the design only in chat) is
the actual fix for the "sessions keep timing out and we lose everything"
problem that started this whole effort.

## Premise (reconstructed)

A prospector climbs a claim site — ladders and platforms over a river
landscape — to plant a stake at the top before the site's defenders knock
them off. 5 stages, one per background: Mountain Vista → Rocky Cliff →
Esmeralda → Pine Grove → Junction Bar (`v7 §2`, all five now confirmed
distinct by hash).

## Core loop (reconstructed)

- Single-screen-per-stage vertical platformer (no camera scroll): solid
  platform rows connected by ladders, à la Donkey Kong.
- Player walks platforms, climbs ladders (vertical-only movement, gravity
  off, locked to the ladder's column while climbing).
- Defenders ("miners") are posted on platforms and periodically throw a
  projectile at the player. Getting hit costs a life and resets the player
  to the stage's bottom platform.
- Reaching the top platform clears the stage and advances to the next
  background; clearing stage 5 wins.
- 3 lives, shared across the run (matches `cutting_season.html`'s HUD
  convention for this engine-sharing family of games).

## Miners: skins and behavior (`v7 §1.1–§1.4`)

Two underlying spawn behaviors, four skins:

| Behavior | Skins | Projectile |
|---|---|---|
| rock-spawn | Rock-Thrower, Archer, Prospector | lobbed arc by default |
| vinegar-spawn | Miner/Soldier | thrown bottle, shatters into a brief ground hazard on landing |

- **Rock-Thrower / Prospector**: identical lobbed-arc projectile (gravity-
  affected, moderate speed). Prospector's gem/nugget is a reskin only —
  "behaves identically to a rock hit" (`v7 §1.4`).
- **Archer**: distinct flatter/faster throw-arc — less gravity drop, shorter
  flight time (`v7 §1.3`). Implemented as separate arc constants, not a
  reused rock trajectory.
- **Miner/Soldier (vinegar)**: thrown bottle arcs down and, on landing,
  leaves a puddle hazard that lingers briefly — distinguishing it from a
  plain projectile hit while still being "just a thrown item" mechanically.

## Wave-gated skin pool (`v7 §1.2`, verbatim)

Waves progress globally across the run (not per-stage), capped at 6:

- Waves 1–2: Rock-Thrower only.
- Waves 3–4: Rock-Thrower + Archer.
- Waves 5–6: Rock-Thrower + Archer + Prospector.
- Once introduced, a skin stays in the pool.
- Miner/Soldier's vinegar-spawn timing is scheduled independently and is
  unaffected by wave gating (`v7 §1.2`, last line).

## Explicitly out of scope (`v7 §4`, unchanged)

Rival-angler ("jumper") miner, the buff-drop system, and the willow-weir
mechanic are not implemented. The fishing-ladder net and the pier are
decorative only (`v7 §1.5–§1.6`) — drawn, not interactive.

## Engine usage

Built on `engine/` (`GameLoop`, `Input`, `StateMachine`, `TileMap`,
`moveAndCollide`) rather than reinventing loop/collision/input code inline,
per the point of building the shared engine in the first place.
