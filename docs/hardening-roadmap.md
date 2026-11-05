# Safety gateway implementation roadmap

## Implemented in this repository

- Deterministic network-change evaluator with strict trusted-policy schema checks.
- Exact scoped change-approval matching, including strict field types.
- Synthetic benchmark and deliberately weak keyword comparator.
- Single-process `InMemoryApprovalGateway` demonstrating atomic one-use ticket consumption with a lock.
- Negative-input and concurrent replay unit tests; a Python-version CI matrix with JSON report artifacts.

## Scope and limitations

The CLI benchmark intentionally calls the **stateless** evaluator. The in-memory gateway is a separate demonstration. Its ticket ledger disappears on restart, is not shared across processes, has no identity authentication, and is not suitable for production authorization. It prevents replay only for a single gateway instance while the process is running. No LLM, SSH, firewall, network device, deployment, or approval-provider integration is implemented. The example YAML policy is still illustrative only; the benchmark uses its synthetic JSON policy.

## Next milestones

1. Define a versioned policy schema shared by YAML and JSON, with authenticated identities and asset/site binding.
2. Build a durable approval service with transactional single-use consumption, expiry, revocation, and cryptographic request/diff binding.
3. Provide a tool-calling agent simulator and independent policy-enforcing tool gateway.
4. Integrate mock network preflight, diff validation, deployment, postchecks, manual rollback gating and complete audit trails.
5. Extend evaluation with held-out adversarial cases, fault injection, safety and usefulness metrics, and independently reproducible results.

All architecture and operational goals beyond the implemented controls remain proposals.
