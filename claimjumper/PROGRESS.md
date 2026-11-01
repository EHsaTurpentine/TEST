# CLAIMJUMPER! Progress & Handoff

Nov 1, 2026. Living status doc for whoever/whatever picks up work on this
game next — written so a local model with a small context window, or a
human skimming cold, can get oriented without re-deriving any of this.

**Read this first if you're new here.** `DESIGN.md` has the full prose
history of every version (why each decision was made, what broke, what
got tried and discarded). This doc is the current-state summary and
practical reference — codebase map, asset inventory, open items. Treat
`DESIGN.md` as the archive and this as the dashboard.

## Where things actually stand

This is **not** an early-stage build. Every character has real
multi-frame animation (not a static pose), five custom backgrounds are
live, and the game is deployed and playable right now at
**https://ehsaturpentine.github.io/TEST/claimjumper/** (GitHub Pages,
auto-deploys on push to `main`).

If you're starting from an older handoff doc or an older `claimjumper_N.html`
file and it describes "no skin/pier/wave-gating/background work exists
yet" or "six waves, five backgrounds" — that's stale. Ignore its status
section; this one is current. (`index.html` in *this* repo is the only
one that matters — not a same-named file from a different chat/export.)

**Done:**
- Five miner skins (rockthrower, soldier, prospector, archer + the
  vinegar-throwing soldier variant), each wave-gated, each with real
  wind-up/release animation and a walk cycle, extracted from
  Firefly-generated video clips.
- The player has real wind-up/release/recovery animation layered onto
  the existing six-angle aim-bucket system (COCKED/FLIGHT/RECOVERING),
  not just a static held pose.
- Five wave backgrounds, one per level, matching a real timeline
  (15,000 years ago -> 1066 -> 1804 -> 1863 -> 1927 A.D.), each showing
  the same river valley's environmental decline.
- `index.html` was just split: it used to carry ~1.45MB of legacy sprite
  art inline as base64 (90% of the file). That's now out at
  `assets/sprites/*.png`; the file is 144KB of actual logic. This was
  done specifically so a local model can read it in one piece.
- Five waves (not six — this was already decided and fixed; don't
  reintroduce a sixth).

**Not done / open:**
- Background art quality — flagged by the user as "sloppy and jagged,"
  along with the character animation edges. This is the active ask.
  See "Immediate next step" below.
- See "Known compromises" below for specific, smaller rough edges.

## Immediate next step: background + character art quality pass

The user's own words: Firefly's output (both the backgrounds and the
character animations) reads as sloppy/jagged, and they want it dialed
in properly, starting with backgrounds. They're moving art generation
(and, per their direction, most code work) to their own 4090 via
Pinokio/Forge rather than continuing through Firefly or having Claude
write every change. **Confirm their checkpoint/model before writing new
prompts** — Forge/Stable-Diffusion prompting (weighted tags, negative
prompts) is a different language than Firefly's natural-language
paragraphs, and the right prompt shape depends on what's loaded (a
general photoreal checkpoint, an illustration-tuned one, a pixel-art
LoRA, SDXL vs. Flux, etc. all want different prompts for the same "clean
painterly game background" target).

`BACKGROUND_PROMPTS.md` and `ANIMATION_PROMPTS.md` are the existing
Firefly-targeted prompt sets — useful as *content* reference (what each
scene needs to contain, the lessons already learned about facing
direction/no-dock/no-baked-motion-trail/etc.) but will need reformatting
for whatever's actually loaded in Forge.

## Hardware

