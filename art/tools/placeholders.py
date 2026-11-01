"""Make a full set of fake "raw" images to test the pipeline end to end.

Each character/prop becomes a flat-coloured silhouette of today's art,
enlarged and dropped onto a green screen at a different size and offset,
the way a real generation would arrive. Backgrounds become a posterised
1344x768 version (Flux's size). Running conform.py on these must put
everything back exactly where the game expects it.

    python art/tools/placeholders.py
    python art/tools/conform.py
    python art/tools/validate.py
    python art/tools/promote.py --preview
"""
import numpy as np
from PIL import Image, ImageFilter, ImageOps

from common import GAME, RAW, bbox, crop_to, load_rgba, load_slots, resize_rgba, save_png

GREEN = (0, 177, 64)
TINTS = {
    "player": (60, 110, 200), "miner": (200, 70, 50), "props": (140, 100, 60),
    "fish": (230, 180, 40),
}


def tint_for(group):
    for k, v in TINTS.items():
        if group.startswith(k):
            return v
    return (120, 120, 120)


def silhouette(arr, tint, enlarge=2.3, pad=60):
    sub = crop_to(arr, bbox(arr))
    sub = resize_rgba(sub, sub.shape[1] * enlarge, sub.shape[0] * enlarge)
    a = sub[..., 3:4].astype(np.float32) / 255
    # Flat tint with a darker rim so the shape reads.
    im = Image.fromarray(sub[..., 3])
    inner = np.array(im.filter(ImageFilter.MinFilter(9))).astype(np.float32)[..., None] / 255
    col = np.array(tint, np.float32) * (0.55 + 0.45 * inner)
    rgb = col * a + np.array(GREEN, np.float32) * (1 - a)
    h, w = sub.shape[:2]
    canvas = np.zeros((h + 2 * pad, w + 2 * pad + 40, 4), np.uint8)
    canvas[...] = (*GREEN, 255)
    canvas[pad:pad + h, pad + 40:pad + 40 + w, :3] = rgb.astype(np.uint8)
    return canvas


def main():
    data = load_slots()
    n = 0
    for slot in data["slots"]:
        mode = data["groups"][slot["group"]]["mode"]
        src = load_rgba(GAME / slot["path"])
        if mode == "keep":
            continue
        if mode == "background":
            im = Image.fromarray(src).convert("RGB")
            im = ImageOps.posterize(ImageOps.autocontrast(im), 3).filter(ImageFilter.GaussianBlur(2))
            im = im.resize((1344, 768), Image.LANCZOS).convert("RGBA")
            save_png(np.array(im), RAW / slot["path"], opaque=True)
        elif mode == "atlas":
            for sp, info in slot["species"].items():
                for i, (x, y, w, h) in enumerate(info["frames"]):
                    cell = src[y:y + h, x:x + w]
                    if bbox(cell) is None:
                        continue
                    save_png(silhouette(cell, tint_for("fish"), enlarge=4, pad=30),
                             RAW / "assets/sprites/fish" / sp / f"{i}.png", opaque=True)
        else:
            save_png(silhouette(src, tint_for(slot["group"])), RAW / slot["path"], opaque=True)
        n += 1
    print(f"wrote placeholder raws for {n} slots -> {RAW}")


if __name__ == "__main__":
    main()
