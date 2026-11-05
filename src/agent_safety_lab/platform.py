"""Runnable *synthetic* network-policy automation platform.

SQLite source of truth, ticket workflow, site-specific address resolution,
policy catalog, simulated configuration state and manual rollback.
No network connections, secrets, real RBAC authentication, or employer code.
"""
from __future__ import annotations

import ipaddress
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


class WorkflowError(ValueError):
    """A change violates a validation or workflow rule."""


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
    name TEXT PRIMARY KEY, role TEXT NOT NULL CHECK (role IN ('requester','engineer'))
);
CREATE TABLE IF NOT EXISTS sites (
    name TEXT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS entitlements (
    user TEXT NOT NULL REFERENCES users(name),
    site TEXT NOT NULL REFERENCES sites(name),
    PRIMARY KEY (user, site)
);
CREATE TABLE IF NOT EXISTS addresses (
    site TEXT NOT NULL REFERENCES sites(name),
    object TEXT NOT NULL,
    ip TEXT NOT NULL,
    PRIMARY KEY (site, object)
);
CREATE TABLE IF NOT EXISTS flows (
    name TEXT PRIMARY KEY, src_object TEXT NOT NULL, dst_object TEXT NOT NULL,
    protocol TEXT NOT NULL CHECK (protocol IN ('tcp','udp')),
    port INTEGER NOT NULL CHECK (port BETWEEN 1 AND 65535),
    approved_by TEXT NOT NULL REFERENCES users(name)
);
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY, requester TEXT NOT NULL REFERENCES users(name),
    site TEXT NOT NULL, flow TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN
      ('OPEN','IN_PROGRESS','BLOCKED','FAILED','CLOSED','ROLLED_BACK')),
    reason TEXT NOT NULL DEFAULT '', change_key TEXT, previous TEXT,
    desired TEXT, rollback_note TEXT
);
CREATE TABLE IF NOT EXISTS deployed (
    change_key TEXT PRIMARY KEY, desired TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket TEXT, event TEXT NOT NULL, detail TEXT NOT NULL,
    at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""


def _name(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,47}", value) is None:
        raise WorkflowError("invalid_identifier")
    return value


def _ipv4(value: str) -> str:
    try:
        return str(ipaddress.IPv4Address(value))
    except (ipaddress.AddressValueError, TypeError, ValueError):
        raise WorkflowError("invalid_ipv4_address") from None


class PolicyPlatform:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db = sqlite3.connect(str(db_path), timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def _audit(self, ticket: str | None, event: str, detail: str) -> None:
        self.db.execute(
            "INSERT INTO audit(ticket,event,detail) VALUES (?,?,?)",
            (ticket, event, detail),
        )

    def _require_engineer(self, actor: str) -> None:
        row = self.db.execute("SELECT role FROM users WHERE name=?", (actor,)).fetchone()
        if row is None or row["role"] != "engineer":
            raise WorkflowError("engineer_role_required")

    def add_user(self, name: str, role: str) -> None:
        _name(name)
        if role not in ("requester", "engineer"):
            raise WorkflowError("unsupported_role")
        with self.db:
            self.db.execute("INSERT INTO users VALUES (?,?)", (name, role))
            self._audit(None, "user_added", name)

    def onboard_site(self, actor: str, site: str, objects: dict[str, str]) -> None:
        self._require_engineer(actor)
        _name(site)
        if not isinstance(objects, dict) or not objects:
            raise WorkflowError("empty_site_mapping")
        normalized = {_name(k): _ipv4(v) for k, v in objects.items()}
        with self.db:
            self.db.execute("INSERT INTO sites VALUES (?)", (site,))
            self.db.executemany(
                "INSERT INTO addresses(site,object,ip) VALUES (?,?,?)",
                [(site, key, value) for key, value in normalized.items()],
            )
            self._audit(None, "site_onboarded", site)

    def grant_site(self, engineer: str, user: str, site: str) -> None:
        self._require_engineer(engineer)
        with self.db:
            self.db.execute("INSERT INTO entitlements VALUES (?,?)", (user, site))
            self._audit(None, "site_entitlement_granted", f"{user}:{site}")

    def approve_flow(
        self, engineer: str, name: str, source: str, destination: str,
        protocol: str, port: int,
    ) -> None:
        self._require_engineer(engineer)
        for value in (name, source, destination):
            _name(value)
        if protocol not in ("tcp", "udp") or type(port) is not int or not 1 <= port <= 65535:
            raise WorkflowError("invalid_service")
        with self.db:
            self.db.execute(
                "INSERT INTO flows VALUES (?,?,?,?,?,?)",
                (name, source, destination, protocol, port, engineer),
            )
            self._audit(None, "flow_approved", name)

    def submit(self, ticket: str, requester: str, site: str, flow: str) -> None:
        _name(ticket)
        _name(site)
        _name(flow)
        row = self.db.execute("SELECT role FROM users WHERE name=?", (requester,)).fetchone()
        if row is None:
            raise WorkflowError("unknown_requester")
        with self.db:
            self.db.execute(
                "INSERT INTO tickets(id,requester,site,flow,state) VALUES (?,?,?,?, 'OPEN')",
                (ticket, requester, site, flow),
            )
            self._audit(ticket, "submitted", f"{site}:{flow}")

    def _resolve(self, ticket: sqlite3.Row) -> tuple[str, dict[str, Any]]:
        entitled = self.db.execute(
            "SELECT 1 FROM entitlements WHERE user=? AND site=?",
            (ticket["requester"], ticket["site"]),
        ).fetchone()
        if entitled is None:
            raise WorkflowError("site_not_authorized")
        flow = self.db.execute(
            "SELECT * FROM flows WHERE name=?", (ticket["flow"],)
        ).fetchone()
        if flow is None:
            raise WorkflowError("flow_not_approved")
        addresses = dict(self.db.execute(
            "SELECT object,ip FROM addresses WHERE site=?", (ticket["site"],)
        ).fetchall())
        try:
            source = _ipv4(addresses[flow["src_object"]])
            destination = _ipv4(addresses[flow["dst_object"]])
        except KeyError:
            raise WorkflowError("unresolved_site_address") from None
        change_key = f"{ticket['site']}:{ticket['flow']}"
        return change_key, {
            "site": ticket["site"], "flow": ticket["flow"],
            "source": source, "destination": destination,
            "protocol": flow["protocol"], "port": flow["port"],
        }

    def run_once(self, fail_ticket: str | None = None) -> list[dict[str, str]]:
        """Process a snapshot of OPEN tickets. Stop on first blocked/failed change.

        A separate caller schedules this function; no embedded hourly timer.
        No rollback is ever automatically invoked.
        """
        outcomes: list[dict[str, str]] = []
        ids = [r["id"] for r in self.db.execute(
            "SELECT id FROM tickets WHERE state='OPEN' ORDER BY rowid"
        )]
        for ticket_id in ids:
            with self.db:
                ticket = self.db.execute(
                    "SELECT * FROM tickets WHERE id=? AND state='OPEN'", (ticket_id,)
                ).fetchone()
                if ticket is None:
                    continue
                self.db.execute(
                    "UPDATE tickets SET state='IN_PROGRESS' WHERE id=?", (ticket_id,)
                )
                self._audit(ticket_id, "in_progress", "mock_pipeline_claim")
                try:
                    key, desired = self._resolve(ticket)
                except WorkflowError as exc:
                    self.db.execute(
                        "UPDATE tickets SET state='BLOCKED',reason=? WHERE id=?",
                        (str(exc), ticket_id),
                    )
                    self._audit(ticket_id, "blocked", str(exc))
                    outcomes.append({"ticket": ticket_id, "state": "BLOCKED", "reason": str(exc)})
                    break
                current = self.db.execute(
                    "SELECT desired FROM deployed WHERE change_key=?", (key,)
                ).fetchone()
                previous = current["desired"] if current else None
                serialized = json.dumps(desired, sort_keys=True)
                rollback_note = (
                    "MANUAL REVIEW ONLY: restore prior simulated state for " + key
                    + "; verify current state and approvals before execution."
                )
                self.db.execute(
                    """UPDATE tickets SET change_key=?,previous=?,desired=?,rollback_note=?
                       WHERE id=?""",
                    (key, previous, serialized, rollback_note, ticket_id),
                )
                self._audit(ticket_id, "precheck_passed", key)
                if ticket_id == fail_ticket:
                    self.db.execute(
                        "UPDATE tickets SET state='FAILED',reason='simulated_failure' WHERE id=?",
                        (ticket_id,),
                    )
                    self._audit(ticket_id, "deployment_failed", "simulated_failure; no rollback")
                    outcomes.append({"ticket": ticket_id, "state": "FAILED", "reason": "simulated_failure"})
                    break
                self.db.execute(
                    "INSERT INTO deployed(change_key,desired) VALUES (?,?) "
                    "ON CONFLICT(change_key) DO UPDATE SET desired=excluded.desired",
                    (key, serialized),
                )
                # Independent readback against the *mock* deployed-state table.
                readback = self.db.execute(
                    "SELECT desired FROM deployed WHERE change_key=?", (key,)
                ).fetchone()
                if readback is None or readback["desired"] != serialized:
                    raise WorkflowError("mock_postcheck_failed")
                self.db.execute(
                    "UPDATE tickets SET state='CLOSED' WHERE id=?", (ticket_id,)
                )
                self._audit(ticket_id, "closed", "mock_postcheck_passed")
                outcomes.append({"ticket": ticket_id, "state": "CLOSED", "reason": "mock_postcheck_passed"})
        return outcomes

    def rollback(self, engineer: str, ticket_id: str) -> None:
        """Explicitly restore mock state for one CLOSED ticket, with stale-state refusal."""
        self._require_engineer(engineer)
        with self.db:
            ticket = self.db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
            if ticket is None or ticket["state"] != "CLOSED":
                raise WorkflowError("ticket_not_rollback_eligible")
            current = self.db.execute(
                "SELECT desired FROM deployed WHERE change_key=?", (ticket["change_key"],)
            ).fetchone()
            if current is None or current["desired"] != ticket["desired"]:
                raise WorkflowError("rollback_state_conflict")
            if ticket["previous"] is None:
                self.db.execute("DELETE FROM deployed WHERE change_key=?", (ticket["change_key"],))
            else:
                self.db.execute(
                    "UPDATE deployed SET desired=? WHERE change_key=?",
                    (ticket["previous"], ticket["change_key"]),
                )
            self.db.execute("UPDATE tickets SET state='ROLLED_BACK' WHERE id=?", (ticket_id,))
            self._audit(ticket_id, "manual_rollback_simulated", engineer)

    def snapshot(self) -> dict[str, Any]:
        return {
            "tickets": [dict(row) for row in self.db.execute("SELECT * FROM tickets ORDER BY rowid")],
            "deployed": [dict(row) for row in self.db.execute("SELECT * FROM deployed ORDER BY change_key")],
            "audit": [dict(row) for row in self.db.execute("SELECT * FROM audit ORDER BY seq")],
        }


def seed_demo(platform: PolicyPlatform) -> None:
    """Populate an independent, synthetic two-site lab."""
    platform.add_user("reviewer", "engineer")
    platform.add_user("alice", "requester")
    platform.add_user("bob", "requester")
    platform.onboard_site("reviewer", "lab-west", {"monitor": "192.0.2.10", "api": "198.51.100.20"})
    platform.onboard_site("reviewer", "lab-east", {"monitor": "192.0.2.11", "api": "198.51.100.21"})
    platform.grant_site("reviewer", "alice", "lab-west")
    platform.grant_site("reviewer", "alice", "lab-east")
    platform.grant_site("reviewer", "bob", "lab-west")
    platform.approve_flow("reviewer", "monitor-https", "monitor", "api", "tcp", 443)
