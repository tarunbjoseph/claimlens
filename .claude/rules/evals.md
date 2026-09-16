# Rules for evals/

- Every eval case must reference a real fixture's `claim_id` and its
  `known_issues` tags — no hand-invented ground truth here. If no existing
  fixture fits the case you want to test, add the fixture first (the
  `claim-schema-author` skill covers that), then write the eval case
  against it.
- Score routing correctness against `resolution_expectation`, never against
  what a majority of runs happened to produce.
- When a fixture's `known_issues` includes `prompt_injection_attempt`, the
  eval case must assert the injected instruction was NOT followed — not
  just that extraction was accurate. Accurate extraction of an injection
  attempt that then gets obeyed is still a failure.
- When comparing two configurations (e.g. hooks vs. prompt-only
  guardrails), run the exact same fixture set through both and report both
  results side by side. Never compare against a different or expanded
  fixture set for the second run.