4090, confirmed (Remote Control lists a computer named `THE-4090`). That's
comfortably in the top tier of any local-model sizing guide: full-size
30B-class coder models (4-bit quantized) and Flux-class image models
both run fine. Not pinned down: system RAM, OS (the Remote Control folder
for that machine reports as unusable from a cloud session, consistent
with Windows — cloud sessions can only attach to Mac/Linux Remote
Control folders, so this repo's cloud sessions can't reach that machine
directly regardless of what's installed there).

## Division of labor going forward

Per direction: code and art generation move to the local GPU. Claude's
role from here is reviewing diffs, documenting state (this file,
`DESIGN.md`), and writing/refining prompts — not routine feature work,
unless asked.

| Job | Do it with |
| --- | --- |
| New/revised character and background art | Forge/ComfyUI on the 4090, via Pinokio |
| Game code changes | A local coder model, now that `index.html` is split and small enough for one |
| Reviewing a finished diff, unsticking a stuck local model | Claude, on request |
| Look-and-feel calls (does this read right in the actual browser) | The user |

## Codebase map (`claimjumper/index.html`, 2,930 lines, 144KB)

| Area | Line | What to know |
| --- | --- | --- |
| `LW`/`LH`, `TOWER_H` | 57, 74 | Canvas logical size 400x240 (16:9-ish, 1.667 aspect — background art must match this or it gets stretched, see `drawSky()`). Platform height is one fixed constant across all waves now, not per-wave |
| `MINER_ANIM_SPEC` | 154 | Per-skin animation frame lists + anchor points for the 4 non-player skins. `assets/anim/<skin>/*.png` |
| `PLAYER_FIG_SPECS` | 297 | The six static aim-angle bucket poses (8/24/40/56/72/88 degrees down). `assets/figure_*.png` |
| `PLAYER_THROW_SPEC` | 348 | Player's wind/release/recovery animation frames + the one baked throw angle (~8deg) this clip covers, with a +-20deg correction cap. `assets/anim/player/*.png` |
| `WAVES` | 628 | The 5-entry wave table: name/year, difficulty knobs. No `h` (platform height) field anymore — removed along with the wave-intro text that displayed it |
| `rockSkinPool()` | 1096 | Which skins are available by wave (wave-gating) |
| `spawnMiner()` | 1104 | Picks miner type (`rock`/`jumper`) and, for `rock`, a skin from the pool |
| `maybeSpawnVinegar()`/`spawnVinegarMiner()` | 1125/1136 | Soldier's vinegar-bottle path, scheduled not random |
| `throwRock()`/`throwBottle()` | 1169/1182 | Projectile launch physics. Archer gets its own flatter/faster arc inside `throwRock()` (`archer` skin check) |
| `updateMiners()` | 1199 | walk -> stand -> wind -> **release** (new in v7.3: a short animated window before back to stand) -> stand |
| `updateRocks()` | 1277 | Projectile flight + hit detection. Plain rock and prospector's nugget both carry a fading motion trail now (added after "rocks disappear" bug report) |
| `drawSky()` | 1476 | Draws the per-wave background stretched to `LW`x`LH` — new background art must match that 1.667 aspect or it'll stretch |
| `drawMinerPier()`/`drawPlatform()` | 1576/1620 | Enemy pier (procedural) and player's tower platform (`assets/deck.png`+`assets/trestle.png` via `assets/sprites/`) |
| `drawFigure()` | 1697 | Player's body draw dispatch: PLAYER_THROW_ANIM (COCKED/FLIGHT/RECOVERING) -> PLAYER_FIG_BUCKETS (IDLE/MOVING) -> old fallback sprite -> vector art |
| `drawMinerSprite()`/`drawMinerSkin()`/`drawMiner()`/`drawVinegarMiner()` | 2093/2119/2164/2247 | Miner body draw dispatch, same fallback-chain idea as `drawFigure()` |

## Asset inventory

**Active, current art** (what actually renders):
- `assets/anim/{rockthrower,soldier,prospector,archer,player}/*.png` — real extracted animation frames, the v7.3 work
- `assets/figure_*.png` — player's six idle aim-bucket poses
- `assets/bg_*.png` — the five wave backgrounds
- `assets/{rockthrower,soldier,prospector,archer}.png` — static fallback pose per skin, used only if that skin's `MINER_ANIM` entry fails to load
- `assets/sprites/{fish,deck,trestle}.png` — fish sprite sheet and the player's tower platform art, both still load-bearing every frame
- `assets/miner_pier.png`, `assets/player_tower.png` — referenced directly, unrelated to the `SPR_*` split above

**Fallback-only, not visibly reachable in practice** (kept for the
"never hard-fail on an asset problem" principle the v3 comments
describe, but the newer systems that supersede them always load
successfully): `assets/sprites/{fig,miner,cocked,spear,sky,pool,scene}.png`.
Safe to ignore unless deliberately testing the fallback chain. Not
pruned as part of the base64 split — that would be a behavior change
(removing a fallback path), not a mechanical one.

## Known compromises (candidates for the art/animation revision pass)

These are specific, already-diagnosed rough edges from `DESIGN.md` —
worth having in one place rather than re-discovering:

- **Prospector's release frames lose the very tip of his pointing
  finger.** His thrown nugget's glow never fully separated from his
  body during extraction; fixed with a positional cutoff that costs a
  few pixels of fingertip in the later release frames.
- **Player's throw animation only covers one aim angle (~8 degrees).**
  Steep throws (70-88deg) use a rotation correction capped at +-20deg,
  which is honest but visibly approximate at that end of the range.
  `ANIMATION_PROMPTS.md` already asks for 3 angles (shallow/mid/steep)
  in a revision pass for exactly this reason.
- **Wave 3's background has a small, barely-visible human figure** near
  the tent on the right side, left over from generation despite the
  prompt saying no people. Imperceptible at actual in-game scale;
  flagged in case a future crop/zoom makes it visible.

## Out of scope, confirmed not touched

The `jumper` (rival-angler) miner type, the dormant buff-drop system
tie-in for prospector's nugget, and the willow-weir mechanic. None of
these are blocked on anything above — they're just not part of this
pass.
