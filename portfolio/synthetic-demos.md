# Synthetic portfolio demos: policy catalog and ticket lifecycle

These are **original offline simulations**, derived from general network-automation design principles. They are not copies of employer software and do not use production network configurations.

## Demo A — Approved-flow catalog with per-site resolution

**Source:** [site_catalog.py](../src/agent_safety_lab/site_catalog.py)

- Separates engineer-approved logical flow definitions from site address mappings.
- Resolves the same logical flow into distinct documentation-only IP addresses for different synthetic sites.
- Requires a synthetic actor-to-site entitlement and rejects unknown policies or incomplete mappings.
- Produces a display-only illustrative policy statement; no device connection or real RBAC authentication.

## Demo B — Sequential ticket pipeline with fail-stop behavior

**Source:** [workflow_demo.py](../src/agent_safety_lab/workflow_demo.py)

- Models a batch of tickets with `COMPLETED`, `BLOCKED`, `FAILED`, and `NOT_STARTED` outcomes.
- Halts subsequent processing when validation or simulated execution fails.
- Produces a *review-required manual reversal note* for completed synthetic requests.
- Never performs automatic rollback or network deployment.

## Run locally

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

The tests verify site-dependent resolution, deny-by-default conditions, incomplete address mappings, and fail-stop sequencing.

## What would turn these into more realistic reference software?

Use an authenticated identity provider; immutable, versioned approval catalogs; an atomic ticket-claim ledger; structured configuration diffs; mock adapters; explicit postchecks; failure-state reconciliation; and controlled operator-driven rollback. Each should be tested independently before any live network integrations are considered.
