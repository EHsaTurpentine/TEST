#!/usr/bin/env python3
"""
Walks /content, converts anything a browser can't render natively
(HEIC -> JPG, DOC/DOCX -> PDF), and writes /manifest.json describing
every project and file so the front end never has to guess.

Run by .github/workflows/build-content.yml on every push to main.
Safe to run locally too: `python3 scripts/build_manifest.py`
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
MANIFEST_PATH = ROOT / "manifest.json"

# Extension -> renderer type the front end knows how to display
TYPE_MAP = {
    ".md": "markdown", ".markdown": "markdown",
    ".pdf": "pdf",
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
    ".mp4": "video", ".mov": "video", ".webm": "video",
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".gif": "image", ".webp": "image",
}
HEIC_EXT = {".heic", ".heif"}
DOC_EXT = {".doc", ".docx"}
SKIP_NAMES = {"project.json", ".ds_store"}


def convert_heic(path: Path) -> Path | None:
    """HEIC/HEIF -> JPG via pillow-heif. Returns new path or None on failure."""
    try:
        from PIL import Image
        import pillow_heif
        pillow_heif.register_heif_opener()
        out = path.with_suffix(".jpg")
        Image.open(path).convert("RGB").save(out, "JPEG", quality=90)
        return out
    except Exception as e:
        print(f"  ! HEIC conversion failed for {path.name}: {e}", file=sys.stderr)
        return None


def convert_doc(path: Path) -> Path | None:
    """DOC/DOCX -> PDF via headless LibreOffice. Returns new path or None on failure."""
    out = path.with_suffix(".pdf")
    try:
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf",
             "--outdir", str(path.parent), str(path)],
            check=True, capture_output=True, timeout=120,
        )
        return out if out.exists() else None
    except Exception as e:
        print(f"  ! DOC conversion failed for {path.name}: {e}", file=sys.stderr)
        return None


def build_project(project_dir: Path) -> dict:
    meta_path = project_dir / "project.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    files = []
    for f in sorted(project_dir.iterdir()):
        if f.is_dir() or f.name.lower() in SKIP_NAMES or f.name.startswith("."):
            continue
        ext = f.suffix.lower()

        # Skip files that are themselves conversion output from a prior run
        # (we regenerate every run, so drop stale .jpg/.pdf siblings of a
        # HEIC/DOC source before re-walking — handled in main()).

        display_path = f
        original_name = None

        if ext in HEIC_EXT:
            converted = convert_heic(f)
            if converted:
                display_path = converted
                original_name = f.name
            else:
                continue  # can't display, skip rather than break the build
        elif ext in DOC_EXT:
            converted = convert_doc(f)
            if converted:
                display_path = converted
                original_name = f.name
            else:
                continue

        rtype = TYPE_MAP.get(display_path.suffix.lower())
        if rtype is None:
            rtype = "download"  # unknown format: still linkable, no inline preview

        entry = {
            "name": f.stem.replace("_", " ").replace("-", " "),
            "path": str(display_path.relative_to(ROOT)),
            "type": rtype,
        }
        if original_name:
            entry["original"] = str(f.relative_to(ROOT))
            entry["originalName"] = original_name
        files.append(entry)

    return {
        "slug": project_dir.name,
        "title": meta.get("title", project_dir.name.replace("-", " ").replace("_", " ").title()),
        "date": meta.get("date", ""),
        "description": meta.get("description", ""),
        "order": meta.get("order"),
        "files": files,
    }


def clean_stale_conversions():
    """Remove previously generated .jpg/.pdf siblings so re-running is idempotent."""
    if not CONTENT.exists():
        return
    for project_dir in CONTENT.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("_"):
            continue
        for f in list(project_dir.iterdir()):
            if f.suffix.lower() in HEIC_EXT:
                stale = f.with_suffix(".jpg")
                if stale.exists():
                    stale.unlink()
            if f.suffix.lower() in DOC_EXT:
                stale = f.with_suffix(".pdf")
                if stale.exists():
                    stale.unlink()


def main():
    if not CONTENT.exists():
        print("No content/ directory found — nothing to build.")
        MANIFEST_PATH.write_text(json.dumps({"projects": []}, indent=2))
        return

    clean_stale_conversions()

    projects = []
    for project_dir in sorted(CONTENT.iterdir()):
        if project_dir.is_dir() and not project_dir.name.startswith("_"):
            print(f"Building project: {project_dir.name}")
            projects.append(build_project(project_dir))

    # Sort: explicit "order" first, then by date (newest first), then title
    projects.sort(key=lambda p: (
        p["order"] if p["order"] is not None else 9999,
        p["date"] and f"~{p['date']}" or "",
    ), reverse=False)
    # newest-first for date when no explicit order given
    dated = [p for p in projects if p["order"] is None]
    dated.sort(key=lambda p: p["date"], reverse=True)
    ordered = [p for p in projects if p["order"] is not None]
    ordered.sort(key=lambda p: p["order"])
    projects = ordered + dated

    MANIFEST_PATH.write_text(json.dumps({"projects": projects}, indent=2))
    print(f"\nWrote manifest.json with {len(projects)} project(s).")


if __name__ == "__main__":
    main()
