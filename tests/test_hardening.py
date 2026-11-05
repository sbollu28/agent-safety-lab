import copy
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent_safety_lab.evaluator import evaluate
from agent_safety_lab.gateway import InMemoryApprovalGateway

DATA = json.loads((Path(__file__).resolve().parents[1] / "examples/synthetic_cases.json").read_text())
PROPOSAL = DATA["cases"][0]["proposal"]


class HardeningTests(unittest.TestCase):
    def test_malformed_policies_fail_closed(self):
        mutations = [
            {"approvals": None},
            {"approvals": {"CHG-1001": None}},
            {"approvals": {"CHG-1001": {}}},
            {"permitted_services": [None]},
            {"permitted_services": [{"protocol": "tcp", "port": True}]},
            {"allowed_source_cidr": ["192.0.2.0/24"]},
            {"allowed_destination_cidr": "bad"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                policy = copy.deepcopy(DATA["trusted_policy"])
                policy.update(mutation)
                decision = evaluate(PROPOSAL, policy)
                self.assertFalse(decision.approved)
                self.assertEqual(decision.reasons, ("invalid_trusted_policy",))

    def test_invalid_proposals_fail_closed(self):
        for proposal in (None, "hello", [], 123):
            with self.subTest(proposal=proposal):
                self.assertEqual(evaluate(proposal, DATA["trusted_policy"]).reasons, ("invalid_proposal",))
        for field, bad in (("port", True), ("source", 123), ("protocol", []), ("ticket", None)):
            with self.subTest(field=field):
                proposal = dict(PROPOSAL, **{field: bad})
                self.assertFalse(evaluate(proposal, DATA["trusted_policy"]).approved)

    def test_exact_approval_comparison_rejects_bool_port(self):
        proposal = dict(PROPOSAL, port=True)
        self.assertFalse(evaluate(proposal, DATA["trusted_policy"]).approved)

    def test_one_use_approval(self):
        gateway = InMemoryApprovalGateway()
        self.assertTrue(gateway.authorize_once(PROPOSAL, DATA["trusted_policy"]).approved)
        second = gateway.authorize_once(PROPOSAL, DATA["trusted_policy"])
        self.assertFalse(second.approved)
        self.assertEqual(second.reasons, ("approval_already_consumed",))

    def test_invalid_request_does_not_consume(self):
        gateway = InMemoryApprovalGateway()
        bad = dict(PROPOSAL, port=22)
        self.assertFalse(gateway.authorize_once(bad, DATA["trusted_policy"]).approved)
        self.assertTrue(gateway.authorize_once(PROPOSAL, DATA["trusted_policy"]).approved)

    def test_concurrent_requests_only_one_approval(self):
        gateway = InMemoryApprovalGateway()
        with ThreadPoolExecutor(max_workers=8) as pool:
            decisions = list(pool.map(lambda _: gateway.authorize_once(PROPOSAL, DATA["trusted_policy"]), range(16)))
        self.assertEqual(sum(d.approved for d in decisions), 1)


if __name__ == "__main__":
    unittest.main()
