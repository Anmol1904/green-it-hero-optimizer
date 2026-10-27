#!/usr/bin/env python3
"""optimise_hero.py - re-encode the largest <img> of a SAVED web page.

Finds the heaviest local image referenced by an <img> tag in an HTML file,
resizes it to a display width, writes AVIF and WebP versions next to it,
rewrites the tag into a <picture> element (original kept as fallback) and
prints before/after byte counts. The original HTML is saved as <file>.orig.

Usage:  python3 optimise_hero.py PAGE.html [--width 1600] [--dry-run]
"""
import argparse
import os
import re
import shutil
import sys
from urllib.parse import unquote

from PIL import Image

try:
    import pillow_avif  # noqa: F401  (registers AVIF support)
except ImportError:
    sys.exit("Missing dependency: pip install pillow pillow-avif-plugin")

IMG_TAG = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC_ATTR = re.compile(r"""\bsrc\s*=\s*(["'])(.*?)\1""", re.I | re.S)
SKIP_EXT = {".avif", ".webp", ".svg", ".gif", ".ico"}


def find_candidates(html, base):
    """Return (size, tag, src, path) for every local, re-encodable <img>."""
    found, skipped = [], []
    for m in IMG_TAG.finditer(html):
        tag = m.group(0)
        s = SRC_ATTR.search(tag)
        if not s:
            continue
        src = s.group(2)
        if re.match(r"^(https?:)?//|^data:", src, re.I):
            skipped.append((src[:60], "remote or data URI"))
            continue
        path = os.path.join(base, unquote(src.split("?")[0]))
        ext = os.path.splitext(path)[1].lower()
        if ext in SKIP_EXT:
            skipped.append((src, "already a modern/vector format (%s)" % ext))
            continue
        if not os.path.isfile(path):
            skipped.append((src, "file not found on disk"))
            continue
        found.append((os.path.getsize(path), tag, src, path))
    return sorted(found, reverse=True), skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page", help="saved HTML file (its asset folder beside it)")
    ap.add_argument("--width", type=int, default=1600,
                    help="max width of the output image in px (default 1600)")
    ap.add_argument("--dry-run", action="store_true", help="report only")
    a = ap.parse_args()

    base = os.path.dirname(os.path.abspath(a.page))
    html = open(a.page, encoding="utf-8", errors="replace").read()
    found, skipped = find_candidates(html, base)

    for src, why in skipped:
        print("skipped  %-50s %s" % (src, why))
    if not found:
        print("No re-encodable <img> found. (Images set in CSS "
              "background-image are NOT handled.)")
        return 1

    size, tag, src, path = found[0]
    img = Image.open(path).convert("RGB")
    w0, h0 = img.size
    if w0 > a.width:
        img = img.resize((a.width, round(h0 * a.width / w0)), Image.LANCZOS)
    w1, h1 = img.size
    stem = os.path.splitext(path)[0]
    out = {"avif": (stem + "-%d.avif" % w1, 55),
           "webp": (stem + "-%d.webp" % w1, 82)}

    print("largest  %s  %dx%d  %d bytes" % (src, w0, h0, size))
    total_after = 0
    for fmt, (p, q) in out.items():
        if not a.dry_run:
            img.save(p, fmt.upper(), quality=q)
            n = os.path.getsize(p)
            total_after = n if fmt == "avif" else total_after
            print("wrote    %s  %dx%d  q=%d  %d bytes" %
                  (os.path.basename(p), w1, h1, q, n))
    if a.dry_run:
        print("dry run: nothing written")
        return 0

    rel = os.path.dirname(src)
    rel = rel + "/" if rel else ""
    pic = ('<picture>'
           '<source type="image/avif" srcset="%s%s">'
           '<source type="image/webp" srcset="%s%s">%s</picture>' % (
               rel, os.path.basename(out["avif"][0]),
               rel, os.path.basename(out["webp"][0]), tag))
    shutil.copyfile(a.page, a.page + ".orig")
    open(a.page, "w", encoding="utf-8").write(html.replace(tag, pic, 1))

    print("rewrote  %s  (backup: %s.orig)" % (a.page, os.path.basename(a.page)))
    print("RESULT   %d -> %d bytes  (-%.1f%%)  [AVIF served to supporting "
          "browsers; WebP/original as fallback]" %
          (size, total_after, 100 * (1 - total_after / size)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
