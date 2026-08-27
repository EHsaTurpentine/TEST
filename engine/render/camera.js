/**
 * 2D camera: a viewport rectangle in world space that can follow a point
 * and stays clamped to the world bounds (unless the world is smaller than
 * the viewport, in which case it centers).
 */
export class Camera {
  constructor({ width, height, worldWidth = Infinity, worldHeight = Infinity }) {
    this.x = 0;
    this.y = 0;
    this.width = width;
    this.height = height;
    this.worldWidth = worldWidth;
    this.worldHeight = worldHeight;
  }

  follow(targetX, targetY) {
    this.x = clamp(targetX - this.width / 2, 0, this.worldWidth, this.width);
    this.y = clamp(targetY - this.height / 2, 0, this.worldHeight, this.height);
  }

  worldToScreen(x, y) {
    return { x: x - this.x, y: y - this.y };
  }

  /** ctx.save() before, ctx.restore() after — translates draws into camera space. */
  apply(ctx) {
    ctx.translate(-Math.round(this.x), -Math.round(this.y));
  }
}

function clamp(value, min, worldSize, viewportSize) {
  if (worldSize < viewportSize) return (worldSize - viewportSize) / 2;
  return Math.max(min, Math.min(value, worldSize - viewportSize));
}
