# Surya Bollu
### Network Infrastructure • Network Automation • Security Engineering

I am a network infrastructure engineer with **9+ years of experience** designing, operating, and automating carrier, data-center, and cloud/NFV networks. My work spans **BGP/MP-BGP, MPLS/VRF, Juniper SRX/vSRX, network security, high-availability design, and Python-driven automation**.

I focus on turning complex infrastructure changes into **repeatable, validated, policy-controlled engineering workflows**, with careful attention to resilience, failure handling, and operational safety.

[![GitHub](https://img.shields.io/badge/GitHub-sbollu28-181717?logo=github)](https://github.com/sbollu28)
[![Portfolio](https://img.shields.io/badge/Project-Agent%20Safety%20Lab-137C8B)](https://github.com/sbollu28/agent-safety-lab)

## Engineering focus

| Domain | Areas of work |
| --- | --- |
| **Network architecture** | BGP, MP-BGP, routing policy, MPLS, VRF, high availability, traffic engineering, carrier/backbone architecture |
| **Security infrastructure** | Juniper SRX/vSRX, segmentation, NAT, VPN/IPsec, 5G roaming security, firewall migrations |
| **Infrastructure automation** | Python, Ansible, Jinja2, YAML, REST APIs, Azure DevOps, validation, controlled configuration delivery |
| **Cloud and virtualization** | Network function virtualization, Azure/OpenStack, Kubernetes networking, SR-IOV and DPDK evaluation |
| **Engineering reliability** | Change safety, pre/post checks, fault analysis, operational runbooks, risk-controlled migrations |

## Featured public project

### [Agent Safety Lab](https://github.com/sbollu28/agent-safety-lab)

An **offline, synthetic security-engineering prototype** that independently checks AI-proposed firewall changes against a trusted policy and exact approval records.

- Evaluates source/destination scope, protocol/port constraints, approved change tickets, and malformed input.
- Includes a deliberately weak keyword-based comparator and **18 hand-authored benchmark scenarios**.
- Provides automated tests and GitHub Actions CI.
- Includes a demonstration of single-process approval replay protection; **not** a production approval service.
- Documents threat models and the proposed architecture of a safer agent-to-tool gateway.

**Current scope:** deterministic evaluation only. It does **not** run a live LLM, connect to production networks, or automatically deploy firewall changes.

[Explore the code and benchmark →](https://github.com/sbollu28/agent-safety-lab)

## Selected professional engineering work

> The work below describes professional experience and is not published as employer source code or employer system documentation.

**Policy-controlled network automation (approximately 50 sites)**  
Designed automation workflows integrating change tickets, an approved policy source of truth, site-specific address resolution, configuration generation, and controlled device deployment. The workflow separates user requests from engineer-approved network flows. It also generates rollback configuration artifacts for a separately initiated manual rollback process.

**Carrier and network-security architecture**  
Worked on routing and security designs across carrier/mobile-core and cloud/NFV environments, including BGP/MP-BGP, MPLS/VRF, SRX/vSRX, HA, migrations, traffic engineering, and troubleshooting.

**5G network security research**  
Named inventor on a **patent-pending** invention titled *Centralized Session Correlation Engine for Real-Time Validation and Security Enforcement in 5G Networks*. Patent status is stated without claims about grant, adoption, or commercial deployment.

## Current learning and engineering directions

- Reproducible network topology and failure testing
- EVPN/VXLAN fabric design and network observability
- Safer agent tool-use through deterministic authorization
- Cloud-native networking and infrastructure software engineering

These are learning and development directions, not claims of completed public implementations.

## Certifications

- **Cisco CCNP Enterprise**
- **Juniper JNCIA** — Junos, Security, Cloud, DevOps, and Design (as listed on my resume)

## Technology stack

`Python` `Ansible` `Jinja2` `YAML` `REST APIs` `Azure DevOps` `Linux` `BGP` `MP-BGP` `MPLS` `VRF` `Juniper SRX/vSRX` `Cisco Nexus` `Arista` `Kubernetes networking`

## Connect

- **GitHub:** [github.com/sbollu28](https://github.com/sbollu28)
- **Professional contact:** [Email](mailto:sbollu28@gmail.com)

---

*All public demonstrations use original or synthetic examples. No employer-confidential implementation details, credentials, production configurations, or unpublished invention disclosures are included.*
