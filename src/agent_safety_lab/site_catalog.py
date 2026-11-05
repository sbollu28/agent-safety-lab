"""Synthetic approved-flow catalog and per-site address resolver.

Original public demonstration. No production assets, credentials, or integrations.
"""
from __future__ import annotations
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Mapping


class CatalogError(ValueError):
    """A request cannot be resolved within approved scope."""


@dataclass(frozen=True)
class Flow:
    name: str
    source_key: str
    destination_key: str
    protocol: str
    port: int


@dataclass(frozen=True)
class ResolvedChange:
    site: str
    flow: str
    source: str
    destination: str
    protocol: str
    port: int


def resolve_change(
    *,
    site: str,
    flow_name: str,
    actor: str,
    site_entitlements: Mapping[str, frozenset[str]],
    approved_flows: Mapping[str, Flow],
    addresses: Mapping[str, Mapping[str, str]],
) -> ResolvedChange:
    """Allow only a cataloged flow for a site explicitly entitled to this actor.

    Note: The caller-supplied actor is for synthetic tests, NOT authentication.
    A real system must obtain identity and entitlements from trusted services.
    """
    if not isinstance(actor, str) or not isinstance(site, str) or not isinstance(flow_name, str):
        raise CatalogError("invalid_request")
    if site not in site_entitlements.get(actor, frozenset()):
        raise CatalogError("site_not_authorized")
    if flow_name not in approved_flows:
        raise CatalogError("flow_not_approved")
    if site not in addresses:
        raise CatalogError("site_not_found")
    flow = approved_flows[flow_name]
    if not isinstance(flow, Flow) or flow.protocol not in ("tcp", "udp") or type(flow.port) is not int or not 1 <= flow.port <= 65535:
        raise CatalogError("invalid_approved_flow")
    site_addresses = addresses[site]
    if not isinstance(site_addresses, Mapping):
        raise CatalogError("invalid_site_mapping")
    try:
        source = str(ip_address(site_addresses[flow.source_key]))
        destination = str(ip_address(site_addresses[flow.destination_key]))
    except (KeyError, ValueError, TypeError):
        raise CatalogError("unresolved_site_address") from None
    return ResolvedChange(site, flow_name, source, destination, flow.protocol, flow.port)


def render_set_command(change: ResolvedChange) -> str:
    """Generate a display-only illustrative configuration line; never execute it."""
    for part in (change.site, change.flow):
        if not part.replace("-", "").replace("_", "").isalnum() or not part:
            raise CatalogError("unsafe_identifier")
    return (
        f"set security policies from-zone TRUST to-zone UNTRUST policy "
        f"{change.flow}-{change.site} match source-address {change.source} "
        f"destination-address {change.destination}"
    )
