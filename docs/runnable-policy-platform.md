# Runnable network policy automation platform — synthetic offline demo

**Implemented** using Python standard library and SQLite. This is an original, standalone software demonstration inspired by *general* safety engineering patterns, not a copy of any employer's implementation.

## How to run

From the repository root:

```bash
python -m pip install -e .
agent-policy-demo --db demo.sqlite3 init-demo
agent-policy-demo --db demo.sqlite3 submit CHG-1001 alice lab-west monitor-https
agent-policy-demo --db demo.sqlite3 run
agent-policy-demo --db demo.sqlite3 status
agent-policy-demo --db demo.sqlite3 rollback reviewer CHG-1001
agent-policy-demo --db demo.sqlite3 status
python -m unittest discover -s tests -v
```

To simulate a failure on a different synthetic request:

```bash
agent-policy-demo --db demo.sqlite3 submit CHG-1002 alice lab-east monitor-https
agent-policy-demo --db demo.sqlite3 run --fail-ticket CHG-1002
agent-policy-demo --db demo.sqlite3 status
```

To simulate a standalone site-onboarding workflow:

```bash
agent-policy-demo --db demo.sqlite3 onboard-site reviewer lab-third '{"monitor":"192.0.2.12","api":"198.51.100.22"}'
```

The new site requires an independently granted entitlement before a requester can use it. The CLI models site onboarding, not a real onboarding pipeline.

## What the system actually implements

| Component | Implementation |
| --- | --- |
| Ticket intake | Local CLI writes records to SQLite |
| Scheduled pipeline stage | `run` invokes one cycle; external scheduling not provided |
| Approved policy catalog | Engineer-only flow definitions in SQLite |
| Simplified RBAC | Synthetic actors and site entitlements; actor supplied as CLI argument |
| Polymorphic address book | Logical objects resolved per synthetic site |
| Site onboarding | Engineer-gated mapping insertion |
| Deployment | Local SQLite mock state; **no device connections** |
| Validation | Approved-flow, site entitlement, mapping and service checks |
| Postcheck | Verifies the mock state table, not network forwarding |
| Audit | Timestamped local SQLite event history |
| Idempotency | Ticket primary key plus OPEN-state processing; single-process execution assumption |
| Failure handling | Stop the cycle; later tickets remain OPEN |
| Rollback | Explicit engineer command restores matching mock prior state; never automatic |

## Security boundaries and known limitations

**Not suitable for production network operations.** The CLI accepts actor names as arguments rather than authenticating users. An attacker with local database access can modify roles, flows, or audit history. The SQLite audit log is not immutable. There is no real Jira, SharePoint, Microsoft Forms, SSH, Azure DevOps, secrets management, maintenance-window control, real network postchecks, distributed locks, robust concurrent worker claims, or transactionally coupled remote execution. Simulated rollback is **not** vendor-specific recovery. The platform is for local demo and tests only.

The actual professional automation described in the portfolio used an hourly polling workflow, SharePoint-approved flow definitions, polymorphic per-site addressing, controlled deployment and manually initiated rollback. Those are architecture observations, not claims that this public demo contains or reuses its employer's implementation.

## Recommended next engineering milestones

1. Implement a separate signed-identity and policy API for real RBAC/ABAC.
2. Add a safe mock adapter interface and command authorization before integrating device APIs.
3. Add pre-deployment snapshots, granular result states, and retry/reconciliation tests.
4. Introduce a mock ticket-provider adapter to separate integration from business logic.
5. Measure correctness and failure recovery across independent held-out cases.
