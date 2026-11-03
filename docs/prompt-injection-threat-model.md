# Prompt Injection Threat Model for a Network Operations Agent

**Status:** Draft threat model.

## System and trust boundaries

The agent receives trusted user instructions, untrusted retrieved documents and telemetry, and responses from authorized tools. Its available tools may range from read-only status queries to high-impact configuration changes. The key trust boundary is between *content describing the world* and *authority to act*.

## Assets

- Device configurations, credentials and access tokens
- Network availability, segmentation and routing correctness
- Approval records, source-of-truth inventory and audit trails

## Adversaries and entry points

An attacker may control text in a retrieved runbook, issue, log entry, web page or a lower-trust tool result. They may insert instructions such as “ignore previous rules,” fabricated emergency notices, or forged approval messages.

## Threat scenarios and controls

| Threat | Example | Required control |
| --- | --- | --- |
| Instruction laundering | A tool result says “execute this remediation command” | Treat tool data as non-authoritative; enforce independent policy |
| Scope escalation | Document directs agent to a different device | Bind allowed resource IDs to the authenticated request |
| Approval spoofing | Page claims that security already approved an action | Verify a cryptographically bound approval outside the agent context |
| Data exfiltration | Tool output requests credential upload to a URL | Restrict network egress and never expose secrets to agent context |
| Safety bypass | Change description conceals permissive firewall rule | Validate structured diffs against security invariants |

## Residual risks

Even policy-compliant commands may be operationally unsafe because of incomplete topology, stale telemetry or unexpected device behavior. Safety therefore requires staged deployment, independent postchecks and an abort path, not prompt instructions alone.

## Scope boundaries

No claim is made that a language model can reliably identify all injection attempts. This threat model favors controls enforced outside the model.
