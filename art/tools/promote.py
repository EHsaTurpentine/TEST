"""Move conformed art into the game, or build a playable preview copy.

    python art/tools/promote.py --preview
        Copies claimjumper/ to art/out/preview/ with every staged file
        swapped in, then you play it locally:
            cd art/out/preview && python -m http.server 8000
            open http://localhost:8000/claimjumper/

    python art/tools/promote.py --group backgrounds
        Validates the staged files for that group, copies them into
        claimjumper/assets/, and marks them "approved" in slots.json.
        Refuses if validation finds errors (override with --force).
        Do this on a branch; main deploys straight to GitHub Pages.
"""
import argparse
import shutil
import sys

from common import CONFORMED, GAME, OUT, REPO, load_rgba, load_slots, save_slots
from validate import check


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true", help="build art/out/preview instead of changing the game")
    ap.add_argument("--group", action="append", help="groups to promote (repeatable)")
    ap.add_argument("--all", action="store_true", help="promote every staged file")
    ap.add_argument("--force", action="store_true", help="promote even if validation reports errors")
    args = ap.parse_args()

    data = load_slots()
    staged = [s for s in data["slots"]
              if (CONFORMED / s["path"]).exists()
              and (args.preview or args.all or (args.group and s["group"] in args.group))]

    if args.preview:
        root = OUT / "preview"
        if root.exists():
            shutil.rmtree(root)
        dest = root / "claimjumper"
        shutil.copytree(GAME, dest)
        shutil.copytree(REPO / "engine", root / "engine")  # the game imports ../engine/
        for s in staged:
            shutil.copy2(CONFORMED / s["path"], dest / s["path"])
        print(f"preview with {len(staged)} new file(s): {dest}")
        print(f"  cd {root} && python -m http.server 8000   then open http://localhost:8000/claimjumper/")
        return

    if not (args.all or args.group):
        sys.exit("say which art to promote: --group NAME (repeatable), --all, or use --preview")
    if not staged:
        sys.exit("nothing staged for that selection; run conform.py first")

    bad = 0
    for s in staged:
        errs, _ = check(s, load_rgba(CONFORMED / s["path"]), data["groups"][s["group"]]["mode"])
        for e in errs:
            print(f"ERROR {s['path']}: {e}")
        bad += bool(errs)
    if bad and not args.force:
        sys.exit(f"{bad} file(s) failed validation; nothing copied. Fix them or pass --force.")

    for s in staged:
        shutil.copy2(CONFORMED / s["path"], GAME / s["path"])
        s["status"] = "approved"
    save_slots(data)
    print(f"promoted {len(staged)} file(s) into claimjumper/ and marked them approved in slots.json")


if __name__ == "__main__":
    main()
