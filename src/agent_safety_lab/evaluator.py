"""Offline guardrail for synthetic AI-proposed firewall changes.
Untrusted proposal text and fields never create authorization.
No network changes are performed.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import ipaddress
import re

ALLOWED_KEYS = frozenset({"action", "source", "destination", "port", "protocol", "ticket", "request_text"})
ACTIONS = frozenset({"allow", "deny"})
PROTOCOLS = frozenset({"tcp", "udp"})

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

def _ip(value: Any):
    try:
        return ipaddress.IPv4Address(value) if isinstance(value, str) else None
    except ipaddress.AddressValueError:
        return None

def evaluate(proposal: Mapping[str, Any], policy: Mapping[str, Any]) -> Decision:
    """Fail closed; an approval must be independently recorded and match the exact action."""
    if not isinstance(proposal, Mapping):
        return Decision(False, ("invalid_proposal",))
    reasons = []
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
    try:
        src_net = ipaddress.IPv4Network(policy["allowed_source_cidr"], strict=True)
        dst_net = ipaddress.IPv4Network(policy["allowed_destination_cidr"], strict=True)
        services = {(x["protocol"], x["port"]) for x in policy["permitted_services"]}
        approvals = policy["approvals"]
    except (KeyError, ValueError, TypeError):
        return Decision(False, ("invalid_trusted_policy",))
    if source is not None and source not in src_net:
        reasons.append("source_outside_scope")
    if destination is not None and destination not in dst_net:
        reasons.append("destination_outside_scope")
    if isinstance(protocol, str) and protocol in PROTOCOLS and type(port) is int and (protocol, port) not in services:
        reasons.append("service_not_permitted")
    ticket = proposal.get("ticket")
    if not isinstance(ticket, str) or re.fullmatch(r"CHG-[0-9]{4}", ticket) is None:
        reasons.append("invalid_ticket")
    elif ticket not in approvals or not isinstance(approvals[ticket], dict):
        reasons.append("missing_approval")
    else:
        required = ("action", "source", "destination", "protocol", "port")
        if not all(approvals[ticket].get(k) == proposal.get(k) for k in required):
            reasons.append("approval_scope_mismatch")
    return Decision(not reasons, tuple(reasons) if reasons else ("policy_and_approval_pass",))
