/**
 * Minimal scene/state machine. Each state is a plain object with any of
 * enter(...args) / update(dt) / render(ctx, alpha) / exit().
 *
 *   const game = new StateMachine({
 *     menu: { enter, update, render },
 *     playing: { enter, update, render, exit },
 *   }, 'menu');
 *   game.update(dt); game.render(ctx, alpha);
 *   game.change('playing');
 */
export class StateMachine {
  constructor(states, initial) {
    this.states = states;
    this.current = null;
    this._name = null;
    if (initial) this.change(initial);
  }

  get name() {
    return this._name;
  }

  change(name, ...args) {
    const next = this.states[name];
    if (!next) throw new Error(`Unknown state: ${name}`);
    if (this.current && this.current.exit) this.current.exit();
    this._name = name;
    this.current = next;
    if (this.current.enter) this.current.enter(...args);
  }

  update(dt) {
    if (this.current && this.current.update) this.current.update(dt);
  }

  render(ctx, alpha) {
    if (this.current && this.current.render) this.current.render(ctx, alpha);
  }
}
