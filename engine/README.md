# engine

A small, dependency-free 2D game engine shared across projects (CLAIMJUMPER
and future ones). Plain ES modules, no build step — import it straight into
a `<script type="module">` the way `cutting_season.html` would, except the
game loop, input, camera, tilemap, and collision code live here once instead
of being rewritten inline in every game file.

It deliberately does **not** try to be a general framework: no asset
pipeline, no editor, no physics beyond AABB-vs-tilemap. Each game keeps its
own content (levels, sprites, entity logic) in its own repo and just imports
these primitives.

## Modules

- `core/loop.js` — `GameLoop`: fixed-timestep update, variable-rate render
  with an interpolation alpha.
- `core/input.js` — `Input`: keyboard state, with named actions (`up` /
  `down` / `left` / `right` / `action`) mapped to arrow keys + WASD by
  default.
- `core/state.js` — `StateMachine`: menu/playing/paused/game-over style
  scene switching.
- `render/camera.js` — `Camera`: viewport that follows a point and clamps
  to world bounds.
- `render/tilemap.js` — `TileMap`: flat-array grid, solid-tile lookup,
  viewport-culled draw.
- `physics/aabb.js` — `intersects`, `moveAndCollide`: axis-separated AABB
  vs. tilemap collision.

Import everything from the barrel, or reach into a module directly:

```js
import { GameLoop, Input, Camera, TileMap, moveAndCollide } from '../engine/index.js';
```

## Minimal usage

```js
const input = new Input();
const map = new TileMap({ cols: 20, rows: 15, tileSize: 32, data, solid: [1] });
const camera = new Camera({ width: 640, height: 480, worldWidth: map.pixelWidth, worldHeight: map.pixelHeight });
const player = { x: 64, y: 64, w: 24, h: 24, vx: 0, vy: 0 };

const loop = new GameLoop({
  update(dt) {
    const speed = 120;
    player.vx = (input.isDown('right') - input.isDown('left')) * speed;
    player.vy = (input.isDown('down') - input.isDown('up')) * speed;
    moveAndCollide(player, map, dt);
    camera.follow(player.x, player.y);
    input.endFrame();
  },
  render(alpha) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    camera.apply(ctx);
    map.draw(ctx, camera, (id) => (id === 1 ? '#444' : '#111'));
    ctx.fillStyle = '#5ec6ff';
    ctx.fillRect(player.x, player.y, player.w, player.h);
    ctx.restore();
  },
});
loop.start();
```

See `examples/demo.html` for a complete, runnable page built from these
pieces (open it via a local static server, e.g. `python3 -m http.server`,
since `type="module"` imports need `http(s)://`, not `file://`).

## Design intent

This code is meant to be copied or referenced by future single-file-HTML
games the same way `cutting_season.html` was hand-rolled, but shared so the
loop/input/camera/tilemap/collision boilerplate is written once and fixed
in one place. When a new game needs something the engine doesn't do, prefer
extending a module here over re-inlining a one-off version in the game
file — but keep additions to things that are genuinely common across games,
not game-specific content or rules.
