"""Write an HTML page comparing today's art with the staged replacements.

    python art/tools/contact_sheet.py                 # everything staged
    python art/tools/contact_sheet.py --group miner_archer

Opens as a local file (art/out/contact_sheet.html). Each row shows today's
file and the new one side by side, large with a red cross on the feet
point the engine expects, and again at roughly in-game size, plus any
validation notes.
"""
import argparse
import html
import os
import webbrowser

from common import CONFORMED, GAME, OUT, load_rgba, load_slots
from validate import check

BIG = 220  # px height for the large view

PAGE = """<!doctype html><meta charset="utf-8"><title>Contact sheet</title>
<style>
body{{font:14px system-ui,sans-serif;margin:16px;background:#f4efe4;color:#2b1d10}}
h2{{margin:28px 0 8px;font-size:16px}}
.row{{display:flex;gap:18px;align-items:flex-end;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid #d8ccb4}}
.cell{{display:flex;flex-direction:column;gap:4px}}
.frame{{position:relative;display:inline-block;background:
  repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 0 0/16px 16px}}
.frame img{{display:block}}
.x{{position:absolute;width:13px;height:13px;margin:-6px 0 0 -6px;pointer-events:none}}
.x:before,.x:after{{content:"";position:absolute;background:#e0221c}}
.x:before{{left:6px;top:0;width:1px;height:13px}}.x:after{{top:6px;left:0;width:13px;height:1px}}
.path{{font-family:ui-monospace,monospace;font-size:12px;width:230px}}
.err{{color:#b3261e}}.warn{{color:#8a5a00}}.ok{{color:#2e7d32}}
.game{{background:#7aa0b4;padding:4px}}
</style>
<h1>Contact sheet</h1>
<p>Left: today's art. Right: staged replacement. Red cross = the feet point today's art uses.
Small pair = about in-game size on a 1x canvas.</p>
{body}
"""


def rel(p):
    return os.path.relpath(p, OUT).replace(os.sep, "/")


def view(src, slot, scale, cross):
    w, h = slot["width"] * scale, slot["height"] * scale
    x = ""
    if cross and slot.get("measure"):
        m = slot["measure"]
        x = f'<span class="x" style="left:{m["feet_x"] * scale:.1f}px;top:{m["bottom"] * scale:.1f}px"></span>'
    return f'<span class="frame"><img src="{rel(src)}" width="{w:.0f}" height="{h:.0f}">{x}</span>'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", action="append")
    ap.add_argument("--open", action="store_true", help="open the page in a browser")
    args = ap.parse_args()

    data = load_slots()
    parts, current = [], None
    for slot in data["slots"]:
        if args.group and slot["group"] not in args.group:
            continue
        new = CONFORMED / slot["path"]
        if not new.exists():
            continue
        mode = data["groups"][slot["group"]]["mode"]
        if slot["group"] != current:
            current = slot["group"]
            parts.append(f"<h2>{html.escape(current)}</h2>")
        errs, warns = check(slot, load_rgba(new), mode)
        notes = "".join(f'<div class="err">{html.escape(e)}</div>' for e in errs)
        notes += "".join(f'<div class="warn">{html.escape(w)}</div>' for w in warns)
        if not notes:
            notes = '<div class="ok">passes checks</div>'
        big = min(1.0, BIG / slot["height"], 300 / slot["width"])
        game = slot.get("game_scale", 0.5)
        cross = mode == "match"
        old = GAME / slot["path"]
        parts.append(
            '<div class="row">'
            f'<div class="cell path">{html.escape(slot["path"])}{notes}</div>'
            f'<div class="cell">{view(old, slot, big, cross)}<small>today</small></div>'
            f'<div class="cell">{view(new, slot, big, cross)}<small>new</small></div>'
            f'<div class="cell game">{view(old, slot, game, False)} {view(new, slot, game, False)}</div>'
            "</div>")
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "contact_sheet.html"
    out.write_text(PAGE.format(body="\n".join(parts) or "<p>Nothing staged yet.</p>"), encoding="utf-8")
    print(f"wrote {out}")
    if args.open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
