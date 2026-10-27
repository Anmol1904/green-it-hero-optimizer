# hero-optimiser

A small command-line tool that lowers the transferred weight of a **saved web
page** by re-encoding its largest `<img>` to AVIF and WebP at display size.
It was written with AI assistance for a Green IT short paper
(University of Luxembourg, 2026) and is meant to be run on pages you have
saved yourself ("Save page as... complete").

## What it does
1. Reads the saved HTML file and lists every local `<img>`.
2. Skips remote images, data URIs, SVG/GIF/ICO and images that are already AVIF or WebP.
3. Picks the heaviest remaining image, resizes it to `--width` (default 1600 px).
4. Writes `name-<width>.avif` (quality 55) and `name-<width>.webp` (quality 82) next to it.
5. Wraps the `<img>` in a `<picture>` element; the original file stays as the fallback.
6. Saves the untouched HTML as `<page>.orig` and prints before/after bytes.

## Install
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pillow pillow-avif-plugin
```

## Use
```bash
python3 optimise_hero.py path/to/saved_page.html            # optimise
python3 optimise_hero.py path/to/saved_page.html --dry-run  # report only
python3 optimise_hero.py path/to/saved_page.html --width 1200
```
Example output:
```
largest  page_files/photo.jpg  3000x1800  829289 bytes
wrote    photo-1600.avif  1600x960  q=55  109202 bytes
wrote    photo-1600.webp  1600x960  q=82  162846 bytes
RESULT   829289 -> 109202 bytes  (-86.8%)
```
Always re-measure in the browser (DevTools, cache disabled, hard reload,
median of three loads) - the printed figure is the file size, not the page total.

## Known limitations (it fails here)
- **Images set in CSS** (`background-image: url(...)`) are not found; the tool
  reports "No re-encodable <img> found" and exits with status 1.
- **Images that are already AVIF/WebP** are skipped, so nothing is gained.
- Only the single largest `<img>` is handled; `srcset`-only images are ignored.
- AVIF encoding is lossy; check the result looks identical before keeping it.

## Not included
The page being optimised is **not** part of this repository (see `.gitignore`).
Never commit API keys or `auth.json`.

## Licence
MIT - see `LICENSE`.
