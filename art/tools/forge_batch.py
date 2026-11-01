"""Generate raw art for slots.json through a local Forge (Flux) API.

Each slot is redrawn img2img from today's file, so the pose, the feet point,
the water line and the banks stay where the game expects them and only the
rendering changes. Characters and props are put on flat green #00B140 first,
so conform.py can key them out afterwards.

    python art/tools/forge_batch.py --path assets/bg_mountainvista.png
    python art/tools/forge_batch.py --group miner_soldier --variants 2
    python art/tools/forge_batch.py --all

Every variant goes to art/staging/candidates/<slot path>/vN.png and variant 1
is copied to art/staging/raw/<slot path> for conform.py. Forge must be
running with --api (http://127.0.0.1:7860 by default).
"""
import argparse
import base64
import io
import json
import shutil
import time
import urllib.request
from pathlib import Path

from PIL import Image

from common import GAME, RAW, STAGING, load_slots, select_slots

CANDIDATES = STAGING / "candidates"
GREEN = (0, 177, 64)
MAGENTA = (255, 0, 255)
CHECKPOINT = "flux1-dev-fp8.safetensors"

# What each group should show. The slot's own prompt wins, then the group's
# prompt in slots.json, then these defaults.
SUBJECT = {
    "backgrounds": "Wide landscape of a forested river valley, horizon-line framing, no people, no boats, no text.",
    "legacy_bg": "Forested river valley scenery, no people, no text.",
    "player_aim": "A rugged frontier fisherman standing on his right, holding a long fishing spear ready to throw, facing screen right.",
    "player_throw": "A rugged frontier fisherman throwing a long fishing spear toward screen right.",
    "miner_rockthrower": "A muscular warrior in red ochre body paint with a feathered headdress, bone necklace and a leather pouch at his hip, in a throwing stance facing screen left.",
    "miner_soldier": "A grizzled bearded old soldier-miner in a blue cavalry uniform and slouch hat with a miner's headlamp, rifle slung on his back, holding whiskey bottles, facing screen left.",
    "miner_soldier_walk": "A grizzled bearded old soldier-miner in a blue cavalry uniform and slouch hat with a miner's headlamp, rifle slung on his back, walking toward screen left.",
    "miner_prospector": "A grizzled bearded old prospector in a brass miner's helmet with headlamp, khaki work shirt, leather satchels full of gold nuggets and gems, facing screen left.",
    "miner_prospector_walk": "A grizzled bearded old prospector in a brass miner's helmet with headlamp, khaki work shirt and leather satchels, walking toward screen left.",
    "miner_archer": "A frontier archer with a longbow, facing screen left.",
    "miner_archer_walk": "A frontier archer carrying a longbow, walking toward screen left.",
    "props": "A weathered wooden prop for a riverside fishing game.",
    "props_tiles": "A weathered wooden game prop.",
    "fish": "Salmon and trout swimming, side view, facing screen right.",
}
SPRITE_TAIL = (" Full body, the whole figure in frame. Isolated on a flat solid pure green background,"
               " no floor, no shadow, no dock or plank under the feet, crisp clean edges.")
PROP_TAIL = " The whole object in frame. Isolated on a flat solid pure green background, no shadow, crisp clean edges."
FISH = {
    "redband": "A redband rainbow trout swimming, side view facing screen right, olive back with black spots and a bright red stripe along its side.",
    "bull": "A bull trout swimming, side view facing screen right, grey-olive body with pale cream spots and white-edged fins.",
    "chinook": "A chinook salmon swimming, side view facing screen right, dark green-grey back with black spots and a silver-grey belly.",
    "steelhead": "A steelhead trout swimming, side view facing screen right, bright silver body with a blue-teal back and fine black spots.",
}
FISH_TAIL = " The whole fish in frame. Isolated on a flat solid magenta background, no shadow, no water, crisp clean edges."
BG_TAIL =" Crisp clean rendering, sharp edges with no jagged aliasing or noisy texture, no watermark, no UI."


def slot_prompt(data, s):
    style = data.get("style_anchor", "")
    body = s.get("prompt") or data["groups"].get(s["group"], {}).get("prompt") or SUBJECT.get(s["group"], "")
    if not s["alpha"]:
        tail = BG_TAIL
    elif s["group"].startswith("props") or s["group"] == "fish":
        tail = PROP_TAIL
    else:
        tail = SPRITE_TAIL
    return f"{style} {body}{tail}".strip()


def snap(v, m=64):
    return max(m, int(round(v / m)) * m)


