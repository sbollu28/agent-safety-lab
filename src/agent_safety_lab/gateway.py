"""Single-process demonstration of one-use approval consumption.

This is NOT a distributed authorization service. State is lost on restart.
A production gateway requires durable atomic consumption, authenticated
principals, expiry, asset/diff binding, and an independent approval provider.
"""
from __future__ import annotations

from threading import Lock
from typing import Any, Mapping

from .evaluator import Decision, evaluate


class InMemoryApprovalGateway:
    def __init__(self) -> None:
        self._lock = Lock()
        self._consumed: set[str] = set()

    def authorize_once(self, proposal: Mapping[str, Any], policy: Mapping[str, Any]) -> Decision:
        """Atomically evaluate and consume a synthetic ticket within this process."""
        with self._lock:
            decision = evaluate(proposal, policy)
            if not decision.approved:
                return decision
            ticket = proposal["ticket"]
            if ticket in self._consumed:
                return Decision(False, ("approval_already_consumed",))
            self._consumed.add(ticket)
            return decision
