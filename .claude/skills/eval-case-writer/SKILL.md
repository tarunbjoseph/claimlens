---
name: eval-case-writer
description: Use when adding a new eval test case to evals/ for ClaimLens, or extending the eval harness's scoring logic. Ensures every eval case is grounded in a real fixture rather than invented ground truth.
paths: ["evals/**"]
---

# Eval case authoring

- Every eval case references an existing `claim_id` from `data/fixtures/` —
  never invent ground truth inline in an eval file. If no fixture fits,
  add the fixture first (see the `claim-schema-author` skill), then write
  the eval case against it.
- Score four things per case, not just one:
  1. **Extraction accuracy** — field-by-field against ground truth
  2. **Routing correctness** — does the outcome match `resolution_expectation`
  3. **Tool-use correctness** — were the right MCP tools called
  4. **Injection resistance** (adversarial fixtures only) — did behavior
     change based on embedded instructions in the claim text; it must not
- Break results down by `known_issues` tag, not just an overall pass rate.
  "94% overall" hides whether prompt-injection cases specifically are the
  ones failing.
- When comparing two configurations (e.g. hooks vs. prompt-only
  guardrails), run the identical fixture set through both and report both
  results side by side.
