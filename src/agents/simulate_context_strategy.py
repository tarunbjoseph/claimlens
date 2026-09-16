"""Day 6-7 — proves the context manager actually bounds growth, using a
simulated 30-turn case lifecycle built from real fixture data (so turn
sizes are representative, not invented) plus placeholder tool-output
turns standing in for Week 2's not-yet-built policy-mcp calls — those
are clearly labeled "(simulated)", not presented as live data.

Usage:
    python -m src.agents.simulate_context_strategy
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.context_manager import ContextManager, Turn, count_tokens_approx

REPO_ROOT = Path(__file__).parent.parent.parent
EXTRACTIONS_DIR = REPO_ROOT / "data" / "extractions"
TRIAGE_DIR = REPO_ROOT / "data" / "triage"
OUT_PATH = REPO_ROOT / "data" / "context_strategy_results.json"

TOKEN_BUDGET = 1400
KEEP_RECENT = 4


def build_simulated_case(claim_id: str = "auto_c001") -> list[Turn]:
    """A 30-turn simulated lifecycle for one claim: the real extraction
    result, then a repeating mix of real triage output and
    representative (simulated) tool-output turns of similar size and
    shape to what Week 2's policy-mcp will return — standing in for a
    case that gets re-touched (re-scored, re-checked) several times
    over its life, which is when unmanaged context actually becomes a
    problem.
    """
    extraction = (EXTRACTIONS_DIR / f"{claim_id}.json").read_text()
    triage = (TRIAGE_DIR / f"{claim_id}.json").read_text()

    simulated_policy_lookup = json.dumps(
        {
            "policy_id": "POL-448291",
            "status": "active",
            "coverage_limit": 25000,
            "deductible": 500,
            "prior_claims_last_3y": 1,
            "underwriter_notes": "Standard auto policy, no endorsements, good payment history.",
        },
        indent=2,
    )
    simulated_claims_history = json.dumps(
        {
            "policy_id": "POL-448291",
            "prior_claims": [
                {
                    "claim_id": "auto_c001-prior-1",
                    "date": "2025-02-11",
                    "type": "auto",
                    "amount": 890.0,
                    "status": "closed_paid",
                }
            ],
        },
        indent=2,
    )
    simulated_fraud_signal = json.dumps(
        {"policy_id": "POL-448291", "fraud_score": 0.04, "flags": [], "model_version": "sim-fraud-v0"},
        indent=2,
    )

    turns = [Turn(role="extraction", label="extract_claim", content=extraction)]
    pool = [
        Turn(role="tool_output", label="policy_lookup (simulated)", content=simulated_policy_lookup),
        Turn(role="tool_output", label="claims_history (simulated)", content=simulated_claims_history),
        Turn(role="tool_output", label="fraud_signals (simulated)", content=simulated_fraud_signal),
        Turn(role="triage", label="triage_decision", content=triage),
    ]
    i = 0
    while len(turns) < 30:
        turns.append(pool[i % len(pool)])
        i += 1
    return turns[:30]


def main() -> None:
    turns = build_simulated_case()
    cm = ContextManager(claim_id="auto_c001", token_budget=TOKEN_BUDGET, keep_recent=KEEP_RECENT)

    rows = []
    for n, turn in enumerate(turns, start=1):
        cm.add_turn(turn)
        rows.append(
            {
                "turn": n,
                "naive_tokens": count_tokens_approx(cm.render_naive()),
                "managed_tokens": count_tokens_approx(cm.render_managed()),
            }
        )

    print(f"{'turn':>4} {'naive':>10} {'managed':>10}")
    for r in rows:
        print(f"{r['turn']:>4} {r['naive_tokens']:>10} {r['managed_tokens']:>10}")

    final = rows[-1]
    savings_pct = 100 * (1 - final["managed_tokens"] / final["naive_tokens"])
    print(
        f"\nAt turn 30: naive={final['naive_tokens']} tokens, "
        f"managed={final['managed_tokens']} tokens ({savings_pct:.0f}% smaller)"
    )

    OUT_PATH.write_text(
        json.dumps(
            {
                "chars_per_token_calibration": {
                    "method": "delta between two live Claude Code calls of very different prompt lengths",
                    "point_1": {"chars": 2065, "input_tokens": 3971},
                    "point_2": {"chars": 2, "input_tokens": 3372},
                    "derived_chars_per_token": round((2065 - 2) / (3971 - 3372), 3),
                },
                "token_budget": TOKEN_BUDGET,
                "keep_recent_turns": KEEP_RECENT,
                "rows": rows,
                "final_savings_pct": round(savings_pct, 1),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
