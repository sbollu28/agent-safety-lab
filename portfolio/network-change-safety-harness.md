# Network Change Safety Harness for AI-Assisted Operations

**Status:** Design proposal, informed by production network automation experience. No production deployment or benchmark is claimed.

## Objective

Prevent unsafe changes when an AI assistant proposes updates to network devices or cloud-network infrastructure. Use deterministic controls around a probabilistic planner.

## Proposed workflow

1. Parse user intent into a typed change request with asset IDs, expected behavior, and a rollback plan.
2. Compare the request with an authorized source of truth and current configuration snapshot.
3. Validate schema, syntax, dependencies, management reachability, and routing/security invariants.
4. Produce a proposed diff; require independent approval for higher-risk changes.
5. Deploy to a canary or tightly scoped batch.
6. Evaluate postchecks (adjacency, reachability, interface health, traffic, policy and error metrics).
7. Continue in bounded batches only if checks pass; otherwise stop and invoke the tested rollback mechanism.
8. Record decisions and evidence for later review.

## Example safety invariants

- Never remove the only verified management path.
- Never expand firewall access outside the approved change scope.
- Never withdraw a required prefix without an approved maintenance plan.
- Never auto-continue when telemetry is missing or health checks are inconclusive.
- Reject configuration drift before proceeding unless explicitly reconciled.

## Failure modes to test

- The AI suggests a syntactically valid but overly permissive firewall rule.
- A stale inventory maps the intended device name to the wrong target.
- Telemetry disappears after a canary configuration is applied.
- Two concurrent change requests conflict.
- The rollback command succeeds, but post-rollback behavior remains degraded.

## Implementation sketch

Python orchestration with typed schemas; mock network devices for initial testing; vendor-specific adapters only after the invariant checker is stable. Separate privilege domains for inventory read, configuration diff, change execution, and approval.

## Success criteria

No unauthorized change execution in the defined adversarial test suite, full audit event coverage, and correct halt/rollback behavior in injected failure cases. These are **targets**, not measured outcomes.
