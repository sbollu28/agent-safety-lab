import tempfile
import unittest
from pathlib import Path

from agent_safety_lab.platform import PolicyPlatform, WorkflowError, seed_demo


class EndToEndPlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "platform.sqlite3"
        self.p = PolicyPlatform(self.path)
        seed_demo(self.p)

    def tearDown(self):
        self.p.close()
        self.temp.cleanup()

    def test_approved_flow_and_manual_rollback(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")
        self.assertEqual(self.p.run_once()[0]["state"], "CLOSED")
        state = self.p.snapshot()
        self.assertEqual(len(state["deployed"]), 1)
        self.assertIn("192.0.2.10", state["deployed"][0]["desired"])
        self.assertTrue(state["tickets"][0]["rollback_note"])
        self.p.close()
        self.p = PolicyPlatform(self.path)  # persistence across restarts
        self.assertEqual(self.p.run_once(), [])  # no duplicate deployment
        self.p.rollback("reviewer", "CHG-1001")
        self.assertEqual(self.p.snapshot()["tickets"][0]["state"], "ROLLED_BACK")
        self.assertEqual(self.p.snapshot()["deployed"], [])

    def test_unauthorized_site_stops_batch(self):
        self.p.submit("CHG-1001", "bob", "lab-east", "monitor-https")
        self.p.submit("CHG-1002", "alice", "lab-west", "monitor-https")
        result = self.p.run_once()
        self.assertEqual(result[0]["state"], "BLOCKED")
        self.assertEqual(self.p.snapshot()["tickets"][1]["state"], "OPEN")

    def test_unapproved_flow_denied(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "ssh")
        self.assertEqual(self.p.run_once()[0]["reason"], "flow_not_approved")

    def test_simulated_failure_stops_no_automatic_rollback(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")
        self.p.submit("CHG-1002", "alice", "lab-east", "monitor-https")
        outcomes = self.p.run_once(fail_ticket="CHG-1001")
        self.assertEqual(outcomes[0]["state"], "FAILED")
        snapshot = self.p.snapshot()
        self.assertEqual(snapshot["deployed"], [])
        self.assertEqual(snapshot["tickets"][1]["state"], "OPEN")
        with self.assertRaisesRegex(WorkflowError, "ticket_not_rollback_eligible"):
            self.p.rollback("reviewer", "CHG-1001")

    def test_manual_rollback_denied_to_requester(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")
        self.p.run_once()
        with self.assertRaisesRegex(WorkflowError, "engineer_role_required"):
            self.p.rollback("alice", "CHG-1001")

    def test_stale_rollback_refused(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")
        self.p.run_once()
        with self.p.db:
            self.p.db.execute("UPDATE deployed SET desired='changed' WHERE change_key='lab-west:monitor-https'")
        with self.assertRaisesRegex(WorkflowError, "rollback_state_conflict"):
            self.p.rollback("reviewer", "CHG-1001")

    def test_site_onboarding_permissions_and_resolution(self):
        with self.assertRaisesRegex(WorkflowError, "engineer_role_required"):
            self.p.onboard_site("alice", "lab-third", {"monitor": "192.0.2.12"})
        self.p.onboard_site("reviewer", "lab-third", {"monitor": "192.0.2.12", "api": "198.51.100.22"})
        self.p.grant_site("reviewer", "alice", "lab-third")
        self.p.submit("CHG-1003", "alice", "lab-third", "monitor-https")
        self.assertEqual(self.p.run_once()[0]["state"], "CLOSED")
        self.assertIn("192.0.2.12", self.p.snapshot()["deployed"][0]["desired"])

    def test_duplicate_ticket_is_rejected(self):
        self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")
        with self.assertRaises(Exception):
            self.p.submit("CHG-1001", "alice", "lab-west", "monitor-https")


if __name__ == "__main__":
    unittest.main()
