"""Pure-code check for silently "corrected" totals — no model call.

Compares the model's own extracted claimed_amount_stated against the sum of
its own extracted line_items. A mismatch is the correct, honest signal for
an inconsistent form (it should surface as clarify/escalate downstream, not
get silently resolved here). What this guards against is the model quietly
overwriting claimed_amount_stated to match its own arithmetic instead of
transcribing what the form actually says.
"""

from __future__ import annotations

from src.schemas.claim import ExtractedClaim


def validate_arithmetic(extracted: ExtractedClaim) -> dict:
    if not extracted.line_items:
        return {"computed_total": None, "arithmetic_mismatch": None}

    computed_total = round(sum(item.amount for item in extracted.line_items), 2)

    if extracted.claimed_amount_stated is None:
        mismatch = None
    else:
        mismatch = abs(computed_total - extracted.claimed_amount_stated) > 0.01

    return {"computed_total": computed_total, "arithmetic_mismatch": mismatch}
