# Guardrailed LLM with Automated Red Teaming

## ?? 2026 Architecture Modernization
To ensure production readiness, LLM agents require continuous adversarial testing. This project implements **Automated AI Red Teaming** within a CI/CD loop.

### Key Features
1. **Adversarial Attacker LLM:** A Python-based script that continuously attacks the primary agent with known jailbreaks, prompt injections, and role-play escapes.
2. **NeMo Guardrails Defense:** Implements strict topical and behavioral guardrails to block malicious inputs and enforce deterministic outputs.
3. **Continuous Security:** Generates automated security reports showing attack success/failure rates, proving the system's resilience.

## ??? Tech Stack
*   **Security:** NeMo Guardrails, Automated Red Teaming
*   **AI / ML:** Python, Local LLMs
