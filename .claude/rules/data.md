# Rules for data/

- `data/schema/claim_schema.json` is the single source of truth. Every
  fixture must validate against it.
- New fixtures: `ground_truth` is written first; `form_text` is derived
  from it (see `fixtures/generate_pdf.py` for the pattern). Never write
  `form_text` first and back a `ground_truth` into it — the eval harness
  needs an answer key that exists independently of anything a model
  produced.
- Adversarial fixtures should isolate a single `known_issues` signal unless
  explicitly building a stacked case. `auto_x001` stacks all three signals
  on purpose as the obvious/centerpiece case; `auto_x002`, `prop_x002`, and
  `auto_x003` each isolate one signal — follow that pattern for new ones.
- Always rerun `validate_fixtures.py` before committing changes here. It
  checks schema validity, confirms every fixture has a matching PDF, and
  verifies `claimed_amount_computed` actually equals the sum of that
  fixture's own `line_items`.
