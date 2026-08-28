# Building a New Game on This Engine

A reusable starting point for the next game — what `engine/` gives you for free, the patterns that worked well building CLAIMJUMPER on top of it, and a fill-in-the-blanks GDD template to kick off the next project.

This is a *template*, not a retrospective. Copy the template section into a new `GAME_NAME/DESIGN.md` and fill it in before writing code.

---

## 1. What `engine/` gives you

Plain ES modules, no build step, imported straight into a single-file HTML game:

```js
import { GameLoop } from '../engine/index.js';
```

| Module | Exports | What it's for |
|---|---|---|
| `core/loop.js` | `GameLoop` | Fixed-timestep accumulator loop. Decouples simulation rate from display rate — call `.start(update, render)`; `update(dt)` fires at a constant tick, `render(alpha)` fires once per frame with an interpolation factor. |
| `core/input.js` | `Input` | Named-action key mapping (`{ left: ['ArrowLeft','a'], jump: ['Space'] }`) instead of raw keycodes scattered through game logic. |
| `core/state.js` | `StateMachine` | Simple state graph (TITLE → PLAY → PAUSE → GAMEOVER, etc.) with enter/exit hooks. |
| `render/camera.js` | `Camera` | 2D camera with position/zoom, world-to-screen transform. |
| `render/tilemap.js` | `TileMap` | Grid-based tile storage + lookup, for tile-based level layouts. |
| `physics/aabb.js` | `intersects`, `moveAndCollide` | Axis-aligned bounding box collision, with epsilon-based flush-contact handling (see §2.3 — this one has a real bug history, use it as-is rather than reimplementing). |

See `engine/README.md` and `engine/examples/demo.html` for a minimal runnable example of all of these wired together.

**Design philosophy**: the engine only owns things every 2D arcade game needs (timing, input, collision, camera). It does *not* own rendering style, entity structure, or game rules — that all stays in the game's own `index.html`. Don't push game-specific logic (skins, waves, scoring) down into `engine/`; keep the engine generic and let each game import only what it needs.

---

## 2. Patterns worth reusing (learned building CLAIMJUMPER)

### 2.1 One file, one game, graceful asset loading
Keep each game as a single `index.html` (or close to it) with inline `<script type="module">`. For every external asset (image, sprite sheet), load it independently and let the game render a fallback (vector/procedural shape, or simply skip the visual) if the asset hasn't loaded yet — never let a missing or slow-loading asset throw and kill the render loop.

```js
const ART = { tower: null };
(async function loadArt(){
  for (let attempt = 0; attempt < 3; attempt++){
    try {
      ART.tower = await loadImage(`assets/tower.png?retry=${attempt}`);
      break;
    } catch { await sleep(300 * (attempt + 1)); }
  }
})();
// render path:
if (ART.tower) ctx.drawImage(ART.tower, ...);
else drawFallbackShape(...); // never a hard failure
```

This pattern caught a real production bug: one skin image silently failed to load over a mobile network on a specific device, with no console visible to the user to diagnose it. Retry-with-backoff plus a visible fallback turns a silent asset failure into a minor visual regression instead of a broken game.

### 2.2 Per-level/per-wave visual variety without extra complexity
If the game has discrete levels/waves/stages, give each one its own background image (`WAVE_BG_FILES[]`) and treat it as the literal play-field background, not just a splash screen — swap it in wherever the old procedural background/sky/water was drawn, with an early-return check ("if a real backdrop image is active, skip painting the procedural layers"). Layer decorative structures (towers, spawn points, platforms) on top with a small per-level *random* offset/rotation rolled once at level start:

```js
function startWave(){
  G.towerX = BASE_X + rnd(-8, 8);
  G.towerRot = rnd(-6, 6) * D2R;
}
```

Apply the rotation around the structure's own anchor point via `ctx.save()/translate()/rotate()/restore()`, not around the image's bounding-box center, and never rotate anything that other systems (gameplay coordinates, collision, aim math) depend on being axis-aligned. This gets visual variety cheaply without touching gameplay logic at all.

### 2.3 Angle-bucket sprites beat whole-body rotation
For an aim-driven or pose-driven character, don't rotate one rigid reference image across a wide angle range — a whole-body sprite rotated more than ~15-20° reads as "collapsing," not aiming. Instead, commission (or crop) a small set of discrete pose images (5-8 buckets covering the practical angle range), each tagged with its own assigned angle and anchor point, and pick the nearest bucket at render time:

```js
function nearestBucket(angleDeg){
  return BUCKETS.reduce((best, b) =>
    Math.abs(b.angle - angleDeg) < Math.abs(best.angle - angleDeg) ? b : best);
}
```

Optionally apply a small *capped* corrective rotation on top (±15-20°) to smooth the gaps between buckets — never uncapped, or you reintroduce the same collapsing artifact at the bucket boundaries.

