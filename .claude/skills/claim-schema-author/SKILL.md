---
name: claim-schema-author
description: Use when adding a new claim type, a new field to claim_schema.json, or generating new synthetic claim fixtures (PDF + ground truth JSON pairs) for ClaimLens. Ensures new fixtures follow the established schema-first pattern and known_issues taxonomy rather than drifting from it.
paths: ["data/**"]
---

# Claim schema & fixture authoring

Follow this order. Don't skip a step or reorder it — the sequence is what
keeps 40+ fixtures internally consistent as the set grows.

1. If adding a new field or claim type, update `data/schema/claim_schema.json`
   first. Every fixture must validate against the current schema.
2. Write `ground_truth` as a plain dict — the answer key, decided
   independently of any model output.
3. Derive `form_text` from the ground truth. Clean fixtures match exactly.
   Messy fixtures should have real gaps that `ground_truth` mirrors with
   `null` — never fill a gap with a guess in either direction. Adversarial
   fixtures may diverge on purpose (see `claimed_amount_stated` vs.
   `claimed_amount_computed`, or a `date_reported` that precedes
   `incident_date`).
4. Tag `known_issues` honestly from the fixed enum: `missing_field`,
   `arithmetic_mismatch`, `contradictory_dates`, `illegible_scan`,
   `prompt_injection_attempt`, or `none`. Isolate signals rather than
   stacking every tag on every hard case, unless deliberately building a
   stacked case (see `auto_x001` vs. `auto_x002`/`prop_x002`/`auto_x003`).
5. Append the new scenario dict to `SCENARIOS` (or `ADDITIONAL_SCENARIOS`)
   in `fixtures/generate_pdf.py`. Don't touch `render_pdf` or `main` unless
   the form layout itself needs to change.
6. Run `python fixtures/generate_pdf.py` then `python fixtures/validate_fixtures.py`.
   Both must succeed.
7. Spot-check at least one rendered PDF per batch by eye
   (`pdftoppm -jpeg -r 100 <id>.pdf preview`, then view the image) — schema
   validity doesn't catch content that drifted from what was intended.
