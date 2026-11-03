# Agent Tool-Use Safety Gateway

**Status:** Design proposal — not a claim of deployed software or measured results.

## Problem

An AI agent can translate untrusted content into high-impact actions if tool invocation and authority are not independently checked. A network-operations assistant may be asked to inspect devices legitimately, but a compromised document or tool response might try to make it push a configuration.

## Proposed architecture

```text
User request + authenticated identity
                |
          Intent parser
                |
     Structured action proposal
                |
        Policy enforcement point <--- policy + asset inventory
                |
       Risk and scope validator
                |
    +-----------+------------+
    |           |            |
  Deny       Dry-run       Approval gate
                             |
                      Bounded executor
                             |
                      Post-execution checks
                             |
                        Audit record
```

The *executor*, not the language model, must enforce permissions, action schemas, resource scopes, time limits, and credential access. Retrieved documents and tool output are untrusted evidence, not authorization.

## Security invariants

1. A lower-trust source cannot grant new privileges.
2. Write actions are denied unless an independent policy allows them.
3. High-impact changes require an approval token bound to the exact action, target, and proposed diff.
4. No credentials or secret values appear in agent-visible logs.
5. If authorization or device state cannot be verified, execution fails closed.
6. Each attempted tool call generates an attributable audit event.

## Example scenarios

- **Allowed:** Read interface status for an approved device and summarize the result.
- **Approval required:** Modify a routing policy in a change window, after schema validation and a dry-run diff.
- **Denied:** Run a configuration command suggested by a retrieved web page, even when the page claims to be a system instruction.
- **Denied:** Apply a change to a device outside the authenticated user's authorized inventory.

## Evaluation direction

Test prompt-injection attempts, approval spoofing, scope escalation, policy-service failure, and audit coverage with a deterministic harness. See [evaluation plan](../docs/evaluation-plan.md).