### 2.4 AABB collision epsilon
`physics/aabb.js`'s `moveAndCollide` already handles a subtle flush-contact bug (an entity resting exactly against a wall on one axis getting teleported on the *other*, zero-velocity axis, because floor()-boundary math treated the touching point as "inside" the next cell). It's fixed with an `EPS = 1e-6` tolerance and a skip-if-zero-velocity guard per axis. If you ever need custom collision beyond AABB, keep this epsilon-and-zero-velocity-guard pattern — it's a real, easy-to-reintroduce bug, not a hypothetical one.

### 2.5 Verify visually, not just by reading code
Canvas-heavy bugs (transparency, alignment, rotation artifacts) are frequently invisible from source alone and often invisible in a naive tool preview too — a fully-transparent (alpha=0) region can render as if it were opaque content in some previews. Confirm visually:
- Run a local static server, drive it with Playwright, take real screenshots at the actual game resolution.
- For alpha/transparency work on a PNG, composite it over a checkerboard and inspect that, or sample pixel alpha directly — don't trust a plain image preview.
- Any temporary debug hook added for diagnosis (e.g. `window.__gameDebug`) gets removed before the final commit.

### 2.6 Deploy pipeline
GitHub Pages via Actions (`actions/upload-pages-artifact` + `actions/deploy-pages`) — see `.github/workflows/build-content.yml` at the repo root; it already builds `manifest.json` and deploys the whole site, so a new game folder under the repo root is live automatically once pushed. Pages deploys occasionally hit a GitHub-side timeout (~10 min) unrelated to the code — if a deploy run fails on infra grounds, the next push carries the same commit through; don't chase it as a code bug.

### 2.7 Keep a living DESIGN.md
Chat sessions can break or time out mid-project. A per-game `DESIGN.md`, updated every time a real decision is made (not just at the end), is what let this project recover context across session breaks. Write it as you go, not as a retrospective at the end.

---

## 3. New Game Template

Copy this into `<game-folder>/DESIGN.md` and fill it in before writing code.

```markdown
# <GAME NAME> — Design Document

## 1. Pitch
One or two sentences: what is this game, and what's the hook?

## 2. Core loop
What does the player do, moment to moment? (e.g. aim → throw → dodge → repeat)
What's the win condition? What's the lose condition?

## 3. Controls
| Input | Action |
|---|---|
| | |

## 4. Structure
- Single continuous level, or discrete waves/stages/levels?
- If staged: how many, how do they escalate (difficulty, enemy variety, visuals)?
- Scoring/progression model?

## 5. Entities
| Entity | Behavior | Notes |
|---|---|---|
| Player | | |
| Enemy type 1 | | |
| ... | | |

## 6. Visual style
- Resolution / canvas size / scale factor
- Art approach: procedural/vector, static reference images, sprite sheets, angle-bucket poses?
- Per-level visual variety plan (backgrounds? palette shifts? structure randomization?)

## 7. Assets needed
- [ ] Backgrounds (how many, what scenes)
- [ ] Character art (poses/buckets needed, if angle-driven)
- [ ] Enemy/prop art
- [ ] Audio (if any)

## 8. Engine modules to use
- [ ] GameLoop
- [ ] Input
- [ ] StateMachine
- [ ] Camera
- [ ] TileMap
- [ ] AABB collision

## 9. Open questions
Anything undecided going in — resolve these before or during early prototyping, and log the decision here once made.
```

---

## 4. Checklist to start a new game

1. `mkdir <game-folder>/` at the repo root, `mkdir <game-folder>/assets/`.
2. Copy the template above into `<game-folder>/DESIGN.md`, fill in what you already know.
3. Scaffold `<game-folder>/index.html`: canvas element, `import { GameLoop, Input, ... } from '../engine/index.js';`, a minimal state machine (TITLE → PLAY), and a placeholder render loop drawing a solid background — confirm it runs before adding any game logic.
4. Build the core loop first (movement/aim/action + one enemy/obstacle type) with procedural placeholder shapes. Get it *fun* before it's *pretty*.
5. Layer in real art using the graceful-fallback pattern (§2.1) so the game never breaks while art is still in progress.
6. Add per-level variety (§2.2) once the core loop is solid, not before.
7. Verify with Playwright screenshots at each major milestone, not just at the end.
8. Push — the existing GitHub Actions workflow deploys the whole repo automatically; no new workflow needed per game.

---

## 5. Licensing note

This repository is CC0 1.0 Universal (public domain dedication) — see `/LICENSE`. Code and design docs in this repo, including this one, carry no restrictions on reuse. That covers the code; it does not retroactively establish provenance for any third-party reference images brought into a game's `assets/` folder from outside this repo — track that separately per asset if it matters for a given project.
