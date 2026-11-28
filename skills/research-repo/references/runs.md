# Runs and Research Logs

Use the project's runner and output format. For new workflows, use this layout for runs worth keeping.

```text
runs/<run_id>/
  run.json
  runner.log
  artifacts/             # Created when the run produces artifacts worth retaining
```

## Keep the run record small

| Path | Contents |
| --- | --- |
| `run.json` | Tested Git SHA, actual command, key conditions, and outcome or result link. The directory name can supply the run ID. |
| `runner.log` | Start and end, key phases, and enough warning or error context to troubleshoot. |
| `artifacts/` | Files used to reproduce a finding, compute a metric, or explain an outcome. Examples include training curves, metric data, predictions, traces, checkpoints, and recordings. |

- **Source and inputs.** Record the full Git SHA at launch. Add `+dirty` for a run that uses uncommitted changes and state any material limit on reproduction. Prefer a retrievable commit for new formal results. Save the actual CLI arguments and working directory when relevant. Record settings that affect the run and cannot be recovered from the command or commit, such as the seed, dataset snapshot, model revision, or runtime image. Mark unknown historical fields as unknown.
- **Results.** Put a small result in `run.json` or link to an existing report. For batch comparisons, keep enough per-case or per-seed data to recompute the core metrics. Use separate job outputs when needed for dispatch, resuming, or isolation.
- **Logs and files.** Keep useful messages once. Reference stable configs and archives to avoid duplicate files. Keep transient smoke output in the terminal unless it supports a finding.

## Run and compare experiments

1. **Choose the purpose and entry point.** A smoke run verifies a path. A diagnostic run investigates a behavior. A formal run follows the agreed protocol. Record the scope with the result.
2. **Set up the comparison.** Decide what changes and what stays fixed. Check the cases or split, versions, seeds, budgets, evaluator, and aggregation. Decide how to count timeouts, infrastructure errors, and missing cases before interpreting results. Use dry run when it helps check the plan.
3. **Save the launch plan and outcome.** Bind the run to the tested revision and inputs at launch. Keep enough of the batch plan to separate completed, unscored, and unstarted jobs. Record execution status separately from scores. If 20 cases were planned, 17 scored, and 12 succeeded, report the coverage as `17/20`, explain the three missing scores, and apply the protocol's denominator.
4. **Preserve earlier attempts.** Reuse a run ID only for safe continuation with matching saved inputs, protocol, and source. Use a new ID for a retry of a failed attempt or for a change in conditions that affects results. Link the original run where relevant and say which attempts the comparison uses.

## Training curves

Save the curves used to assess training in `artifacts/`.

- **`loss.png`.** Plot training and validation loss as separate series when both are measured.
- **`reward.png`.** Plot training episode return and evaluation return when available.
- **Other curves.** Plot metrics such as evaluation success rate when they inform the experiment.

Label axes and series. Use a common horizontal axis for curves compared in one figure, such as optimizer steps, tokens, or environment steps. Note any smoothing and keep the unsmoothed data. Reuse a stable runner or tracker export. When the original data is temporary, save a compact file such as `artifacts/metrics.csv` so the plots can be regenerated.

## Record the finding

Date each research log entry. Start with the observation and add the conditions, limits, and any decision or follow-up. Name each run with a repository-root-relative path, such as `runs/<run_id>/`. Group related runs in one entry. For Git-ignored runs, write local paths as code and add a stable archive link when available. Link a specific artifact when it supports the finding.

Use a separate report when the comparison needs more detail. Include the conditions, sample counts, outcomes, material limits, and run references. Keep historical findings tied to their original evidence and date any correction. Record routine changes and smoke checks in the usual review or test record.

## Worked example

Both runs in this example use the same cases and budget, with 12 successes out of 20. The files below are for the history-frame run.

```text
runs/20261127-history-frames/
  run.json
  runner.log
  artifacts/cases.csv
```

In `run.json`, the command and tested revision identify the config.

```json
{
  "source": {"git_commit": "0123456789abcdef0123456789abcdef01234567"},
  "command": [
    "python", "-m", "project.evaluate", "--config", "configs/history-frames.yaml",
    "--run-id", "20261127-history-frames"
  ],
  "status": "completed",
  "result": {"successes": 12, "scored": 20, "case_results": "artifacts/cases.csv"}
}
```

Example `runner.log`.

```text
2026-11-27T15:00:00Z INFO Started history-frame evaluation on 20 cases
2026-11-27T15:03:42Z INFO Completed 20 cases, 12 successes and 8 failures
```

First three rows of `artifacts/cases.csv`.

```csv
case_id,outcome
case-001,success
case-002,failure
case-003,success
```

Example entry in `docs/research-log.md`.

```markdown
## 2026-11-27 — History frames left the success count unchanged

Both versions succeeded on 12/20 cases under the same held-out protocol and budget.
This round covered one layout, so keep single-frame input for now and test a
second layout before drawing a broader conclusion.

- Baseline run `runs/20261127-single-frame/`
- History-frame run `runs/20261127-history-frames/`
- [Per-case comparison](results/20261127-history-frames.md)
```
