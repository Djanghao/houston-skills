---
name: research-repo
description: Set up and maintain computational research repositories. Use when organizing a research repo, running or auditing experiments, recording findings with run references, cleaning up research outputs, or presenting experiment results with Sites.
---

# Research Repositories

Keep each research result traceable to its evaluation protocol, run, tested revision, and supporting evidence.

## Start here

- **Existing repo.** Read the applicable `AGENTS.md`, README, and relevant code or docs. For experiments, find the normal entry point, an actual config, and a representative run. Follow the project's paths, output format, and validation commands.
- **New repo.** Start with the first runnable research workflow. Use the layout below as a guide and create the paths the project needs.
- **Run, audit, or record an experiment.** See [run records, training curves, and research logs](references/runs.md).
- **Prepare or publish a results Site.** See [presenting results with Sites](references/sites.md).

## Repository layout

```text
README.md                # Research question, quick start, primary results
AGENTS.md                # Project-specific Codex guidance
.gitignore
<dependency manifest and lockfile>
src/                     # Method, experiment runner, and evaluation code
tests/                   # Targeted tests and small fixtures
configs/                 # Reusable experiment settings and case lists
docs/
  methods.md             # Protocol, data splits, metrics, and budgets
  research-log.md        # Findings and decisions worth revisiting
  results/               # Formal reports and small result tables
runs/                    # Generated output, normally Git-ignored
```

In `AGENTS.md`, point to the protocol and results. Give the commands for common work and the checks for typical changes. Link details maintained elsewhere. Keep task-specific rules and results near the relevant tasks.

Keep reusable logic with the implementation and experiment settings in versioned configs. Use `scripts/` for maintained entry points such as data preparation, job dispatch, or export. Keep large datasets and checkpoints in the project's artifact storage. Document how to retrieve and use the version that affects execution.

## Write readable code

Write clean, clear, concise code that is easy to read and maintain.

- **Keep the implementation straightforward.** Use clear names and direct control flow. Prefer existing code and standard libraries. Add abstractions, options, or dependencies only when they solve a concrete need. Keep the code needed for correctness and supported edge cases.
- **Keep changes focused.** Match the surrounding style and preserve behavior outside the requested change. Remove code your change makes unused. Use comments and docstrings for rationale or contracts that are hard to see in the code.
- **Make experiment behavior easy to inspect.** Use the normal training or evaluation entry point and the project's config or CLI. Reuse parsing and scoring code. Make case selection, budgets, scoring, and aggregation explicit where they affect a comparison.

## Validate research changes

- Document diagnostic shortcuts that affect interpretation, such as shorter budgets, substituted inputs, or rescoring saved predictions.
- Keep method behavior, test data, and scoring separately identifiable. When the implementation or protocol changes, identify which results can still be compared, which can be rescored, and which need a rerun.
- Use focused checks for the behavior you changed. Run representative cases when correctness depends on the actual backend. Report what ran and limit conclusions to the protocol and coverage verified.

## Write readable docs

Write clean, clear, concise documentation that is easy to read.

- **Lead with what the reader needs.** Put the answer, purpose, or next action first. Use descriptive headings, short paragraphs, and numbered steps for procedures.
- **Give each detail one home.** Use the README to orient readers and get them started. Keep the current protocol, definitions, and setup in the relevant method or task docs. Link to the maintained explanation and remove stale or repeated text in the sections you update.
- **Make instructions usable.** Use the project's actual names, commands, and paths. Add a short working example when it helps. Check changed examples and links against the implementation. Update the affected guide when behavior, defaults, data, or budgets change.
- **Keep the evidence that matters.** Use the research log for findings and decisions worth revisiting, including informative negative results. Include the run directories. Use a separate report when the setup, results, or limits need more explanation.

## Repository hygiene

- Track source, configs, docs, small fixtures, and evidence needed to understand results. Ignore specific generated paths. Keep build output, caches, environments, and bulky artifacts in their designated locations.
- Before removing data or prototypes, check the owning worktree, Git status, and references. Archive unique evidence used by a report or Site before removing the local copy.
- Keep one usable record of each result. Reuse runner outputs and link to archived artifacts.

## Commits and PRs

Follow the project's commit convention. For new repos, Conventional Commits are a reasonable default, for example `fix(eval): record interrupted jobs`.

Group one logical change per commit with the relevant docs. Review staged paths and the diff. In a PR, describe the purpose, change, and checks run. In a results PR, link the run directories or archives and identify the actual tested revision separately from the report or merge commit.
