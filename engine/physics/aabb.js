/** True if two {x,y,w,h} rectangles overlap. */
export function intersects(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

/**
 * Moves an AABB entity {x,y,w,h,vx,vy} by its velocity against a TileMap,
 * resolving the x and y axes separately so diagonal motion into a corner
 * doesn't tunnel through one axis or stick on the other. Zeroes velocity
 * on any axis where a collision occurred. Mutates and returns `entity`.
 */
export function moveAndCollide(entity, tilemap, dt) {
  entity.x += entity.vx * dt;
  resolveAxis(entity, tilemap, 'x');

  entity.y += entity.vy * dt;
  resolveAxis(entity, tilemap, 'y');

  return entity;
}

// Nudges the trailing edge in off the exact tile boundary so an entity
// resting flush against a wall (edge exactly on the grid line) reads as
// touching, not overlapping — otherwise floor() would place that boundary
// point in the next tile and falsely trigger a collision every frame.
const EPS = 1e-6;

function resolveAxis(entity, tilemap, axis) {
  // Nothing moved on this axis this step, so there's no direction to
  // resolve a correction toward — leave it alone.
  if (axis === 'x' && entity.vx === 0) return;
  if (axis === 'y' && entity.vy === 0) return;

  const corners = [
    [entity.x, entity.y],
    [entity.x + entity.w - EPS, entity.y],
    [entity.x, entity.y + entity.h - EPS],
    [entity.x + entity.w - EPS, entity.y + entity.h - EPS],
  ];

  for (const [px, py] of corners) {
    if (!tilemap.isSolidAt(px, py)) continue;
    const size = tilemap.tileSize;
    if (axis === 'x') {
      entity.x = entity.vx > 0
        ? Math.floor(px / size) * size - entity.w
        : (Math.floor(px / size) + 1) * size;
      entity.vx = 0;
    } else {
      entity.y = entity.vy > 0
        ? Math.floor(py / size) * size - entity.h
        : (Math.floor(py / size) + 1) * size;
      entity.vy = 0;
    }
    return; // one correction per axis per step keeps this simple and stable
  }
}
