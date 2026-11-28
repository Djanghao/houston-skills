# Results Sites

For a requested results Site, load `sites:sites` in Codex. Follow the requested
delivery scope and preserve the Site and its audience when updating it.

## Prepare the evidence

- **Trace the results.** Check each value against its run record, results file,
  evaluation protocol, and resolved inputs.
- **Version the export.** Record the research revision, run IDs, protocol version,
  and evidence references. Use the existing aggregation command for repeated or
  derived results and keep the command and inputs. For a small one-off export,
  check copied values against their summaries. Store the export with the Site
  source or at a versioned location the Site can read.
- **Link the evidence.** For Git-ignored runs, keep the workspace path and link a
  versioned archive or released summary when readers need access. For restricted
  evidence, identify the authorized source and give readers an appropriate
  summary. Include only files and fields approved for the audience.

## Display the comparison

- Show the fraction beside the percentage, as in `12/20 (60%)`. Link the
  protocol and show the case set, budget, metric, model or system versions,
  and other conditions that affect interpretation.
- For incomplete results, show coverage and apply the protocol's denominator
  rule. Give counts for measured failures, infrastructure errors, timeouts, and
  missing or unrun cases as applicable.
- Label diagnostic results and explain the conditions and limits of any
  cross-protocol comparison. Link evidence from each table or figure. Label
  recordings and replays by their provenance.

## Verify and record delivery

Check representative rendered values, denominators, statuses, and links against
the export and underlying evidence. When possible, verify that the intended
audience can open the report and its evidence.

Record the results ID, research revisions, and run references. For a hosted
release, also record the Site source commit, saved version or deployment ID as
available, and deployed URL. Report which delivery steps were verified, from
local generation through save, deployment, and audience access.

## Example export

These fictitious runs share a revision, held-out case set, budget, and success
rule. When revisions differ, record the tested revision per row.

```json
{
  "results_id": "20261127-frame-history-v1",
  "research_revision": "0123456789abcdef0123456789abcdef01234567",
  "protocol": "held-out-v1",
  "case_set": "holdout-v1",
  "budget": {"max_steps_per_case": 150},
  "metric": "successful cases / scored cases",
  "rows": [
    {
      "label": "Single frame",
      "run": "runs/20261127-single-frame/run.json",
      "planned": 20,
      "scored": 20,
      "successes": 12
    },
    {
      "label": "History frames",
      "run": "runs/20261127-history-frames/run.json",
      "planned": 20,
      "scored": 20,
      "successes": 12
    }
  ]
}
```
