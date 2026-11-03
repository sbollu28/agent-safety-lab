# Reproducible prototype: AI-proposed network change guardrail

This is an original, **offline and synthetic** research-engineering demonstration. It does not call a language model or execute firewall commands.

## Question
Can independent structured policy and authoritative scoped approval prevent unsafe actions even if untrusted proposal text contains persuasion, role spoofing, or prompt injection?

## Threat model
An adversary controls `request_text` and proposal parameters. They cannot change the trusted policy or authoritative approval records. All IP addresses belong to documentation-only ranges.

## Baselines
- **Keyword baseline:** screens only request text and intentionally misses many unsafe structured proposals; may block benign quotes.
- **Structured guardrail:** enforces allowed network ranges and service pairs, strict field validation, and approvals tied to exact change parameters; ignores free-form claims of authority.

## Run
```bash
python -m pip install -e .
python -m unittest discover -s tests -v
agent-safety-lab --dataset examples/synthetic_cases.json --output results/report.json
```

The fixture contains **18 hand-authored scenarios**. The unit tests check the declared expected decisions. Reproducing a high result on this constructed fixture is *not* evidence of general safety, model alignment, immunity to prompt injection, or effectiveness on unseen production cases.

## Limitations and research extensions
No live LLM, telemetry, real authorization provider, deployment stage, or adversarially sampled attack campaign was tested. This is a deterministic policy prototype, not a complete agent security gateway. Future experiments should evaluate real tool-calling agents, randomized held-out attacks, policy tampering, human approval workflows, and operational false-positive costs.

## Ethics and disclosure
No employer code, production systems, credentials, unpublished patent disclosure, or customer data were used.
