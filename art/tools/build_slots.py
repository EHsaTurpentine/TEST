"""Build art/slots.json: one row per art file the game loads.

Reads claimjumper/index.html for the numbers the engine uses (anchors,
scales, fish atlas boxes) and measures the current PNGs (canvas size,
subject bounding box, where the feet are). Re-running keeps any prompt,
seed, model, status, etc. already filled in.

    python art/tools/build_slots.py
"""
import json
import re
import sys

from common import GAME, SLOTS_FILE, cleanup, load_rgba, measure, is_opaque, save_slots

STYLE_ANCHOR = (
    "Painterly 2D video game illustration, clean bold linework, saturated color, "
    "soft cel-shading with directional light, smooth anti-aliased edges, "
    "game-sprite illustration style."
)

# Fields people/LLMs fill in; preserved across rebuilds.
KEEP = ["status", "prompt", "negative", "seed", "model", "lora", "license", "notes"]


def must(pattern, text, what, flags=0):
    m = re.search(pattern, text, flags)
    if not m:
        sys.exit(f"build_slots: could not find {what} in index.html -- engine changed? Update this script.")
    return m


def main():
    html = (GAME / "index.html").read_text(encoding="utf-8")

    # Player aim poses: per-file anchors.
    fig = re.findall(r"file:'(assets/figure_\w+\.png)',\s*angle:(\d+),\s*anchorX:(\d+),\s*anchorY:(\d+)", html)
    if len(fig) != 6:
        sys.exit("build_slots: expected 6 PLAYER_FIG_SPECS entries")

    # Player throw: shared anchor.
    m = must(r"PLAYER_THROW_SPEC = \{(.*?)\n\};", html, "PLAYER_THROW_SPEC", re.S)
    pt = m.group(1)
    pt_anchor = [int(v) for v in must(r"anchorX:\s*(\d+),\s*anchorY:\s*(\d+)", pt, "player anchor").groups()]
    pt_frames = {ph: re.findall(r"'(\w+\.png)'", must(ph + r":\s*\[(.*?)\]", pt, ph, re.S).group(1))
                 for ph in ("wind", "release", "recov")}

    # Miner skins: per-skin shared anchor + frame lists.
    m = must(r"const MINER_ANIM_SPEC = \{(.*?)\n\};", html, "MINER_ANIM_SPEC", re.S)
    miners = {}
    for skin, body in re.findall(r"\n  (\w+): \{(.*?)\n  \},", m.group(1), re.S):
        anchor = [int(v) for v in must(r"anchorX:\s*(\d+),\s*anchorY:\s*(\d+)", body, skin + " anchor").groups()]
        phases = {}
        for ph in ("walk", "stand", "wind", "release"):
            pm = re.search(r"\n\s*" + ph + r":\s*\[(.*?)\]", body, re.S)
            if pm:
                phases[ph] = re.findall(r"'(\w+\.png)'", pm.group(1))
        miners[skin] = {"anchor": anchor, "phases": phases}
    if len(miners) != 4:
        sys.exit(f"build_slots: expected 4 miner skins, found {list(miners)}")

    pier = [int(v) for v in must(r"const anchorX = (\d+), anchorY = (\d+);\s*\n\s*const scale = 0\.21", html, "pier anchor").groups()]
    tower = [int(v) for v in must(r"const anchorX = (\d+), anchorY = (\d+); // player's foot point", html, "tower anchor").groups()]
    spr = json.loads(must(r"const SPR_DATA = (\{.*?\});\n", html, "SPR_DATA").group(1))
    fish = spr["fishAtlas"]

    groups = {
        "backgrounds": {"mode": "background", "facing": None,
                        "notes": "Wave backgrounds, stretched to 400x240. Keep water line, banks and open sky where the current ones are. No people, no boats, no docks."},
        "player_aim": {"mode": "match", "ref": "assets/figure_level.png", "facing": "right",
                       "notes": "Six idle aim poses, spear angled from slightly up to steeply down. Drawn at fixed scale 34/390."},
        "player_throw": {"mode": "match", "ref": "assets/anim/player/wind1.png", "facing": "right",
                         "notes": "Wind-up, release and recovery of one spear throw at a shallow (~8 deg) downward angle. Fixed scale 0.196."},
        "miner_static": {"mode": "match", "facing": "left",
                         "notes": "One fallback pose per skin, only shown if the animation fails to load."},
        "props": {"mode": "match", "facing": None, "notes": "Pier and tower: feet/plank point must stay put."},
        "props_tiles": {"mode": "fit_bbox", "facing": None,
                        "notes": "Deck and trestle bay (tiled vertically) and the flying spear (rotated about its left end)."},
        "fish": {"mode": "atlas", "facing": "right",
                 "notes": "4 species x 8 swim frames in one sheet, all facing right, nose tip at the box's noseTip."},
        "legacy_bg": {"mode": "background", "facing": None, "notes": "Fallback-only scenery, never seen in practice."},
        "legacy_keep": {"mode": "keep", "facing": None, "notes": "Fallback-only sprite strips. Leave as is."},
    }

    slots = []

    def add(path, group, **extra):
        full = GAME / path
        arr = load_rgba(full)
        h, w = arr.shape[:2]
        row = {"path": path, "group": group, "width": w, "height": h,
               "alpha": not is_opaque(arr)}
        if not row["alpha"]:
            row["measure"] = None
        else:
            # Measured on the main subject only (same cleanup conform.py applies),
            # so a detached prop in today's art doesn't skew the feet point.
            row["measure"] = measure(cleanup(arr))
        row.update(extra)
        slots.append(row)

    for name in ["mountainvista", "rockycliff", "esmeralda", "pinegrove", "junctionbar"]:
        add(f"assets/bg_{name}.png", "backgrounds", game_scale=0.5)

    for path, angle, ax, ay in fig:
        add(path, "player_aim", anchor=[int(ax), int(ay)], aim_deg=int(angle), game_scale=round(34 / 390, 4))

    for ph in ("wind", "release", "recov"):
        for i, fn in enumerate(pt_frames[ph]):
            add(f"assets/anim/player/{fn}", "player_throw", anchor=pt_anchor, phase=ph, frame=i, game_scale=0.196)

    for skin, spec in miners.items():
        target_h = 56 if skin == "soldier" else 50
        g = f"miner_{skin}"
        groups[g] = {"mode": "match", "ref": f"assets/anim/{skin}/stand.png", "facing": "left",
                     "notes": f"{skin}: stand, wind-up and release of a throw, facing screen left. Projectile is drawn by the game, so nothing leaves the hand."}
        if "walk" in spec["phases"]:
            groups[g + "_walk"] = {"mode": "match", "ref": f"assets/anim/{skin}/walk1.png", "facing": "left",
                                   "notes": f"{skin}: 8-frame walk cycle toward screen left. Each frame tight-cropped, drawn bottom-centre."}
        for ph, files in spec["phases"].items():
            for i, fn in enumerate(files):
                path = f"assets/anim/{skin}/{fn}"
                arr_h = load_rgba(GAME / path).shape[0]
                if ph == "walk":
                    add(path, g + "_walk", phase=ph, frame=i, game_scale=round(target_h / arr_h, 4))
                else:
                    add(path, g, anchor=spec["anchor"], phase=ph, frame=i, game_scale=round(target_h / arr_h, 4))
        h = load_rgba(GAME / f"assets/{skin}.png").shape[0]
        add(f"assets/{skin}.png", "miner_static", game_scale=round(target_h / h, 4))

    add("assets/miner_pier.png", "props", anchor=pier, game_scale=0.21)
    add("assets/player_tower.png", "props", anchor=tower, game_scale=round((226 - 55) / (622 - tower[1]), 4))
    add("assets/sprites/deck.png", "props_tiles", game_scale=round(34 / 385, 4))
    add("assets/sprites/trestle.png", "props_tiles", game_scale=round(34 / 385, 4))
    grip = json.loads(must(r"const SPR_SPEAR_DATA = (\{.*?\});\n", html, "SPR_SPEAR_DATA").group(1))["spearAtlas"]["grip"]
    add("assets/sprites/spear.png", "props_tiles", anchor=[grip["x"], grip["y"]], game_scale=0.6)

    species = {k: {"frames": [[f["x"], f["y"], f["w"], f["h"]] for f in v["frames"]],
                   "noseTip": [v["noseTip"]["x"], v["noseTip"]["y"]]}
               for k, v in fish["sprites"].items()}
    add("assets/sprites/fish.png", "fish", species=species, game_scale=0.3)

    for name in ["sky", "pool", "scene"]:
        add(f"assets/sprites/{name}.png", "legacy_bg", game_scale=0.5)
    for name in ["fig", "miner", "cocked"]:
        add(f"assets/sprites/{name}.png", "legacy_keep", game_scale=0.3)

    # Preserve hand-filled fields.
    if SLOTS_FILE.exists():
        old = {s["path"]: s for s in json.loads(SLOTS_FILE.read_text(encoding="utf-8"))["slots"]}
        old_groups = json.loads(SLOTS_FILE.read_text(encoding="utf-8")).get("groups", {})
    else:
        old, old_groups = {}, {}
    for s in slots:
        prev = old.get(s["path"], {})
        for k in KEEP:
            s[k] = prev.get(k, "original" if k == "status" else ("" if k != "seed" else None))
    for g, info in groups.items():
        info["prompt"] = old_groups.get(g, {}).get("prompt", "")

    data = {
        "_about": "Generated by art/tools/build_slots.py from claimjumper/index.html and the current PNGs. "
                  "Edit prompt/seed/model/lora/license/status/notes freely; everything else is regenerated.",
        "style_anchor": STYLE_ANCHOR,
        "groups": groups,
        "slots": slots,
    }
    save_slots(data)
    print(f"wrote {SLOTS_FILE.relative_to(GAME.parent)}: {len(slots)} slots in {len(groups)} groups")


if __name__ == "__main__":
    main()
