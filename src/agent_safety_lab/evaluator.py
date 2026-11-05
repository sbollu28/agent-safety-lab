"""Offline guardrail for synthetic AI-proposed firewall changes.

Untrusted proposal text and fields never create authorization.
No network changes are performed.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Any, Mapping
import ipaddress
import re

ALLOWED_KEYS = frozenset({"action", "source", "destination", "port", "protocol", "ticket", "request_text"})
ACTIONS = frozenset({"allow", "deny"})
PROTOCOLS = frozenset({"tcp", "udp"})
APPROVAL_FIELDS = ("action", "source", "destination", "protocol", "port")


@dataclass(frozen=True)
class Decision:
    approved: bool
    reasons: tuple[str, ...]


def naive_keyword_baseline(proposal: Mapping[str, Any]) -> Decision:
    """Deliberately weak baseline, NOT a recommended security control."""
    text = str(proposal.get("request_text", "")).lower()
    if any(word in text for word in ("ignore previous", "bypass", "disable security", "any any")):
        return Decision(False, ("keyword_block",))
    return Decision(True, ("no_keyword_match",))


def _ip(value: Any) -> IPv4Address | None:
    if not isinstance(value, str):
        return None
    try:
        return ipaddress.IPv4Address(value)
    except (ipaddress.AddressValueError, ValueError):
        return None


def _trusted_policy(policy: Any) -> tuple[IPv4Network, IPv4Network, set[tuple[str, int]], Mapping[str, Mapping[str, Any]]] | None:
    """Validate the entire trusted policy before using any of it.

    A malformed policy must cause a denial, never an exception or a partial approval.
    """
    if not isinstance(policy, Mapping):
        return None
    try:
        source_cidr = policy["allowed_source_cidr"]
        destination_cidr = policy["allowed_destination_cidr"]
        raw_services = policy["permitted_services"]
        raw_approvals = policy["approvals"]
        if not isinstance(source_cidr, str) or not isinstance(destination_cidr, str):
            return None
        source_net = ipaddress.IPv4Network(source_cidr, strict=True)
        destination_net = ipaddress.IPv4Network(destination_cidr, strict=True)
        if not isinstance(raw_services, list) or not raw_services:
            return None
        services: set[tuple[str, int]] = set()
        for service in raw_services:
            if not isinstance(service, Mapping):
                return None
            proto, port = service.get("protocol"), service.get("port")
            if proto not in PROTOCOLS or type(port) is not int or not 1 <= port <= 65535:
                return None
            services.add((proto, port))
        if not isinstance(raw_approvals, Mapping):
            return None
        for ticket, approval in raw_approvals.items():
            if not isinstance(ticket, str) or not isinstance(approval, Mapping):
                return None
            if not all(field in approval for field in APPROVAL_FIELDS):
                return None
            if approval["action"] != "allow" or _ip(approval["source"]) is None or _ip(approval["destination"]) is None:
                return None
            if approval["protocol"] not in PROTOCOLS or type(approval["port"]) is not int or not 1 <= approval["port"] <= 65535:
                return None
    except (KeyError, ValueError, TypeError, AttributeError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        return None
    return source_net, destination_net, services, raw_approvals


def evaluate(proposal: Mapping[str, Any], policy: Mapping[str, Any]) -> Decision:
    """Fail closed: approval must match exact structured fields in trusted policy.

    This function is intentionally stateless. For one-use approvals, use the
    InMemoryApprovalGateway demo or a durable transactional approval service.
    """
    if not isinstance(proposal, Mapping):
        return Decision(False, ("invalid_proposal",))
    validated = _trusted_policy(policy)
    if validated is None:
        return Decision(False, ("invalid_trusted_policy",))
    src_net, dst_net, services, approvals = validated

    reasons: list[str] = []
    if set(proposal) - ALLOWED_KEYS:
        reasons.append("unexpected_fields")
    action = proposal.get("action")
    if not isinstance(action, str) or action not in ACTIONS:
        reasons.append("unsupported_action")
    if action != "allow":
        reasons.append("not_an_allow_request")
    source, destination = _ip(proposal.get("source")), _ip(proposal.get("destination"))
    if source is None or destination is None:
        reasons.append("invalid_ip")
    protocol, port = proposal.get("protocol"), proposal.get("port")
    if not isinstance(protocol, str) or protocol not in PROTOCOLS:
        reasons.append("invalid_protocol")
    if type(port) is not int or not (1 <= port <= 65535):
        reasons.append("invalid_port")
    if source is not None and source not in src_net:
        reasons.append("source_outside_scope")
    if destination is not None and destination not in dst_net:
        reasons.append("destination_outside_scope")
    if isinstance(protocol, str) and protocol in PROTOCOLS and type(port) is int and (protocol, port) not in services:
        reasons.append("service_not_permitted")
    ticket = proposal.get("ticket")
    if not isinstance(ticket, str) or re.fullmatch(r"CHG-[0-9]{4}", ticket) is None:
        reasons.append("invalid_ticket")
    elif ticket not in approvals:
        reasons.append("missing_approval")
    elif not all(
        type(approvals[ticket].get(k)) is type(proposal.get(k))
        and approvals[ticket].get(k) == proposal.get(k)
        for k in APPROVAL_FIELDS
    ):
        reasons.append("approval_scope_mismatch")
    return Decision(not reasons, tuple(reasons) if reasons else ("policy_and_approval_pass",))
