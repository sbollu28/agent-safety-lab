# Policy-controlled network automation — architecture review

**Origin:** A high-level description of professional network policy automation work. This review is an independent, sanitized account of the patterns described, not a reproduction of employer implementation or confidential design.

## Workflow described

1. A wiki landing page contains user instructions and a button that starts a request through Microsoft Forms/Jira.
2. An Azure DevOps pipeline runs approximately **hourly**. Its first stage finds tickets matching a designated pattern.
3. A second stage processes eligible tickets, marks them **In Progress**, and adds ticket comments.
4. The pipeline reads the engineer-controlled list of **approved policy flows** from a SharePoint-backed policy sheet.
5. A **polymorphic address book** resolves logical source/destination references to site-specific IPs according to the site named in the request.
6. The pipeline generates a concrete configuration and pushes it over **SSH** to the selected site.
7. Ticket status and comments are updated as processing proceeds; completed requests are closed.
8. A separate new-site onboarding pipeline populates site-specific address mappings.
9. Rollback configuration artifacts can be prepared; **rollback is initiated manually via a separate pipeline**.
10. On a reported deployment failure, the process **stops; it does not automatically roll back**.

**Reported scope:** approximately **50 sites**. Request volume, users/teams, deployment savings, reliability metrics, and actual rollback success rates are not established.

## Security interpretation: approval catalog is not proof of complete RBAC

The design establishes an important *policy-approval boundary*: ordinary users can request pre-approved flows; new flows must be reviewed with engineers before being added to the authoritative policy sheet. This is a strong foundation for least-privilege self-service.

However, the conversation does **not establish** the presence of authenticated per-user site entitlements, service-account permission scoping, separation of duties on SharePoint sheet edits, immutable change authorization, or cryptographic request-to-approval binding. Do not claim that comprehensive RBAC was implemented without additional evidence.

A safer reference design should independently validate: requester identity, allowed sites/assets, approved flow ID, immutable policy version, exact resolved diff, change-window and deployment privilege. Ticket text alone must never grant access.

## Engineering strengths

- Separates request intake from the approved policy catalog.
- Models a **logical flow once** and resolves site-specific attributes through an abstraction layer, reducing repeated per-site flow definitions.
- Uses an independent new-site onboarding workflow.
- Makes changes traceable through ticket lifecycle updates.
- Uses explicit operator-controlled rollback rather than falsely asserting autonomous recovery.

## Failure and operational risks to address

| Concern | Why it matters | Recommended evidence/control |
| --- | --- | --- |
| Request scope and identity | A valid catalog entry must not give every requester access to every site | Trusted identity; site and flow entitlement checks |
| Source-of-truth integrity | Unauthorized SharePoint edits could expand allowed access | Engineer approval workflow, restricted editing, versioned catalog |
| Partial batch completion | Earlier changes may already be applied when a later ticket fails | Per-ticket execution journal and explicit partial-success state |
| SSH execution safety | Remote commands may partially apply or fail after an acknowledgment | Candidate/commit validation where supported, bounded execution, read-back verification |
| Retry and duplicate tickets | Hourly polling or pipeline retries may re-apply a change | Ticket/change idempotency keys and atomic claim/lock |
| Polymorphic resolution drift | Incorrect site mapping can target unintended addresses | Typed mapping validation, provenance, site onboarding review |
| Postchange state | Ticket closure need not imply intended forwarding behavior | Independent postchecks and evidence before close |
| Manual rollback | Generated rollback may be stale or incomplete | Human review, verified snapshots, preconditions, manual execution and post-rollback checks |
| Audit traceability | Ticket comments alone may not prove each action | Append-only execution/event records with policy and diff hashes |

## What is implemented publicly vs. only documented

- **Professional experience, described but not published:** the Jira/SharePoint/Azure DevOps/SSH platform and approximately 50-site scope.
- **Public synthetic demo code in this repository:** approved-flow catalog and site-specific address resolver; sequential ticket-processing simulator with stop-on-failure behavior.
- **Not implemented in the synthetic demos:** Jira, SharePoint, Microsoft Forms, Azure DevOps, real RBAC authentication, SSH, live device configuration, scheduling, persistent approvals, actual rollback, production telemetry.

## Staff-level talking points

- Why engineer-controlled flow catalogs are safer than broad configuration privileges.
- How polymorphic site resolution avoids maintaining duplicate configurations across many sites.
- Why source-of-truth provenance, idempotency, and partial batch failure are critical at scale.
- Difference between an authorization design principle and proven enforced RBAC.
- Failure model: stop on error, preserve evidence, and require controlled manual recovery.
