const DEFAULT_ACTIONS = {
  up: ['ArrowUp', 'KeyW'],
  down: ['ArrowDown', 'KeyS'],
  left: ['ArrowLeft', 'KeyA'],
  right: ['ArrowRight', 'KeyD'],
  action: ['Space', 'Enter'],
};

/**
 * Keyboard state tracker. Named "actions" map to one or more KeyboardEvent
 * `code` values, so games can ask isDown('left') instead of juggling both
 * arrow keys and WASD everywhere.
 */
export class Input {
  constructor({ target = window, actions = DEFAULT_ACTIONS } = {}) {
    this.actions = actions;
    this._down = new Set();
    this._pressed = new Set();
    this._released = new Set();

    this._onKeyDown = (e) => {
      if (!this._down.has(e.code)) this._pressed.add(e.code);
      this._down.add(e.code);
    };
    this._onKeyUp = (e) => {
      this._down.delete(e.code);
      this._released.add(e.code);
    };

    this._target = target;
    target.addEventListener('keydown', this._onKeyDown);
    target.addEventListener('keyup', this._onKeyUp);
  }

  destroy() {
    this._target.removeEventListener('keydown', this._onKeyDown);
    this._target.removeEventListener('keyup', this._onKeyUp);
  }

  isDown(action) {
    const codes = this.actions[action] || [action];
    return codes.some((c) => this._down.has(c));
  }

  wasPressed(action) {
    const codes = this.actions[action] || [action];
    return codes.some((c) => this._pressed.has(c));
  }

  wasReleased(action) {
    const codes = this.actions[action] || [action];
    return codes.some((c) => this._released.has(c));
  }

  /** Call once per frame, after game logic has read this frame's input. */
  endFrame() {
    this._pressed.clear();
    this._released.clear();
  }
}
