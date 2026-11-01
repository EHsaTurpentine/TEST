"""Make raw generated images fit their game slots exactly.

Put raw images in art/staging/raw/ using the same relative path as the
slot (e.g. art/staging/raw/assets/anim/soldier/wind3.png). Any size, any
background: either already cut out (BiRefNet/rembg output with alpha) or
on a flat colour (green or grey), which gets keyed out here.

Fish frames go in art/staging/raw/assets/sprites/fish/<species>/<0-7>.png.

    python art/tools/conform.py                  # everything in staging/raw
    python art/tools/conform.py --group miner_soldier
    python art/tools/conform.py --key 0,177,64 --tol 60

Output lands in art/staging/conformed/ at the slot's path, ready for
validate.py, contact_sheet.py and promote.py.

What each mode does:
  background  cover-crop to the slot's size, saved opaque.
  match       cut out, clean up, scale so the character is the same height
              as today's art (one scale per group, taken from the group's
              reference frame so every frame matches), then place it so its
              feet land on the same pixel as today's art.
  fit_bbox    cut out, scale to fit today's subject box, centre it there.
  atlas       fish: fit each frame into its atlas box, nose on noseTip.
  keep        not processed (legacy fallback strips).
"""
import argparse
import sys
from pathlib import Path

import numpy as np

from common import (CONFORMED, GAME, RAW, bbox, cleanup, crop_to, extract_alpha,
                    load_rgba, load_slots, measure, paste, resize_rgba, save_png)


def cut(raw, args):
    a = extract_alpha(raw, key=args.key, tol=args.tol, soft=args.soft)
    a = cleanup(a, keep_ratio=args.keep_ratio)
    bb = bbox(a)
    if bb is None:
        raise ValueError("nothing left after cut-out (check --key/--tol)")
    return crop_to(a, bb)


def conform_background(raw, slot):
    H, W = slot["height"], slot["width"]
    h, w = raw.shape[:2]
    s = max(W / w, H / h)
    big = resize_rgba(raw, round(w * s), round(h * s))
    y0 = (big.shape[0] - H) // 2
    x0 = (big.shape[1] - W) // 2
    out = big[y0:y0 + H, x0:x0 + W].copy()
    out[..., 3] = 255
    return out, []


def conform_match(sub, slot, scale):
    """sub = cut-out, cropped subject."""
    m = slot["measure"]
    ob = m["bbox"]
    if scale is None:
        scale = (ob[3] - ob[1]) / sub.shape[0]
    nw, nh = round(sub.shape[1] * scale), round(sub.shape[0] * scale)
    s2 = resize_rgba(sub, nw, nh)
    fm = measure(s2)
    if fm is None:
        raise ValueError("subject vanished after resize")
    # Align: new subject's bottom row on today's bottom row, feet centre on today's feet centre.
    ox = round(m["feet_x"] - fm["feet_x"])
    oy = m["bottom"] - fm["bottom"]
    canvas = np.zeros((slot["height"], slot["width"], 4), np.uint8)
    lost = paste(canvas, s2, ox, oy)
    warn = []
    total = int((s2[..., 3] > 16).sum())
    if lost > total * 0.002:
        warn.append(f"{lost} subject pixels ({100 * lost / total:.1f}%) fell outside the {slot['width']}x{slot['height']} canvas")
    return canvas, warn


def conform_fit_bbox(sub, slot):
    ob = slot["measure"]["bbox"]
    bw, bh = ob[2] - ob[0], ob[3] - ob[1]
    s = min(bw / sub.shape[1], bh / sub.shape[0])
    s2 = resize_rgba(sub, round(sub.shape[1] * s), round(sub.shape[0] * s))
    canvas = np.zeros((slot["height"], slot["width"], 4), np.uint8)
    ox = ob[0] + (bw - s2.shape[1]) // 2
    oy = ob[1] + (bh - s2.shape[0]) // 2
    paste(canvas, s2, ox, oy)
    return canvas, []


