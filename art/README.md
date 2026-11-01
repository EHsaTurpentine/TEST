# CLAIMJUMPER! art pipeline

Tools for replacing the game's art with new, locally generated art
without touching `claimjumper/index.html`. The rule is simple: a new file
must have the same path, the same pixel size, and the character's feet on
the same pixel as today's file. These scripts do that fitting for you and
check it before anything reaches the game.

Plan and background: [CLAIMJUMPER! local art pipeline plan](https://claude.ai/artifact/NVCAzqaFP5gWWgtg4KsKt6).

## Setup (once, on either machine)

```
py -m pip install -r art/requirements.txt      # Windows
python3 -m pip install -r art/requirements.txt # Mac/Linux
```

Run every command from the repo root (the folder that holds `claimjumper/`
and `art/`). On Windows use `py` where these examples say `python`.

## The loop

1. **Generate** images in Forge (or WanGP for animation) and save the one
   you want under `art/staging/raw/`, using the slot's own path:
   `art/staging/raw/assets/anim/soldier/wind3.png`,
   `art/staging/raw/assets/bg_pinegrove.png`, and so on.
   Any size is fine. Characters and props either come already cut out
   (transparent PNG from BiRefNet or rembg) or on a **flat** background
   colour, ideally pure green `#00B140` or flat grey, with no shadow,
   floor, dock or checkerboard.
2. **Conform:** `python art/tools/conform.py`
   Cuts out, cleans up, scales and places everything in
   `art/staging/raw/` into `art/staging/conformed/`.
3. **Check:** `python art/tools/validate.py` and
   `python art/tools/contact_sheet.py --open` (today's art next to the new
   art, with a red cross on the feet point).
4. **Play it:** `python art/tools/promote.py --preview`, then
   `cd art/out/preview && python -m http.server 8000` and open
   <http://localhost:8000/claimjumper/>. This is a copy; the real game is
   untouched.
5. **Promote** when you like it, on a branch:
   `python art/tools/promote.py --group backgrounds`
   Copies the files into `claimjumper/assets/` and marks them `approved`
   in `slots.json`. Refuses if validation fails. Merging to `main`
   publishes to GitHub Pages, so check the preview first.

`art/staging/` and `art/out/` are not committed. Only the tools,
`slots.json` and approved art in `claimjumper/` are.

## Try it with placeholders first

```
python art/tools/placeholders.py   # fake raw images: flat silhouettes on green, oversized
python art/tools/conform.py
python art/tools/validate.py
python art/tools/promote.py --preview
```

Every character becomes a flat-coloured silhouette standing exactly where
today's art stands. If that plays correctly, the pipeline works on your
machine. Delete `art/staging/` afterwards.

## slots.json

One row per art file the game loads (121 rows, 16 groups). Built by
`python art/tools/build_slots.py` from `index.html` and today's PNGs.
Re-running it keeps anything filled in by hand.

Fields you (or a local LLM) fill in: `prompt`, `negative`, `seed`,
`model`, `lora`, `license`, `status`, `notes`, plus a `prompt` per group.
`style_anchor` at the top is the shared style text every prompt starts
with. Everything else is measured and gets overwritten:

| Field | Meaning |
| --- | --- |
| `width`, `height` | Exact canvas size the file must have |
| `alpha` | Needs transparency (characters, props) or not (backgrounds) |
| `measure.bbox` | Where today's subject sits in the canvas |
| `measure.bottom`, `measure.feet_x` | Today's feet point; new art is placed to match |
| `anchor` | The engine's own anchor numbers, for reference |
| `game_scale` | Roughly how much the game shrinks the file on screen |
| `phase`, `frame` | Animation phase and frame number |

Groups and what conform does with them:

| Mode | Groups | What happens |
| --- | --- | --- |
| `background` | backgrounds, legacy_bg | Scaled to cover the canvas, centre-cropped, saved opaque. Generate at 1344x768 in Flux |
| `match` | player_aim, player_throw, miner_*, miner_static, props | Cut out, keep the main subject, scale to today's height, feet on today's feet point. Animation groups use **one** scale for all frames, taken from the group's `ref` frame, so stage that frame too |
| `fit_bbox` | props_tiles (deck, trestle, spear) | Scaled to fit today's subject box and centred in it |
| `atlas` | fish | Frames go in `art/staging/raw/assets/sprites/fish/<species>/0.png` to `7.png`; each is fitted into its atlas box with the nose on the nose point. Species you don't supply keep today's art |
| `keep` | legacy_keep | Left alone (fallback-only strips) |

## Generation rules that save cleanup time

These come from problems the Firefly art already hit (see `claimjumper/DESIGN.md`):

- Miners face **screen left**; the player and fish face **screen right**.
- Nothing under the feet: no dock, plank, floor or shadow.
- Thrown objects leave the hand cleanly, with no glow or motion trail.
  `conform.py` drops small detached pieces (under 15% of the body; change
  with `--keep-ratio`), so a released rock simply disappears.
- Animation frames come from one clip with a locked camera, and every
  frame of a group goes through `conform.py` in the same run.
- Don't put green things on a green screen. Use grey (`--key 128,128,128`)
  or cut out with BiRefNet first.

## Useful options

```
python art/tools/conform.py --group miner_archer       # one group only
python art/tools/conform.py --key 0,177,64 --tol 60     # force key colour / looser key
python art/tools/conform.py --keep-ratio 1              # keep only the biggest piece
python art/tools/validate.py --game                     # check the live game files
```
