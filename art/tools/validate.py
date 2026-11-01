"""Check art files against their slots before they go into the game.

    python art/tools/validate.py              # staged files in art/staging/conformed
    python art/tools/validate.py --game       # every file the game loads, in claimjumper/
    python art/tools/validate.py --group backgrounds

Exit code 1 if anything is an error, so scripts can stop on it.

Checks: file present, exact canvas size, transparency where the slot needs
it (and none where it doesn't), subject not empty, subject not cut off at
the canvas edge, and for characters and props that the feet sit on the
same bottom row and centre as today's art.
"""
import argparse
import sys

import numpy as np

from common import CONFORMED, GAME, load_rgba, load_slots, measure

FEET_ROW_TOL = 2       # px
FEET_X_TOL_FRAC = 0.04  # of canvas width


def check(slot, arr, mode):
    errs, warns = [], []
    h, w = arr.shape[:2]
    if (w, h) != (slot["width"], slot["height"]):
        errs.append(f"size {w}x{h}, slot needs {slot['width']}x{slot['height']}")
        return errs, warns
    opaque = int(arr[..., 3].min()) >= 250
    if mode in ("background",):
        if not opaque:
            errs.append("background has transparent pixels; it must be fully opaque")
        return errs, warns
    if not slot["alpha"]:
        return errs, warns
    if opaque:
        errs.append("no transparency; cut the subject out first")
        return errs, warns
    m = measure(arr)
    if m is None:
        errs.append("image is fully transparent")
        return errs, warns
    old = slot["measure"]
    x0, y0, x1, y1 = m["bbox"]
    ox0, oy0, ox1, oy1 = old["bbox"]
    # Touching an edge today's art doesn't touch usually means a clipped limb.
    edges = []
    if mode != "atlas":
        if x0 == 0 and ox0 > 2: edges.append("left")
        if y0 == 0 and oy0 > 2: edges.append("top")
        if x1 == w and ox1 < w - 2: edges.append("right")
        if y1 == h and oy1 < h - 2: edges.append("bottom")
    if edges:
        warns.append(f"subject touches the {'/'.join(edges)} edge; may be cut off")
    if mode == "match":
        if abs(m["bottom"] - old["bottom"]) > FEET_ROW_TOL:
            errs.append(f"feet on row {m['bottom']}, should be {old['bottom']} (+-{FEET_ROW_TOL})")
        tol = max(3, w * FEET_X_TOL_FRAC)
        if abs(m["feet_x"] - old["feet_x"]) > tol:
            errs.append(f"feet centred at x={m['feet_x']}, should be {old['feet_x']} (+-{tol:.0f})")
        oh, nh = oy1 - oy0, y1 - y0
        if not (0.75 * oh <= nh <= 1.3 * oh):
            warns.append(f"subject is {nh}px tall vs {oh}px today; check the size reads right in game")
    coverage = float((arr[..., 3] > 16).mean())
    if coverage < 0.01:
        warns.append(f"subject covers only {coverage:.1%} of the canvas")
    return errs, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", action="store_true", help="check claimjumper/ (all files must exist)")
    ap.add_argument("--group", action="append", help="only these groups (repeatable)")
    ap.add_argument("--quiet", action="store_true", help="only print problems")
    args = ap.parse_args()

    data = load_slots()
    root = GAME if args.game else CONFORMED
    n_err = n_warn = n_ok = n_missing = 0
    for slot in data["slots"]:
        if args.group and slot["group"] not in args.group:
            continue
        mode = data["groups"][slot["group"]]["mode"]
        if mode == "keep":
            continue
        p = root / slot["path"]
        if not p.exists():
            if args.game:
                n_err += 1
                print(f"ERROR {slot['path']}: missing")
            else:
                n_missing += 1
            continue
        errs, warns = check(slot, load_rgba(p), mode)
        for e in errs:
            print(f"ERROR {slot['path']}: {e}")
        for wmsg in warns:
            print(f"WARN  {slot['path']}: {wmsg}")
        if errs:
            n_err += 1
        elif warns:
            n_warn += 1
        else:
            n_ok += 1
            if not args.quiet:
                print(f"ok    {slot['path']}")
    where = "claimjumper/" if args.game else "art/staging/conformed/"
    tail = "" if args.game else f", {n_missing} slot(s) not staged"
    print(f"\n{where}: {n_ok} ok, {n_warn} warning(s), {n_err} error(s){tail}")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