def init_image(s, im=None, key=GREEN):
    """Today's file (or `im`), flattened onto `key` and sized for Flux. Returns (PIL image, size)."""
    if im is None:
        with Image.open(GAME / s["path"]) as f:
            im = f.convert("RGBA")
    w, h = im.size
    if not s["alpha"]:
        # Backgrounds: ~1MP at the file's own aspect.
        k = (1024 * 1024 / (w * h)) ** 0.5
        size = (snap(w * k), snap(h * k))
        return im.convert("RGB").resize(size, Image.LANCZOS), size
    # Sprites: long side ~1024, padded with the key colour to a multiple of 64.
    k = 1024 / max(w, h)
    sw, sh = max(1, round(w * k)), max(1, round(h * k))
    big = im.resize((sw, sh), Image.LANCZOS)
    size = (snap(sw + 64), snap(sh + 64))
    canvas = Image.new("RGBA", size, key + (255,))
    canvas.alpha_composite(big, ((size[0] - sw) // 2, (size[1] - sh) // 2))
    return canvas.convert("RGB"), size


def jobs_for(s):
    """(name, init image, size, raw destination) per image a slot needs.

    The fish atlas becomes one job per species frame, on magenta since the
    steelhead is close to green; conform it with --key 255,0,255.
    """
    if s["group"] != "fish":
        init, size = init_image(s)
        return [(s["path"], init, size, RAW / s["path"])]
    with Image.open(GAME / s["path"]) as f:
        atlas = f.convert("RGBA")
    base = Path(s["path"]).with_suffix("")
    out = []
    for sp, info in s["species"].items():
        for n, (x, y, w, h) in enumerate(info["frames"]):
            init, size = init_image(s, atlas.crop((x, y, x + w, y + h)), MAGENTA)
            name = (base / sp / f"{n}.png").as_posix()
            out.append((name, init, size, RAW / name))
    return out


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def call(url, payload, timeout=900):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", action="append", help="only these groups (repeatable)")
    ap.add_argument("--path", action="append", help="only these slot paths (repeatable)")
    ap.add_argument("--all", action="store_true", help="every slot except legacy_keep")
    ap.add_argument("--variants", type=int, default=2)
    ap.add_argument("--denoise", type=float, help="override denoise (default 0.55 backgrounds, 0.45 sprites)")
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--dcfg", type=float, default=3.5, help="Flux distilled CFG")
    ap.add_argument("--seed", type=int, default=1101)
    ap.add_argument("--url", default="http://127.0.0.1:7860")
    ap.add_argument("--skip-existing", action="store_true", help="skip slots that already have candidates")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_slots()
    if not (args.all or args.group or args.path):
        ap.error("pick slots with --path, --group or --all")
    slots = [s for s in select_slots(data, args.group, args.path) if s["group"] != "legacy_keep"]
    print(f"{len(slots)} slots x {args.variants} variants")

    jobs = [(s, *j) for s in slots for j in jobs_for(s)]
    for i, (s, name, init, size, dst) in enumerate(jobs, 1):
        out_dir = CANDIDATES / name
        if args.skip_existing and (out_dir / "v1.png").exists():
            continue
        prompt = slot_prompt(data, s)
        if s["group"] == "fish":
            prompt = f"{data.get('style_anchor', '')} {FISH[name.split('/')[-2]]}{FISH_TAIL}"
        denoise = args.denoise if args.denoise is not None else (0.55 if not s["alpha"] else 0.45)
        seed = s["seed"] if s.get("seed") is not None else args.seed
        print(f"[{i}/{len(jobs)}] {name} {size[0]}x{size[1]} denoise {denoise}")
        if args.dry_run:
            print("   ", prompt)
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        init.save(out_dir / "init.png")
        for v in range(1, args.variants + 1):
            t = time.time()
            res = call(args.url + "/sdapi/v1/img2img", {
                "init_images": [b64(init)],
                "prompt": prompt,
                "negative_prompt": "",
                "denoising_strength": denoise,
                "width": size[0], "height": size[1],
                "steps": args.steps,
                "sampler_name": "Euler", "scheduler": "Simple",
                "cfg_scale": 1, "distilled_cfg_scale": args.dcfg,
                "seed": seed + v - 1,
                "override_settings": {"sd_model_checkpoint": CHECKPOINT},
            })
            img = Image.open(io.BytesIO(base64.b64decode(res["images"][0])))
            img.save(out_dir / f"v{v}.png")
            print(f"    v{v} seed {seed + v - 1} in {time.time() - t:.0f}s")
        (out_dir / "prompt.txt").write_text(
            f"{prompt}\n\ndenoise={denoise} steps={args.steps} dcfg={args.dcfg} seed={seed}\n", encoding="utf-8")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out_dir / "v1.png", dst)


if __name__ == "__main__":
    main()
