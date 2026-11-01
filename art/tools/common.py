"""Shared helpers for the CLAIMJUMPER! art pipeline.

Everything here is plain numpy + Pillow (scipy is used if installed, for
speed). Nothing in this folder is loaded by the game; it only reads and
writes PNGs.
"""
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ART = Path(__file__).resolve().parent.parent
REPO = ART.parent
GAME = REPO / "claimjumper"
SLOTS_FILE = ART / "slots.json"
STAGING = ART / "staging"
RAW = STAGING / "raw"
CONFORMED = STAGING / "conformed"
OUT = ART / "out"

ALPHA_THR = 16  # alpha at or below this counts as transparent when measuring


# ---------------------------------------------------------------- slots

def load_slots():
    return json.loads(SLOTS_FILE.read_text(encoding="utf-8"))


def save_slots(data):
    SLOTS_FILE.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


def slots_by_path(data):
    return {s["path"]: s for s in data["slots"]}


def select_slots(data, groups=None, paths=None):
    out = []
    for s in data["slots"]:
        if groups and s["group"] not in groups:
            continue
        if paths and s["path"] not in paths:
            continue
        out.append(s)
    return out


# ---------------------------------------------------------------- images

def load_rgba(path):
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def save_png(arr, path, opaque=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(arr, "RGBA")
    if opaque:
        im = im.convert("RGB")
    im.save(path, optimize=True)


def is_opaque(arr):
    return int(arr[..., 3].min()) >= 250


def bbox(arr, thr=ALPHA_THR):
    ys, xs = np.nonzero(arr[..., 3] > thr)
    if not len(ys):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def feet_x(arr, bb, thr=ALPHA_THR):
    """Mean x of opaque pixels in the bottom few rows of the subject."""
    x0, y0, x1, y1 = bb
    band = max(3, int((y1 - y0) * 0.04))
    ys, xs = np.nonzero(arr[y1 - band:y1, x0:x1, 3] > thr)
    if not len(xs):
        return (x0 + x1) / 2
    return float(xs.mean() + x0)


def measure(arr):
    bb = bbox(arr)
    if bb is None:
        return None
    return {"bbox": bb, "feet_x": round(feet_x(arr, bb), 1), "bottom": bb[3]}


def resize_rgba(arr, w, h):
    """Lanczos resize on premultiplied alpha, so edges don't pick up dark fringes."""
    im = Image.fromarray(arr, "RGBA").convert("RGBa")
    im = im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
    return np.array(im.convert("RGBA"))


# ---------------------------------------------------------------- cut-out

def extract_alpha(arr, key=None, tol=48.0, soft=24.0):
    """Give an image real transparency.

    If it already has alpha (e.g. from BiRefNet/rembg), it is returned as is.
    Otherwise the background is keyed out: the key colour is the median of
    the border pixels unless given, and pixels within `tol` of it become
    transparent, with a `soft` ramp for anti-aliased edges. Green spill is
    pulled out of edge pixels when the key is green.
    """
    if not is_opaque(arr):
        return arr
    rgb = arr[..., :3].astype(np.float32)
    if key is None:
        border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
        key = np.median(border, axis=0)
    key = np.asarray(key, dtype=np.float32)
    dist = np.sqrt(((rgb - key) ** 2).sum(-1))
    alpha = np.clip((dist - tol) / soft, 0, 1)
    out = arr.copy()
    out[..., 3] = (alpha * 255).astype(np.uint8)
    if key[1] > key[0] + 30 and key[1] > key[2] + 30:  # green screen: remove green spill
        # Classic despill: green may not exceed the brighter of red/blue. Applied
        # everywhere, since spill also tints fully opaque edge pixels. Don't use
        # a green screen for green subjects; use grey or BiRefNet instead.
        g = out[..., 1].astype(np.int32)
        lim = np.maximum(out[..., 0], out[..., 2]).astype(np.int32)
        out[..., 1] = np.minimum(g, lim).astype(np.uint8)
    return out


def _label(mask):
    try:
        from scipy import ndimage
        lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
        return lab, n
    except ImportError:
        pass
    # Pure-Python fallback: label a downsampled copy, then map back up.
    h, w = mask.shape
    f = max(1, int(np.ceil(max(h, w) / 400)))
    small = mask[::f, ::f]
    sh, sw = small.shape
    lab_s = np.zeros((sh, sw), np.int32)
    n = 0
    for y, x in zip(*np.nonzero(small)):
        if lab_s[y, x]:
            continue
        n += 1
        lab_s[y, x] = n
        q = deque([(y, x)])
        while q:
            cy, cx = q.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < sh and 0 <= nx < sw and small[ny, nx] and not lab_s[ny, nx]:
                        lab_s[ny, nx] = n
                        q.append((ny, nx))
    lab = np.repeat(np.repeat(lab_s, f, 0), f, 1)[:h, :w] * mask
    return lab, n


def cleanup(arr, keep_ratio=0.15, alpha_floor=12):
    """Drop faint haze and specks; keep the main subject.

    Keeps the largest connected piece plus any piece at least `keep_ratio`
    of its size (so a detached bowstring survives, a thrown rock or a stray
    speck does not). keep_ratio=1 keeps only the largest piece.
    """
    out = arr.copy()
    out[out[..., 3] <= alpha_floor, 3] = 0
    mask = out[..., 3] > 0
    lab, n = _label(mask)
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        big = sizes.max()
        keep = sizes >= big * keep_ratio
        keep[0] = False
        out[~keep[lab], 3] = 0
    out[out[..., 3] == 0, :3] = 0
    return out


def crop_to(arr, bb):
    x0, y0, x1, y1 = bb
    return arr[y0:y1, x0:x1]


def paste(canvas, sub, ox, oy):
    """Alpha-paste sub onto canvas at integer offset; returns pixels lost off-canvas."""
    H, W = canvas.shape[:2]
    h, w = sub.shape[:2]
    x0, y0 = max(0, ox), max(0, oy)
    x1, y1 = min(W, ox + w), min(H, oy + h)
    lost = int((sub[..., 3] > ALPHA_THR).sum())
    if x1 <= x0 or y1 <= y0:
        return lost
    part = sub[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    lost -= int((part[..., 3] > ALPHA_THR).sum())
    canvas[y0:y1, x0:x1] = part
    return lost
