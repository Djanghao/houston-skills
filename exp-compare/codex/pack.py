#!/usr/bin/env python3
"""Pack a comparison spec into ONE self-contained HTML file.

Every image is re-encoded to WebP and inlined as a data URI, so the result is a
single file with no external assets — which is exactly what an Artifact publish
wants (a publish caps out at 255 separate files, and listing them costs tokens).

    pack.py spec.json -o out.html [--max-width 900] [--quality 85]

Spec:
    {
      "title":    "v58 icon ablation",
      "subtitle": "optional one-liner",            # optional
      "columns":  ["original", "baseline", "ours"],
      "max_width": 640,                            # optional, default 900
      "quality":   82,                             # optional, default 85
      "rows": [
        { "label":   "image_0008",
          "metrics": {"ssim": 0.862},              # optional -> enables sorting
          "cells": [
            "/abs/path/original.png",              # plain path
            {"src": "/abs/render.png", "note": "ssim 0.862"},   # path + caption
            null                                   # missing -> blank cell
          ] }
      ]
    }

Paths are resolved by whoever writes the spec, so any directory layout works.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).parent / "template.html"
BUDGET_MB = 14      # keeps clear of the 16MB Artifact page limit


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def die(msg: str) -> None:
    print(f"pack: error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def encode(path: Path, max_width: int, quality: int, cache: dict) -> str:
    """Re-encode to WebP and return a data URI. Identical paths are shared."""
    key = (str(path), max_width, quality)
    if key in cache:
        return cache[key]
    try:
        from PIL import Image
    except ImportError:
        die("Pillow is required: pip install pillow")
    from PIL import Image

    try:
        with Image.open(path) as im:
            im.load()
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.mode else "RGB")
            if max_width and im.width > max_width:
                im = im.resize((max_width, round(im.height * max_width / im.width)),
                               Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=quality, method=5)
    except Exception as e:                                   # noqa: BLE001
        die(f"cannot read image {path}: {e}")

    uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    cache[key] = uri
    return uri


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", type=Path)
    p.add_argument("-o", "--out", type=Path)
    p.add_argument("--max-width", type=int, default=None,
                   help="downscale wider images; overrides the spec's max_width "
                        "(default 900)")
    p.add_argument("--quality", type=int, default=None,
                   help="WebP quality; overrides the spec's quality (default 85)")
    p.add_argument("--template", type=Path, default=TEMPLATE,
                   help="custom page; must contain the marker /*__DATA__*/null")
    p.add_argument("--budget", type=float, default=BUDGET_MB, metavar="MB",
                   help=f"refuse to write a page bigger than this (default "
                        f"{BUDGET_MB}MB, sized for Artifacts). A Vercel-hosted "
                        f"page has no such limit, but large pages load slowly.")
    p.add_argument("--check", action="store_true",
                   help="validate the spec and report missing files, without "
                        "encoding images or writing output")
    a = p.parse_args()

    if not a.out and not a.check:
        die("-o/--out is required (or pass --check to only validate)")
    if not a.spec.exists():
        die(f"no such spec: {a.spec}")
    try:
        spec = json.loads(a.spec.read_text())
    except json.JSONDecodeError as e:
        die(f"{a.spec} is not valid JSON: {e}")

    cols = spec.get("columns")
    rows = spec.get("rows")
    if not cols or not rows:
        die("spec needs both 'columns' and 'rows'")

    # Resolution is the spec's call — it is written by whoever knows how dense
    # the images are and how many rows there will be. A flag still overrides.
    max_width = a.max_width if a.max_width is not None else int(spec.get("max_width", 900))
    quality = a.quality if a.quality is not None else int(spec.get("quality", 85))
    if max_width < 32:
        die(f"max_width must be at least 32, got {max_width}")
    if not 1 <= quality <= 100:
        die(f"quality must be between 1 and 100, got {quality}")

    cache: dict = {}
    out_rows = []
    gone: list[str] = []
    for i, row in enumerate(rows):
        label = str(row.get("label", i))
        cells = row.get("cells", [])
        if len(cells) != len(cols):
            die(f"row {i} ({label}) has {len(cells)} cells "
                f"but there are {len(cols)} columns")
        packed = []
        for ci, cell in enumerate(cells):
            if cell is None:
                packed.append(None)
                continue
            if isinstance(cell, str):
                cell = {"src": cell}
            if not isinstance(cell, dict) or "src" not in cell:
                die(f"row {label}, column {cols[ci]!r}: a cell must be a path "
                    f"string, an object with 'src', or null — got {cell!r}")
            src = Path(cell["src"]).expanduser()
            if not src.is_file():
                gone.append(f"{label} / {cols[ci]}: {src}")
                packed.append(None)
                continue
            packed.append({"u": "" if a.check
                                else encode(src, max_width, quality, cache),
                           "n": cell.get("note", "")})
        out_rows.append({"label": label,
                         "metrics": row.get("metrics") or {},
                         "cells": packed})

    n_img = sum(1 for r in out_rows for c in r["cells"] if c)
    if a.check:
        print(f"{a.spec}: {len(out_rows)} rows x {len(cols)} cols, "
              f"{n_img} images resolve, {len(gone)} missing")
        for g in gone[:20]:
            print(f"  missing  {g}")
        if len(gone) > 20:
            print(f"  ... and {len(gone) - 20} more")
        raise SystemExit(1 if gone else 0)

    data = {
        "title": spec.get("title", a.spec.stem),
        "subtitle": spec.get("subtitle", ""),
        "columns": cols,
        "rows": out_rows,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    html = a.template.read_text()
    marker = "/*__DATA__*/null"
    if marker not in html:
        die(f"{a.template} has no {marker} marker")
    # The <title> tag is what an Artifact publish reads as the page name, so it
    # has to carry the real title rather than a placeholder.
    html = html.replace("__TITLE__", esc(data["title"])).replace(marker, blob)
    size = len(html.encode())

    # Check before writing, so an over-budget page never lands on disk where
    # publish.py would deploy it.
    budget = int(a.budget * 1024 * 1024)
    if size > budget:
        over = size / 1024 / 1024
        fits = int(n_img * budget / size) if size else 0
        print(f"pack: error: the page would be {over:.1f}MB, over the {a.budget:g}MB "
              f"budget.\n"
              f"  {n_img} images at max_width {max_width} quality {quality}; "
              f"about {fits} of them would fit.\n"
              f"  Lower max_width (try {max(160, max_width // 2)}), drop quality "
              f"to 75, pack fewer rows, or raise --budget if this page is not "
              f"going to be an Artifact.", file=sys.stderr)
        raise SystemExit(2)

    a.out.write_text(html)
    print(f"{a.out}  {size / 1024 / 1024:.1f}MB  "
          f"{len(out_rows)} rows x {len(cols)} cols, {n_img} images"
          + (f", {len(cache)} unique" if len(cache) != n_img else ""))
    for g in gone[:10]:
        print(f"  missing  {g}")
    if len(gone) > 10:
        print(f"  ... and {len(gone) - 10} more missing")


if __name__ == "__main__":
    main()
