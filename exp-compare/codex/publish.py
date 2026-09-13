#!/usr/bin/env python3
"""Build a multi-page comparison site and (optionally) deploy it to Vercel.

Each page is a self-contained HTML file produced by pack.py, so the site is just
a folder of those files plus a tab shell that loads one at a time.

    # add or replace one comparison, then deploy
    publish.py spec.json --name v58-ablation --deploy

    # rebuild the index and deploy without adding anything
    publish.py --deploy

    # see what is in the site
    publish.py --list

The site folder is disposable — it is rebuilt from specs and should stay out of
git, which is what keeps multi-megabyte pages out of the repository's history.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHELL = HERE / "shell"
PACK = HERE / "pack.py"
TITLE_RX = re.compile(r"<title>(.*?)</title>", re.I | re.S)


def die(msg: str) -> None:
    print(f"publish: error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s).strip("-")
    return s or "page"


def page_title(f: Path) -> str:
    m = TITLE_RX.search(f.read_text(errors="replace")[:8192])
    return html.unescape(m.group(1).strip()) if m else f.stem


def rebuild(site: Path, site_title: str) -> dict:
    """Sync the shell into the site folder and regenerate pages.json."""
    site.mkdir(parents=True, exist_ok=True)
    (site / "pages").mkdir(exist_ok=True)
    for f in SHELL.iterdir():
        if f.is_file():
            shutil.copy2(f, site / f.name)

    pages = []
    for f in sorted((site / "pages").glob("*.html")):
        st = f.stat()
        pages.append({
            "id": f.stem,
            "file": f.name,
            "title": page_title(f),
            "date": dt.date.fromtimestamp(st.st_mtime).isoformat(),
            "mtime": st.st_mtime,
            "size": st.st_size,
        })
    pages.sort(key=lambda p: -p["mtime"])

    index = {
        "title": site_title,
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pages": [{k: v for k, v in p.items() if k != "mtime"} for p in pages],
    }
    (site / "pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n")
    return index


TOKEN_FILE = Path.home() / ".config" / "vercel-token"


def vercel_token() -> str | None:
    """$VERCEL_TOKEN, else ~/.config/vercel-token, else None (saved CLI login)."""
    tok = os.environ.get("VERCEL_TOKEN")
    if tok:
        return tok.strip()
    if TOKEN_FILE.is_file():
        return TOKEN_FILE.read_text().strip() or None
    return None


def deploy(site: Path, project: str) -> None:
    if not shutil.which("vercel"):
        die("the vercel CLI is not installed:  npm i -g vercel")

    # Keep credentials and link metadata out of the upload.
    ignore = site / ".vercelignore"
    if not ignore.exists():
        ignore.write_text(".vercel\n.env*\n")

    token = vercel_token()

    # Without this, a first deploy silently creates a project named after the
    # folder — "site" — instead of the one the user means.
    if not (site / ".vercel" / "project.json").is_file():
        link = ["vercel", "link", "--cwd", str(site), "--project", project, "--yes"]
        if token:
            link += ["--token", token]
        print(f"linking {site} to the Vercel project {project!r}")
        if subprocess.run(link, capture_output=True).returncode != 0:
            die(f"vercel link failed for project {project!r}")

    cmd = ["vercel", "deploy", str(site), "--prod", "--yes"]
    if token:
        cmd += ["--token", token]
    else:
        print("note: no VERCEL_TOKEN and no ~/.config/vercel-token — falling back\n"
              "      to the CLI's saved login, which will prompt if absent.",
              file=sys.stderr)
    print("$ " + " ".join("***" if c == token else c for c in cmd))
    if subprocess.run(cmd, capture_output=True).returncode != 0:
        die("vercel deploy failed — run the command above without -q to see why")

    name = None
    link = site / ".vercel" / "project.json"
    if link.is_file():
        name = json.loads(link.read_text()).get("projectName")
    print(f"deployed: https://{name}.vercel.app" if name else "deployed")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", type=Path, nargs="?", help="spec.json to pack into the site")
    p.add_argument("--name", help="page name / URL slug (default: the spec's filename)")
    p.add_argument("--site", type=Path, default=Path("site"), help="site folder (default: ./site)")
    p.add_argument("--site-title", default="Experiment Gallery")
    p.add_argument("--max-width", type=int, default=None,
                   help="override the spec's max_width")
    p.add_argument("--quality", type=int, default=None,
                   help="override the spec's quality")
    p.add_argument("--budget", type=float, default=None, metavar="MB",
                   help="max page size; a Vercel page is not bound by the "
                        "Artifact limit, but large pages load slowly")
    p.add_argument("--template", type=Path)
    p.add_argument("--deploy", action="store_true", help="push the site to Vercel")
    p.add_argument("--project", default=None,
                   help="Vercel project name, used the first time the site folder "
                        "is linked (default: the current directory's name)")
    p.add_argument("--list", action="store_true", help="list the pages in the site")
    p.add_argument("--rm", help="remove a page by name")
    a = p.parse_args()

    site = a.site

    if a.rm:
        f = site / "pages" / f"{slug(a.rm)}.html"
        if not f.exists():
            die(f"no such page: {f}")
        f.unlink()
        print(f"removed {f}")

    if a.spec:
        if not a.spec.exists():
            die(f"no such spec: {a.spec}")
        name = slug(a.name or a.spec.stem.replace(".spec", ""))
        out = site / "pages" / f"{name}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(PACK), str(a.spec), "-o", str(out)]
        if a.max_width is not None:
            cmd += ["--max-width", str(a.max_width)]
        if a.quality is not None:
            cmd += ["--quality", str(a.quality)]
        if a.budget is not None:
            cmd += ["--budget", str(a.budget)]
        if a.template:
            cmd += ["--template", str(a.template)]
        if subprocess.run(cmd).returncode != 0:
            die("pack failed")

    index = rebuild(site, a.site_title)

    if a.list or not (a.spec or a.deploy or a.rm):
        total = 0
        for pg in index["pages"]:
            total += pg["size"]
            print(f"  {pg['id']:<30} {pg['date']}  {pg['size']/1024/1024:>6.1f}MB  {pg['title']}")
        if not index["pages"]:
            print("  (no pages yet)")
        else:
            print(f"  {'':<30} {'':<10} {total/1024/1024:>7.1f}MB  total")

    if a.deploy:
        deploy(site, a.project or Path.cwd().name)


if __name__ == "__main__":
    main()
