# AI Security Portfolio | Surya Bollu

**Network Security Engineering · Agent Safety · Infrastructure Automation · Secure Systems Design**

This repository documents my technical background and a research-oriented portfolio focused on secure, reliable AI agents operating in critical infrastructure environments.

> **Evidence note:** The engineering background below reflects professional experience described by the author. The agent-safety architectures, evaluations, and prototypes are *proposals or work in progress* unless a linked artifact demonstrates implementation and results. No affiliation with, endorsement by, or disclosure on behalf of any employer is implied.

## Focus areas

- **Agentic AI security:** least-privilege tool access, approval gates for high-impact actions, adversarial input handling, and auditable execution
- **Network and cloud security:** firewalls, routing, IPsec/VPN, segmentation, stateful inspection, and resilient infrastructure
- **Secure automation:** Python, structured configuration generation, validation, configuration drift detection, staged rollout, and rollback
- **Safety engineering:** explicit invariants, fault injection, fail-closed decisions, observability, and measurable evaluation

## Selected experience

- Network security and large-scale infrastructure engineering, including Juniper SRX and carrier-network environments.
- Automation workflows using Python, Jinja2, YAML and delivery pipelines for network configuration and lifecycle tasks.
- Technical investigation and invention work relating to 5G roaming security and correlation-driven validation. **Patent status and claims are intentionally not asserted in this public portfolio.**

## Portfolio projects

| Project | Status | What it explores |
| --- | --- | --- |
| [Agent Tool-Use Safety Gateway](portfolio/agent-tool-safety-gateway.md) | Design proposal | Authorization, approval, dry-run, audit, and policy-based action gating |
| [Network Change Safety Harness](portfolio/network-change-safety-harness.md) | Design proposal | Preflight checks, canary deployment, postchecks, drift detection, and rollback |
| [Prompt Injection Threat Model](docs/prompt-injection-threat-model.md) | Threat-model draft | Trust boundaries, untrusted retrieval, and tool-output manipulation |
| [Evaluation Plan](docs/evaluation-plan.md) | Proposed methodology | Test cases and measurable safety outcomes |

## Demonstration artifact

[`examples/policy.yaml`](examples/policy.yaml) is an **illustrative, non-production policy** for a hypothetical agent allowed to inspect network state but requiring human approval before configuration changes.

## Research questions

1. How can agent tool permissions be bound to user intent, environment, and change scope rather than the model's own request?
2. What evidence is sufficient to authorize a network change autonomously, and when must the agent refuse or escalate?
3. How can a deployment harness measure and constrain blast radius when telemetry is incomplete or compromised?
4. How should agent actions be logged so a reviewer can reconstruct the decision and execution path?

## Principles

**Separation of duties · Least privilege · Explicit authorization · Reproducible evaluation · Conservative failure handling · Human control over high-impact actions**

## Contact

GitHub: [@sbollu28](https://github.com/sbollu28)

## Responsible disclosure and confidentiality

This repository does not contain employer network configurations, internal architecture, customer data, credentials, proprietary source code, or unpublished invention disclosures. Illustrations are simplified, original, and intended for public discussion.
