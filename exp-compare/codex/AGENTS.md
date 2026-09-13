# exp-compare — experiment image comparison (Codex version)

**Use this whenever the user wants to look at, compare, or share experiment
result images** — "对比一下这几个 run 的渲染图", "把 v58 的结果做成网页看看",
"show me original vs rendered for these samples", "生成结果对比", "看看哪个
variant 更好".

It turns experiment output images into a grid — **rows = samples, columns =
methods/runs** — as one self-contained HTML file, and deploys it to a Vercel
site where several comparisons sit behind a tab bar.

**You write a spec, the tools render it.** Every experiment lays its output out
differently, so there is no scanner and no path-pattern language: explore the
directory with `ls`/`find`/`glob`, work out where each image is, and write the
spec. `pack.py` only resolves paths, re-encodes images, and renders — all the
judgement lives in the spec you write.

## Flow

1. **Explore.** Find where each (sample, method) image lives, and where
   per-sample metrics live (`metrics.json`, `samples.jsonl`, `summary.csv`, …).

   Keep it cheap: `find <dir> -name '*.png' | head`, then counts — never list
   thousands of paths into context, and never open the images one at a time.

2. **Write the spec** (format below). For more than a handful of rows, generate
   it with a short Python script — that script is also where selection logic
   goes. Choosing *which* samples make the comparison convincing is the part
   that needs judgement; don't just take the first N.

3. **Check** — cheap, no image encoding:

   ```bash
   python3 pack.py spec.json --check
   ```

4. **Publish:**

   ```bash
   python3 publish.py spec.json --name v58-ablation --deploy
   ```

   Print the resulting URL for the user.

## Spec format

```json
{
  "title":    "v58 icon ablation",
  "subtitle": "optional one-liner shown under the title",
  "columns":  ["原图", "v53_baseline", "d_v1_sizing"],
  "max_width": 640,
  "quality":   82,
  "rows": [
    {
      "label":   "image_0008",
      "metrics": { "ssim": 0.862 },
      "cells": [
        "/abs/path/image_0008/original.png",
        { "src": "/abs/path/v53_baseline/image_0008/06_render/rendered.png",
          "note": "ssim 0.791" },
        null
      ]
    }
  ]
}
```

| field | required | meaning |
|---|---|---|
| `title` | yes | becomes the page `<title>` and its tab label |
| `subtitle` | no | one line under the title |
| `columns` | yes | column headers, left to right |
| `max_width` | no | downscale images wider than this (default 900) |
| `quality` | no | WebP quality 1–100 (default 85) |
| `rows[].label` | yes | the row header — usually the sample id |
| `rows[].cells` | yes | **exactly one entry per column**, in column order |
| `rows[].metrics` | no | `{name: number}`; supplying it turns on a sort dropdown |

A cell is one of:

- `"path/to.png"` — a plain path
- `{"src": "path/to.png", "note": "ssim 0.791"}` — `note` prints under that image
- `null` — an empty cell, for a method that produced nothing for that sample

Rules that matter:

- **Paths are yours to resolve.** Absolute paths are safest. Any directory
  layout works because the tool never guesses.
- **`note` is per image**, so put *that method's* score for *that sample* in it.
  A grid without notes is just pictures; with them it is evidence.
- **`metrics` is per row** — use it for the one number worth ranking by, so the
  user can sort the worst cases to the top.
- Every row needs the same number of cells as there are columns. `pack.py`
  refuses the spec otherwise and names the offending row.

## Publishing

```bash
python3 publish.py spec.json --name v58-ablation --deploy
python3 publish.py --list             # what's in the site
python3 publish.py --rm old-page --deploy
```

This packs into `site/pages/<name>.html`, syncs the tab shell, regenerates
`site/pages.json`, and runs `vercel deploy --prod`. The shell loads a page only
when its tab is opened, so unopened tabs cost nothing.

The first `--deploy` from a fresh `site/` links it to a Vercel project named
after the current directory; pass `--project <name>` to choose. Once linked,
the name is remembered in `site/.vercel/`.

Needs the Vercel CLI (`npm i -g vercel`) and a token, taken from
`$VERCEL_TOKEN` or `~/.config/vercel-token`; with neither, the CLI falls back to
its saved login and will prompt — which will hang a non-interactive run, so
check for a token first. `publish.py` writes a `.vercelignore` so the link
metadata and `.env.local` that Vercel drops into the folder are never uploaded.

**Keep `site/` out of git** — that is what stops multi-megabyte pages
accumulating in the repository's history.

If the user instead wants a quick private link that does not need a deploy,
that is Claude Code's Artifact route (`claude/` in this repo). Codex cannot
publish Artifacts; say so rather than trying.

## Capacity — set `max_width` deliberately

Images are inlined as base64 (×1.33), so a page's size is set by how many
images you pack and how big you let them be. `pack.py` refuses to write past
`--budget` (default 14MB) and says how many images would have fit.

**Resolution is a judgement call, and it belongs in the spec.** You know how
dense the images are and how many rows there will be; pick `max_width` from
that rather than leaving it to the default.

Measured on dense UI screenshots (~840×630 widget renders):

| `max_width` | per image | fits in 14MB | legibility |
|---|---|---|---|
| 1200 q85 | 24.5KB | ~580 | full detail |
| 900 q85 | 21.8KB | ~660 | clear |
| **640 q85** | **17.4KB** | **~830** | **still evaluable — good default ceiling** |
| 480 q85 | 13.2KB | ~1,080 | small text getting hard |
| 320 q85 | 8.7KB | ~1,650 | layout only |
| 200 q72 | 3.8KB | ~3,600 | useless |

**Content density changes these numbers by 2× or more.** Simple flat widgets
run ~10KB at full size; dense screenshots with lots of text run ~22KB at 900px.
Check with `--check`, then pack — don't trust the table alone.

The 14MB default is sized for Artifacts, and a Vercel-hosted page is not bound
by it — `--budget 40` will happily write a 30MB page. But the browser downloads
the whole page up front, so raise it only when the extra rows earn the wait.

The real ceiling is not the byte budget, it is legibility: shrinking images
until 3,000 of them fit produces a page nobody can evaluate. Prefer fewer,
readable rows — select the samples that make the point instead of packing
everything.

## Custom layouts

The default page — sortable, filterable, paginated, with a lightbox where
`←/→` switch column and `↑/↓` switch row — covers the usual comparison. For
anything else (trajectories, figure-and-text, grouped sections) write your own
page and pass `--template mine.html`. It needs only the marker
`/*__DATA__*/null`, which is replaced by:

```js
{ title, subtitle, columns: [...],
  rows: [{ label, metrics, cells: [{u, n} | null] }] }   // u = data URI, n = note
```
