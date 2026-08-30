"""
Validates every claim_*.json in this directory against ../schema/claim_schema.json,
and cross-checks that a matching PDF exists for each one.

Usage:
    python validate_fixtures.py
Exits non-zero if anything fails, so this can be wired into CI later
(Week 2's secret-leak/CI gate step is the natural home for it).
"""

import json
import sys
from pathlib import Path
import jsonschema

HERE = Path(__file__).parent
SCHEMA_PATH = HERE.parent / "schema" / "claim_schema.json"


def main():
    schema = json.loads(SCHEMA_PATH.read_text())
    json_files = sorted(HERE.glob("*.json"))

    if not json_files:
        print("No fixture JSON files found.")
        sys.exit(1)

    failures = []
    tier_counts = {"clean": 0, "messy": 0, "adversarial": 0}

    for jf in json_files:
        data = json.loads(jf.read_text())
        claim_id = data.get("claim_id", jf.stem)

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            failures.append(f"{jf.name}: SCHEMA ERROR — {e.message}")
            continue

        pdf_path = HERE / f"{claim_id}.pdf"
        if not pdf_path.exists():
            failures.append(f"{jf.name}: no matching PDF found ({pdf_path.name})")

        # Rough tier classification from claim_id suffix convention (_c/_m/_x)
        if "_c" in claim_id:
            tier_counts["clean"] += 1
        elif "_m" in claim_id:
            tier_counts["messy"] += 1
        elif "_x" in claim_id:
            tier_counts["adversarial"] += 1

        # Sanity check: if line_items present, computed should equal their sum
        li = data.get("line_items")
        computed = data.get("claimed_amount_computed")
        if li and computed is not None:
            actual_sum = round(sum(item["amount"] for item in li), 2)
            if abs(actual_sum - computed) > 0.01:
                failures.append(
                    f"{jf.name}: claimed_amount_computed ({computed}) doesn't "
                    f"match sum of line_items ({actual_sum}) — fix the fixture itself"
                )

    print(f"Checked {len(json_files)} fixtures.")
    print(f"Tier distribution so far: {tier_counts}")

    if failures:
        print(f"\n{len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("All fixtures valid.")


if __name__ == "__main__":
    main()
