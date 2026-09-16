---
name: review
description: Read-only review of recent changes against ClaimLens's core principles. Never writes or edits files — findings are reported, not fixed. Use before committing, or invoke explicitly with /review.
disallowed-tools: Write, Edit, NotebookEdit
---

# /review — read-only

Review the current diff (`git diff` and `git diff --staged`) against these
checks. Report findings; do not fix them — this skill has no write access,
so it physically cannot.

1. **Null-over-guess** — does any extraction code path fill a missing field
   with a plausible-looking default instead of `null`?
2. **Hooks not weakened** — do `PreToolUse`/`PostToolUse` hooks still
   hard-block the behavior they're meant to block, or has a check been
   loosened or removed to make a test pass?
3. **Untrusted claim content** — is text extracted from a claim document
   ever concatenated into a prompt in a way that could be interpreted as
   an instruction, rather than treated as data?
4. **Fixture integrity** — if `data/` changed, was `validate_fixtures.py`
   run, and did it pass?
5. **Ground truth discipline** — was any `ground_truth` JSON edited to
   match a model's output rather than the other way around?

End with a short pass/fail summary per check.