def conform_atlas(slot, args):
    """Fish atlas: replace any species that has raw frames; keep the rest as is."""
    atlas = load_rgba(GAME / slot["path"])
    base = RAW / Path(slot["path"]).with_suffix("")  # .../sprites/fish/
    done, warn = [], []
    for sp, info in slot["species"].items():
        d = base / sp
        files = [d / f"{i}.png" for i in range(len(info["frames"]))]
        if not any(f.exists() for f in files):
            continue
        missing = [f.name for f in files if not f.exists()]
        if missing:
            warn.append(f"fish {sp}: missing {missing}, those frames keep today's art")
        nose_x, nose_y = info["noseTip"]
        scale = None
        for f, (x, y, w, h) in zip(files, info["frames"]):
            if not f.exists():
                continue
            sub = cut(load_rgba(f), args)
            if scale is None:  # one scale per species, from its first frame
                scale = min((nose_x + 1) / sub.shape[1], h / sub.shape[0])
            s2 = resize_rgba(sub, round(sub.shape[1] * scale), round(sub.shape[0] * scale))
            # nose = rightmost opaque column; its mean row goes on noseTip.y
            cols = np.nonzero((s2[..., 3] > 16).any(0))[0]
            rx = cols.max()
            rows = np.nonzero(s2[:, rx, 3] > 16)[0]
            ny = rows.mean() if len(rows) else s2.shape[0] / 2
            cell = np.zeros((h, w, 4), np.uint8)
            paste(cell, s2, round(nose_x - rx), round(nose_y - ny))
            atlas[y:y + h, x:x + w] = cell
        done.append(sp)
    return (atlas if done else None), done, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", action="append", help="only these groups (repeatable)")
    ap.add_argument("--key", type=lambda s: [float(v) for v in s.split(",")],
                    help="background colour to key out as R,G,B (default: border median)")
    ap.add_argument("--tol", type=float, default=48, help="key distance that counts as background")
    ap.add_argument("--soft", type=float, default=24, help="width of the soft edge ramp")
    ap.add_argument("--keep-ratio", type=float, default=0.15,
                    help="keep detached pieces at least this fraction of the main subject (1 = main subject only)")
    ap.add_argument("--per-frame-scale", action="store_true",
                    help="scale each frame to today's frame height instead of one scale per group")
    args = ap.parse_args()

    data = load_slots()
    groups = data["groups"]
    todo = [s for s in data["slots"] if not args.group or s["group"] in args.group]

    # One scale per group, from its reference frame (if that raw exists).
    group_scale = {}
    for g, info in groups.items():
        ref = info.get("ref")
        if info["mode"] != "match" or not ref or args.per_frame_scale:
            continue
        rp = RAW / ref
        refslot = next(s for s in data["slots"] if s["path"] == ref)
        if rp.exists():
            sub = cut(load_rgba(rp), args)
            ob = refslot["measure"]["bbox"]
            group_scale[g] = (ob[3] - ob[1]) / sub.shape[0]

    n_ok = n_warn = n_err = 0
    for slot in todo:
        mode = groups[slot["group"]]["mode"]
        out_path = CONFORMED / slot["path"]
        try:
            if mode == "keep":
                continue
            if mode == "atlas":
                atlas, done, warn = conform_atlas(slot, args)
                if atlas is None:
                    continue
                save_png(atlas, out_path)
                msg = f"fish species {done}"
            else:
                rp = RAW / slot["path"]
                if not rp.exists():
                    continue
                raw = load_rgba(rp)
                if mode == "background":
                    out, warn = conform_background(raw, slot)
                    save_png(out, out_path, opaque=True)
                else:
                    sub = cut(raw, args)
                    if mode == "match":
                        g = slot["group"]
                        if groups[g].get("ref") and g not in group_scale and not args.per_frame_scale:
                            warn_ref = f"no raw for reference frame {groups[g]['ref']}; scaled this frame on its own"
                        else:
                            warn_ref = None
                        out, warn = conform_match(sub, slot, group_scale.get(g))
                        if warn_ref:
                            warn.append(warn_ref)
                    else:
                        out, warn = conform_fit_bbox(sub, slot)
                    save_png(out, out_path)
                msg = ""
            if warn:
                n_warn += 1
                for w in warn:
                    print(f"WARN  {slot['path']}: {w}")
            else:
                n_ok += 1
                print(f"ok    {slot['path']} {msg}".rstrip())
        except Exception as e:  # keep going; report at the end
            n_err += 1
            print(f"ERROR {slot['path']}: {e}")
    print(f"\nconformed {n_ok + n_warn} file(s): {n_ok} clean, {n_warn} with warnings, {n_err} failed -> {CONFORMED}")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
