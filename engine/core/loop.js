/**
 * Fixed-timestep game loop with a render alpha for interpolation.
 *
 *   const loop = new GameLoop({
 *     update: (dt) => { ... },       // dt is always exactly `step` seconds
 *     render: (alpha) => { ... },    // alpha in [0,1): how far into the next tick
 *   });
 *   loop.start();
 */
export class GameLoop {
  constructor({ update, render, step = 1 / 60, maxUpdatesPerFrame = 5 }) {
    this.update = update;
    this.render = render;
    this.step = step;
    this.maxUpdatesPerFrame = maxUpdatesPerFrame;
    this._running = false;
    this._raf = null;
    this._last = 0;
    this._acc = 0;
    this._tick = this._tick.bind(this);
  }

  start() {
    if (this._running) return;
    this._running = true;
    this._last = performance.now();
    this._acc = 0;
    this._raf = requestAnimationFrame(this._tick);
  }

  stop() {
    this._running = false;
    if (this._raf !== null) cancelAnimationFrame(this._raf);
    this._raf = null;
  }

  get running() {
    return this._running;
  }

  _tick(now) {
    if (!this._running) return;

    const elapsed = Math.min((now - this._last) / 1000, this.step * this.maxUpdatesPerFrame);
    this._last = now;
    this._acc += elapsed;

    let updates = 0;
    while (this._acc >= this.step && updates < this.maxUpdatesPerFrame) {
      this.update(this.step);
      this._acc -= this.step;
      updates++;
    }

    this.render(this._acc / this.step);
    this._raf = requestAnimationFrame(this._tick);
  }
}
