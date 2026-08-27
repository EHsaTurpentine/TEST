/**
 * Grid tilemap backed by a flat array of tile ids. Out-of-bounds tiles are
 * treated as solid, so entities can't walk off the edge of the map without
 * the game having to special-case it.
 */
export class TileMap {
  constructor({ cols, rows, tileSize, data, solid = [] }) {
    this.cols = cols;
    this.rows = rows;
    this.tileSize = tileSize;
    this.data = data; // flat array, length cols*rows, row-major
    this.solid = new Set(solid);
  }

  get pixelWidth() {
    return this.cols * this.tileSize;
  }

  get pixelHeight() {
    return this.rows * this.tileSize;
  }

  tileAt(col, row) {
    if (col < 0 || row < 0 || col >= this.cols || row >= this.rows) return undefined;
    return this.data[row * this.cols + col];
  }

  isSolidAt(worldX, worldY) {
    const col = Math.floor(worldX / this.tileSize);
    const row = Math.floor(worldY / this.tileSize);
    const tile = this.tileAt(col, row);
    return tile === undefined ? true : this.solid.has(tile);
  }

  /** Draws only the tiles visible through `camera`. tileColor(id) => CSS color, or falsy to skip. */
  draw(ctx, camera, tileColor) {
    const startCol = Math.max(0, Math.floor(camera.x / this.tileSize));
    const startRow = Math.max(0, Math.floor(camera.y / this.tileSize));
    const endCol = Math.min(this.cols - 1, Math.floor((camera.x + camera.width) / this.tileSize));
    const endRow = Math.min(this.rows - 1, Math.floor((camera.y + camera.height) / this.tileSize));

    for (let row = startRow; row <= endRow; row++) {
      for (let col = startCol; col <= endCol; col++) {
        const color = tileColor(this.tileAt(col, row));
        if (!color) continue;
        ctx.fillStyle = color;
        ctx.fillRect(col * this.tileSize, row * this.tileSize, this.tileSize, this.tileSize);
      }
    }
  }
}
