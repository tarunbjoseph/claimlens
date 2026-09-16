"""Day 6-7 — context strategy: a persistent case-facts block plus
tool-output pruning, so a long-running case doesn't have to resend its
full history every turn.

Token counts use a per-character approximation (~3.44 chars/token)
rather than the real Claude tokenizer, which the Agent SDK doesn't
expose for arbitrary text outside an actual call. The ratio was
calibrated against real usage: two live Claude Code calls of very
different prompt lengths, taking the delta to isolate this project's
own content from the ~3,300-token fixed overhead every call carries
regardless of prompt size (tool definitions, base system prompt, etc.).
See docs/build-log.md, Day 6-7, for the two calibration numbers. What
this measures — the *relative* growth of naive vs. managed context
across a case's lifetime — only depends on the marginal rate, which
the delta captures correctly even though neither call's raw total is a
clean per-character count on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CHARS_PER_TOKEN = 3.44  # calibrated — see docs/build-log.md, Day 6-7


def count_tokens_approx(text: str) -> int:
    return round(len(text) / CHARS_PER_TOKEN)


@dataclass
class Turn:
    role: str  # "extraction" | "triage" | "tool_output" | "clarification"
    label: str  # short human label, e.g. "policy_lookup (simulated)"
    content: str


@dataclass
class CaseFactsBlock:
    """A compact, persistent summary of a case. Grows by folding in a
    one-line digest of each pruned turn — never by re-including a
    pruned turn's raw content, and never by dropping it silently
    either."""

    claim_id: str
    facts: list[str] = field(default_factory=list)

    def add(self, fact: str) -> None:
        self.facts.append(fact)

    def render(self) -> str:
        header = f"CASE FACTS — {self.claim_id}"
        if not self.facts:
            return header
        return header + "\n" + "\n".join(f"- {f}" for f in self.facts)


class ContextManager:
    """Keeps a case's context under a token budget by holding the most
    recent `keep_recent` turns verbatim and folding everything older
    into the case-facts block as a short digest, rather than resending
    the full raw history forever or dropping older turns outright.
    """

    def __init__(self, claim_id: str, token_budget: int, keep_recent: int = 4):
        self.case_facts = CaseFactsBlock(claim_id=claim_id)
        self.token_budget = token_budget
        self.keep_recent = keep_recent
        self.all_turns: list[Turn] = []  # full history — for the naive comparison only
        self.window: list[Turn] = []  # turns still kept verbatim in the managed view

    def add_turn(self, turn: Turn) -> None:
        self.all_turns.append(turn)
        self.window.append(turn)
        self._enforce_budget()

    def _enforce_budget(self) -> None:
        while (
            count_tokens_approx(self.render_managed()) > self.token_budget
            and len(self.window) > self.keep_recent
        ):
            oldest = self.window.pop(0)
            self.case_facts.add(self._digest(oldest))

    def _digest(self, turn: Turn) -> str:
        snippet = " ".join(turn.content.split())[:100]
        ellipsis = "…" if len(turn.content) > 100 else ""
        return f"{turn.label}: {snippet}{ellipsis}"

    def render_naive(self) -> str:
        """Every turn ever seen, resent in full — no management at all."""
        return "\n\n".join(f"[{t.label}]\n{t.content}" for t in self.all_turns)

    def render_managed(self) -> str:
        recent_text = "\n\n".join(f"[{t.label}]\n{t.content}" for t in self.window)
        return self.case_facts.render() + "\n\n" + recent_text
