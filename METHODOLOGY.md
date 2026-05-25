# Research Methodology

**DBITSA AI Security Research**
Repository: [dbitsa/research](https://github.com/dbitsa/research)
Pages: [dbitsa.github.io/research](https://dbitsa.github.io/research)
Updated: May 2026

***

## Overview

This repository documents independent applied research at the intersection of AI systems security, behavioral testing, and governance frameworks. Work proceeds in a non-linear model: broad exploratory phases give way to intensive sessions that produce discrete, committed artifacts. Not every exploratory thread results in a published output; priority is placed on methodology documents, training datasets, test outputs, and visualizations over incremental documentation.

The central research question across all threads:

> *How do established cybersecurity principles — threat modeling, adversarial testing, incident response, compliance mapping — translate into rigorous, operationalizable controls for AI systems?*

***

## Research Domains

### 1. AI Governance Framework Mapping

**Status:** Active — ongoing

Systematic analysis of intersections, gaps, and practical cross-mappings across the major AI security and risk governance frameworks. Particular focus on the full NIST AI family as an integrated set, and on how adjacent standards (ISO, OWASP, CSA) relate to and extend NIST coverage.

**Current Artifact:**
- [AI Security 3D Matrix](https://dbitsa.github.io/research/ai_security_3D.html) — interactive three-dimensional visualization mapping NIST AI RMF governance functions, MITRE ATLAS tactic categories, and OWASP LLM risk classes across a unified threat surface. An exploratory synthesis tool produced through extended multi-session research; not a final deliverable.

**Frameworks:**

| Framework | Version | Role in Research |
|---|---|---|
| NIST AI RMF 1.0 (AI 100-1) | Jan 2023 | Core governance structure (GOVERN · MAP · MEASURE · MANAGE); primary training data source; cross-mapping anchor |
| NIST AI 100-2e2025 | 2025 | Adversarial ML taxonomy: evasion, poisoning, misuse across PredAI and GenAI; terminology reference |
| NIST AI 600-1 | 2024 | Generative AI Risk Profile: 12 GenAI-specific risk categories; confabulation, data privacy, information integrity |
| NIST SP 800-218A | 2024 | SSDF Community Profile for GenAI: secure development practices for model producers, system producers, and acquirers |
| NIST SP 800-53 v5 | Rev 5 | Security and privacy controls; cross-mapped to AI RMF functions; enterprise control implementation baseline |
| NIST CSF 2.0 | 2024 | Cross-cutting GOVERN function maps to AI governance structures; supply chain risk |
| ISO/IEC 42001:2023 | 2023 | AI management system standard; compliance mapping and gap analysis |
| ISO/IEC 23894:2023 | 2023 | AI risk management guidance; risk identification and treatment processes for AI systems |
| OWASP LLM Top 10 | 2025 | LLM vulnerability taxonomy; behavioral divergence test seed categories |
| OWASP Agentic Top 10 | 2026 (Dec 2025) | Security risks for autonomous and agentic AI systems: memory poisoning, goal manipulation, MCP attack surface |
| MITRE ATLAS | Current | Tactic/technique taxonomy for ML system attacks; annotation reference for test output classification |
| CSA Agentic AI RMF Profile | 2026 | Targeted controls for autonomous agent risk; complements MITRE ATLAS |
| Google SAIF | 2026 | Secure AI Framework: training data integrity, model robustness, deployment controls |

***

### 2. Domain-Specific Model Fine-Tuning

**Status:** Initial release complete — evaluation ongoing

Fine-tuning of open-weight language models on curated Q&A datasets derived from AI security governance frameworks. Goal: produce models that reason accurately about AI risk, adversarial techniques, and governance controls without requiring full-context retrieval from source documents.

**Initial Model:** Mistral 7B-Instruct
**Training Sources:** NIST AI RMF 1.0, MITRE ATLAS, OWASP LLM Top 10, Google SAIF
**Serving Formats:** Ollama (GGUF), llama.cpp

**Published Artifacts:**
- [Ollama model](https://ollama.com/dbristol/mistral-7b-instruct-aisec-bf16)
- [Training dataset](https://huggingface.co/datasets/dbristol/aisec-training-data) — curated Q&A pairs (HuggingFace)
- [llama.cpp GGUF](https://huggingface.co/dbristol/aisec_model_v1)

**Open Questions:**
- How does framework-specific fine-tuning affect performance on general security reasoning tasks?
- What is the minimum viable dataset size for reliable single-framework alignment?
- How does quantization level affect response quality on nuanced governance queries?

***

### 3. Behavioral Divergence Testing

**Status:** Framework design phase — initial test runs complete

Development of a methodology to measure and characterize *behavioral divergence* in both white-box (local/open-weight) and black-box (closed API) LLMs when exposed to systematically varied prompt families. Current focus has shifted toward black-box testing of frontier models (Claude, ChatGPT).

Rather than testing only discrete known attack vectors, this research asks a broader structural question: given a generated "family" of semantically related prompts with controlled variation in framing, tone, and constraint language, how consistently does a model respond? Divergence patterns may surface implicit boundary conditions, alignment boundaries, or undocumented behavioral properties relevant to security and trust assessment.

**Tooling:**
- [FuzzyAI](https://github.com/cyberark/FuzzyAI) — LLM fuzzing and adversarial testing (CyberArk)
- [TransformerLens](https://github.com/TransformerLensOrg/TransformerLens) — mechanistic interpretability for white-box behavioral inspection
- Custom prompt family generation pipeline (in development)

**Methodology Design (draft):**

1. Define a *seed prompt* representing a security-relevant query category (seeded from OWASP LLM / MITRE ATLAS taxonomy)
2. Generate a structured family of prompt variants using an LLM-assisted taxonomy across four axes: framing, constraint, persona, specificity
3. Submit family members to target model(s) and record responses
4. Apply divergence scoring: semantic similarity, refusal rate, response length distribution, policy citation frequency
5. Cluster divergence patterns and annotate with probable behavioral explanation (alignment boundary, RLHF artifact, context sensitivity)
6. Cross-reference with MITRE ATLAS technique categories where applicable

**Current State:** Prompt family taxonomy drafted; initial test inputs run against multiple frontier black-box models (Claude, ChatGPT); qualitative observations recorded. Quantitative scoring pipeline not yet implemented. No quantitative results published.

***

### 4. Local AI Lab Infrastructure

**Status:** Operational

Design, deployment, and iterative configuration of an on-premises AI research environment. Infrastructure decisions are treated as research artifacts: stack tradeoffs, toolchain evaluations, and configuration choices are documented and relevant to the broader question of AI security research accessibility.

**Stack:**
- OS: Ubuntu 24.04 LTS
- Inference: Ollama, llama.cpp, LM Studio
- Orchestration: Docker, Docker Compose
- Observability: OpenTelemetry
- Agent development: Node-RED, OpenClaw (Removed), LangChain
- Interpretability: TransformerLens
- Automation: Ansible, Python, Bash

***

## Working Conventions

### Research Cadence

Work does not follow a linear sprint model. Exploratory phases inform later intensive sessions that produce committed artifacts. A visualization, model card, or methodology document may represent days of upstream work not visible in commit history.

### Artifact Status Labels

| Label | Meaning |
|---|---|
| `Active` | Currently under investigation; outputs expected |
| `Initial release complete` | First artifact published; evaluation or iteration ongoing |
| `Framework design phase` | Methodology defined; implementation in progress |
| `Operational` | Infrastructure or tooling stable and in use |
| `Paused` | Work suspended pending resources or dependencies |

### Scope Boundaries

This repository documents applied independent research, not:
- Production-ready deployable tools
- Benchmark results (pending scoring pipeline)
- Peer-reviewed academic findings
