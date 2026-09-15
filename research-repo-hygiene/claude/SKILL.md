---
name: research-repo-hygiene
description: Set up or maintain the structure of a research/experiment repository — what docs/ must contain, which pages are living, when an experiment earns its own branch, and what to archive versus delete when a direction is abandoned. Use when starting a new experiment repo, when asked to "整理项目结构"/"优化文档"/"tidy up the repo"/"写个 docs 路由", when outputs/ or scratch directories have accumulated, when an investigation is being closed out, or when a session cannot tell what has already been tried.
---

# Research repo hygiene

An experiment repo accumulates two things faster than code: output nobody will
read again, and knowledge that exists only in a conversation.

## The layout

```text
README.md              what this is, quickstart, and a pointer to docs/README.md
CLAUDE.md  AGENTS.md   conventions for agents; both point at docs/README.md
PROJECT_LOG.md         every run that informed a decision, newest first
docs/
  README.md            routing by situation, and which pages are living
  ENVIRONMENT.md       interpreter, dependencies, what is already running
  WORKFLOW.md          when to branch, what to log, what to archive
  BRANCHES.md          what each branch holds and concluded
  COMMAND.md           every entry point: flags, defaults, exit codes
  <service>.md         pinned versions, restart, inspect
<package>/             the library — importable, no CLI, no hard-coded paths
scripts/               CLI entry points, one docs/commands/ page each
tests/
configs/               the production config, exactly one of it on main
.env.example           tracked: every variable name, no values
.gitignore
```

Never tracked, and they differ in kind:

| | |
|---|---|
| `data/` | inputs. Rebuildable by downloading again. |
| `outputs/` | runs. **Disposable** once archived to a branch. |
| the raw request log | what was actually sent to an external service. **Permanent** — nothing recomputes it. |
| `.env` | secrets. `.env.example` carries the names. |
| `tmp/` | scratch scripts and one-off results. Ignore the **whole** directory, not half of it, or its scripts sit untracked in a shared tree. |

The split that matters is the last column: one scratch directory is safe to
delete, one is not, and the difference is whether a command rebuilds it.

**Ask where a one-off script should live before writing it.** Scratch that turns
out to matter is worth `scripts/` with a flag and a page; scratch that stays
scratch belongs in `tmp/`. Guessing wrong in either direction is expensive — a
throwaway in `scripts/` accrues documentation it does not deserve, and something
load-bearing in `tmp/` is untracked when it matters.

## The invariant

**`main` carries what ships. Anything being measured lives on a branch.**

| `main` | branch |
|---|---|
| the production config, exactly one of it | variants, candidates, ablation arms |
| library, scripts, docs | apparatus built for one investigation |
| `PROJECT_LOG.md` | generated runs, scores, reports |

An abandoned direction stays on its branch — the next person can see it was
tried, and the tree does not carry it.

## `docs/`

One page per fact, as laid out above. Two lists of the same thing drift within a
week — including the two router pages you will be tempted to write.

### Route by situation

A new session does not know your filenames. The first table is a decision table:
*new session* → ENVIRONMENT, *about to run a script* → its page, *about to try an
idea* → `PROJECT_LOG.md`, *about to measure* → WORKFLOW, *investigation ended* → WORKFLOW,
*looking for prior work* → BRANCHES.

### Mark the living pages

Readers trust a stale page until it burns them. State each refresh trigger: the
log on every run that informed a decision; `COMMAND.md` in the **same commit** as the flag; ENVIRONMENT when the machine changes; BRANCHES when one opens or
closes.

### Say what to do

| Instead of | Write |
|---|---|
| never delete the request log | the request log is permanent |
| do not spend paid calls unasked | ask before spending paid calls |
| the package is not installed | run from the repository root |
| the default interpreter fails | *(name the environment that has the deps)* |

Negation is fine for what the *system* does — "the logger never stores a whole
key" — not for telling the reader to refrain.

## Command pages are what make a run reproducible

An experiment is identified by its **invocation**, not its output directory. The
same script under two settings is two experiments; later, the command is the
only thing that distinguishes them.

- **Everything is a flag** — paths, inputs, models, thresholds. A constant at
  the top of a script cannot be replayed: the value that produced last month's
  numbers is gone. This is also what stops `run_v2_final.py` from existing.
- **A new flag is documented in the same commit as the code.** Otherwise the
  page is wrong exactly when someone reads it to replay a run.
- **Record the invocation twice**: in the log entry, and in a manifest the run
  writes itself carrying arguments, config hash and service versions. The
  manifest says what produced a run; the log says why those arguments.
- **For a comparison, copy the previous invocation from the log and change one
  flag.** The comparison is only as good as the guarantee nothing else moved. A
  silently different flag is how two arms stop being comparable.

Each entry point's section carries: every flag with its default, behaviour a
table cannot hold (resume semantics, path resolution order, flag interactions),
output layout, exit codes. One file until it stops being navigable — a directory
of pages costs you a second index that drifts against the first.

## Branching

Work on `main` for a change you would keep whatever the outcome — a bug fix, a
doc, a flag. Branch as soon as you are **measuring**:

```bash
git worktree add -b experiments/<question>-<date> <path> main
```

A worktree, not a checkout: `main` keeps its working tree and other sessions are
undisturbed. Name it after the question, not the method, and fold related
attempts into one branch.

## Closing a direction

1. **Archive what no command rebuilds** — per sample: the artifact, the raw
   response, the exact input, the scores, the run metadata; per run: manifest and
   summary; plus any config variant a run cites by hash.
2. **Leave out what a command rebuilds** — rendered images, deterministic derived
   datasets, per-sample copies of a versioned config. Getting this line right is
   usually two orders of magnitude of branch size.
3. **Verify the round trip before deleting.** Restore one run, regenerate, check
   the scores match. They should be identical; a difference means the archive is
   incomplete or a service changed.
4. **Then clear the scratch directory.**
5. **Write the closing entry**: what was measured, what was decided, which branch
   holds the rest.

The raw request log is never cleared — nothing recomputes what was sent.

## `PROJECT_LOG.md`

Terse, newest first, every number also in a results file on disk. The log points
at evidence; it does not replace it. It records progress as well as findings —
what landed and when, not only what was measured.

- **Log every experiment that finished, including failures.** A rejected
  approach is most of the log's value: it stops the next session repeating a
  week. A run abandoned mid-flight is scratch and stays out.
- **Record the exact command**, paths and all — the replay starts there.
- **When later evidence contradicts an entry, correct it in place and say so.**
  An entry carrying its own retraction is the log working.
- Record the decision, not only the numbers.

## Committing

Commit as you go and keep the tree clean — an uncommitted working directory is
indistinguishable from an abandoned one, and in a shared checkout another
session cannot tell your edits from its own.

Set the author once per repo so every commit carries the same identity:

```bash
git config user.name  "<name>"
git config user.email "<email>"
```

## Keeping it honest

- Check every internal link after editing docs.
- Fact-check against the machine, not memory: test counts, service versions,
  sample counts, files per branch. All of these drift.
- Grep for stale names after a rename — docstrings outlive code.
- **Watch for read-only paths.** A fallback reading a file or key the repo never
  writes is dead code; if it is the *only* path, the feature has never worked.
