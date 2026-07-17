# Trevor — Archive

A minimal, self-updating archive site. Hosted free on GitHub Pages.

## How to add a project

1. Duplicate `content/_example-project/` and rename the copy — the folder
   name becomes the project's URL slug (e.g. `content/1998-zine/`).
2. Drop in whatever files you want: `.md`, `.pdf`, `.docx`, `.doc`, `.mp3`,
   `.mp4`, `.heic`, `.jpg`, `.png` all work.
3. (Optional) Edit `project.json` inside the folder to set a title, date,
   and one-line description. If you skip it, the site just uses the folder
   name as the title.
4. Commit and push. That's it.

A GitHub Action rebuilds and redeploys the site automatically on every
push — usually live within a minute or two. You never touch HTML, CSS, or
the file list by hand.

## What happens automatically

- **HEIC photos** are converted to JPG for display (original HEIC stays
  downloadable).
- **.doc / .docx** files are converted to PDF for in-browser preview
  (original file stays downloadable).
- Markdown renders inline. PDFs, images, audio, and video all play/display
  directly on the page.
- Projects are sorted newest-first by `date`, or you can pin order manually
  with the `order` field in `project.json`.

## One-time setup

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages** and set **Source** to
   **GitHub Actions**.
3. Push once more (or re-run the workflow from the **Actions** tab) to
   trigger the first build.

## Local preview

No build step needed to just look at the site, but the manifest won't
reflect new files until you run the build script once:

```
pip install Pillow pillow-heif
python3 scripts/build_manifest.py
python3 -m http.server 8000
```

Then open `http://localhost:8000`. (DOC/DOCX conversion needs LibreOffice
installed locally too — `soffice` on the PATH — but this only matters for
local preview; GitHub's servers handle it automatically on push either
way.)

## Structure

```
content/<project-slug>/project.json   optional metadata
content/<project-slug>/*              your files
manifest.json                         generated — do not hand-edit
scripts/build_manifest.py             the converter/indexer
.github/workflows/build-content.yml   runs the script on every push
index.html / assets/                  the site itself
```
