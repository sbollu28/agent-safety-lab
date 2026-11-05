import unittest

from agent_safety_lab.site_catalog import CatalogError, Flow, resolve_change, render_set_command
from agent_safety_lab.workflow_demo import Ticket, process_batch


FLOWS = {"monitor": Flow("monitor", "monitor", "service", "tcp", 443)}
ADDRESSES = {
    "lab-west": {"monitor": "192.0.2.10", "service": "198.51.100.20"},
    "lab-east": {"monitor": "192.0.2.11", "service": "198.51.100.21"},
}
ENTITLEMENTS = {"operator": frozenset({"lab-west", "lab-east"})}


class PortfolioDemoTests(unittest.TestCase):
    def test_polymorphic_resolution(self):
        west = resolve_change(site="lab-west", flow_name="monitor", actor="operator",
                              site_entitlements=ENTITLEMENTS, approved_flows=FLOWS, addresses=ADDRESSES)
        east = resolve_change(site="lab-east", flow_name="monitor", actor="operator",
                              site_entitlements=ENTITLEMENTS, approved_flows=FLOWS, addresses=ADDRESSES)
        self.assertNotEqual(west.source, east.source)
        self.assertEqual(west.port, east.port)
        self.assertIn("192.0.2.10", render_set_command(west))

    def test_unknown_flow_is_denied(self):
        with self.assertRaisesRegex(CatalogError, "flow_not_approved"):
            resolve_change(site="lab-west", flow_name="ssh-admin", actor="operator",
                           site_entitlements=ENTITLEMENTS, approved_flows=FLOWS, addresses=ADDRESSES)

    def test_entitlement_is_required(self):
        with self.assertRaisesRegex(CatalogError, "site_not_authorized"):
            resolve_change(site="lab-east", flow_name="monitor", actor="visitor",
                           site_entitlements=ENTITLEMENTS, approved_flows=FLOWS, addresses=ADDRESSES)

    def test_missing_address_fails_closed(self):
        with self.assertRaisesRegex(CatalogError, "unresolved_site_address"):
            resolve_change(site="lab-west", flow_name="monitor", actor="operator",
                           site_entitlements=ENTITLEMENTS, approved_flows=FLOWS,
                           addresses={"lab-west": {"monitor": "192.0.2.10"}})

    def test_sequential_stop_no_auto_rollback(self):
        tickets = [Ticket("CHG-1001", "operator", "lab-west", "monitor"),
                   Ticket("CHG-1002", "operator", "lab-east", "monitor"),
                   Ticket("CHG-1003", "operator", "lab-west", "monitor")]
        results = process_batch(tickets, site_entitlements=ENTITLEMENTS,
                                approved_flows=FLOWS, addresses=ADDRESSES,
                                simulated_failed_tickets=frozenset({"CHG-1002"}))
        self.assertEqual([r.state for r in results], ["COMPLETED", "FAILED", "NOT_STARTED"])
        self.assertIsNotNone(results[0].manual_rollback_artifact)
        self.assertIsNone(results[1].manual_rollback_artifact)

    def test_unapproved_flow_stops_batch(self):
        tickets = [Ticket("CHG-1", "operator", "lab-west", "unapproved"),
                   Ticket("CHG-2", "operator", "lab-west", "monitor")]
        results = process_batch(tickets, site_entitlements=ENTITLEMENTS,
                                approved_flows=FLOWS, addresses=ADDRESSES)
        self.assertEqual([r.state for r in results], ["BLOCKED", "NOT_STARTED"])


if __name__ == "__main__":
    unittest.main()
