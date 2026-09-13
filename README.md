# houston-skills

Agent skills for research work, each packaged for both Claude Code and Codex.

```
<skill>/
  claude/    SKILL.md + scripts   — symlink into ~/.claude/skills/
  codex/     AGENTS.md + scripts  — point ~/.codex/AGENTS.md at it
sync.py      keeps the shared scripts in the two folders identical
```

The two folders hold the same scripts; only the instruction file differs, and
with it what each agent can actually do. Edit `claude/`, then run `./sync.py`.

## Skills

### exp-compare

Turns experiment output images into a comparison grid — rows = samples,
columns = methods — as one self-contained HTML file, published as an Artifact
or deployed to a Vercel site with a tab bar across several comparisons.

You explore the output directory and write a spec; the tools resolve paths,
re-encode to WebP, inline everything, and render. There is no directory
scanner and no path-pattern language, because every experiment is laid out
differently.

Needs Python with Pillow. The Vercel route also needs `npm i -g vercel` and a
token in `$VERCEL_TOKEN` or `~/.config/vercel-token`.

**Claude gets both routes; Codex only the Vercel one**, since it cannot publish
Artifacts.

## Install

```bash
git clone https://github.com/Djanghao/houston-skills ~/houston-skills

# Claude Code — available from any directory
ln -sfn ~/houston-skills/exp-compare/claude ~/.claude/skills/exp-compare

# Codex — add a pointer to the global instructions
echo 'For experiment image comparisons, follow
~/houston-skills/exp-compare/codex/AGENTS.md' >> ~/.codex/AGENTS.md
```
