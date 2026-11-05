"""Offline sequential ticket-processing simulator.

Models stop-on-failure and a manual rollback artifact. Does not deploy,
operate a timer, call Jira/SharePoint, or touch any network device.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping

from .site_catalog import CatalogError, Flow, resolve_change


@dataclass(frozen=True)
class Ticket:
    id: str
    actor: str
    site: str
    flow: str


@dataclass(frozen=True)
class TicketResult:
    ticket: str
    state: str
    reason: str
    manual_rollback_artifact: str | None = None


def process_batch(
    tickets: Iterable[Ticket],
    *,
    site_entitlements: Mapping[str, frozenset[str]],
    approved_flows: Mapping[str, Flow],
    addresses: Mapping[str, Mapping[str, str]],
    simulated_failed_tickets: frozenset[str] = frozenset(),
) -> list[TicketResult]:
    """Stop processing after the first failed request; do NOT auto-rollback."""
    results: list[TicketResult] = []
    halted = False
    for ticket in tickets:
        if halted:
            results.append(TicketResult(ticket.id, "NOT_STARTED", "batch_halted"))
            continue
        try:
            change = resolve_change(
                site=ticket.site, flow_name=ticket.flow, actor=ticket.actor,
                site_entitlements=site_entitlements,
                approved_flows=approved_flows, addresses=addresses,
            )
        except CatalogError as exc:
            results.append(TicketResult(ticket.id, "BLOCKED", str(exc)))
            halted = True
            continue
        if ticket.id in simulated_failed_tickets:
            results.append(TicketResult(ticket.id, "FAILED", "simulated_deployment_failure"))
            halted = True
            continue
        # Illustrative artifact only: a proposed manual reversal, not a safe
        # vendor-specific rollback plan or an automatically executed operation.
        artifact = (
            f"REVIEW REQUIRED: reverse synthetic flow {change.flow} "
            f"at site {change.site}; verify current state before manual action"
        )
        results.append(TicketResult(ticket.id, "COMPLETED", "simulated_success", artifact))
    return results
