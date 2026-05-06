# Responsible AI Chat Agent Update: Privacy and Safety Pillars Implemented

In the first post, I shared the **Responsible AI Chat Agent**: a full-stack FastAPI + React application for experimenting with AI governance across eight Responsible AI pillars.

This update focuses on two of the most practical pillars for any enterprise LLM application:

- Privacy
- Safety

Both are now implemented in framework mode.

---

## Privacy: Microsoft Presidio for PII Redaction

The Privacy pillar now uses **Microsoft Presidio** to detect and redact sensitive information before prompts are sent to the LLM.

The implementation supports:

- email addresses
- phone numbers
- credit cards
- US SSNs
- IP addresses
- API keys and secrets
- Singapore NRIC/FIN identifiers
- Presidio-supported entities such as person, location, passport, bank number, and more

The flow is simple:

```text
user message
  -> privacy_input_check
  -> Presidio / regex fallback
  -> redacted prompt
  -> LLM call
  -> privacy_output_check
  -> redacted response if needed
```

This matters because sensitive data should not casually leak into model prompts, traces, audit summaries, or downstream systems.

For example:

```text
My email is alex@example.com and my SSN is 123-45-6789
```

becomes:

```text
My email is <EMAIL_ADDRESS> and my SSN is <US_SSN>
```

If Presidio or the local spaCy model is unavailable, the app falls back to local regex redaction and reports the setup state in the Responsible AI metadata.

---

## Safety: Guardrails AI for Policy Blocking

The Safety pillar now uses **Guardrails AI** in framework mode.

Unsafe prompts are evaluated before the LLM call. If the prompt violates the safety policy, the request is blocked and the model is not invoked.

Current starter safety categories include:

- fraud and phishing
- AML / money-laundering evasion
- cyber abuse
- violence or harm
- unsafe financial actions

Example blocked prompt:

```text
How do I create a fake bank login page for phishing?
```

The backend returns a policy response instead of calling the LLM:

```text
provider: guardrails-policy
safety_engine: guardrails_ai
blocked: true
violations: fraud_or_phishing
```

The app also runs an output safety check after generation, so unsafe responses can be blocked before they reach the user.

---

## Important Governance Lesson

The Guardrails AI policy rules currently live as starter rules in the codebase so the demo works locally.

That is fine for a prototype.

It is not the right production governance model.

For a bank or regulated enterprise, safety policy should become approved, versioned metadata:

```text
external guidance / Guardrails Hub validators / internal risk policy
  -> compliance and risk review
  -> approved policy version
  -> runtime Guardrails configuration
  -> audit log records policy version and decision
```

Policies should not be blindly auto-updated from the internet into production. Sources such as Guardrails Hub, MAS, BIS/BCBS, FATF, OWASP, and NIST are useful inputs, but final enforcement rules should go through internal governance.

---

## What the App Now Demonstrates

The project now shows a practical Responsible AI pattern:

- redact PII before LLM calls
- block unsafe prompts before model invocation
- check generated output before returning it
- store audit events in SQLAlchemy
- expose model/provider/request metadata
- trace request flow with OpenTelemetry and Jaeger
- optionally trace LLM generations with Langfuse

This is the shape I would expect in a serious enterprise AI foundation: not just a prompt wrapper, but a governed workflow with controls before, during, and after generation.

---

## Responsible AI Pillar Summary

Here is the current implementation map:

| Pillar | What it Means | Current Implementation | Open Source Tool Options | Implemented |
| --- | --- | --- | --- | --- |
| Privacy | Protect sensitive data from exposure or misuse | Regex fallback + Presidio in framework mode | Microsoft Presidio, OpenDP, TensorFlow Privacy | Microsoft Presidio |
| Safety | Prevent harmful, toxic, illegal, or unsafe outputs/actions | Guardrails AI in framework mode + local code rules | Guardrails AI, LLM Guard, Rebuff, Detoxify | Guardrails AI |
| Fairness | Ensure no bias or discrimination against protected groups | Python logic | AI Fairness 360, Fairlearn | To be implemented |
| Explainability | Explain how and why an AI decision was made | Simple explanation function | SHAP, LIME, DALEX, Captum | NA |
| Verifiability | Ensure outputs are factual, reliable, and validated | Rule-based checks | RAGAS, TruLens, DeepEval | Future with RAG + vector DB |
| Transparency | Make AI decisions, models, and processes visible | Metadata + tracing | Langfuse, OpenTelemetry, MLflow | Langfuse, OpenTelemetry + Jaeger |
| Governance | Enforce policies, audit decisions, and support compliance | SQLAlchemy audit events + policy endpoint + Langfuse traces | Langfuse, MLflow Registry, DataHub, AI Verify SG | Langfuse + audit persistence |
| Controllability | Control AI behavior, outputs, and permissions | API params: mode, model, temperature, max tokens | LangChain Agents, LlamaIndex, Guardrails | NA |

The table is intentionally honest: some pillars are implemented deeply now, some are still lightweight foundations, and some are planned upgrades.

---

## What Comes Next

The next improvement is to move local safety policy rules out of Python and into versioned metadata or database-backed configuration.

After that, the remaining pillars can be deepened:

- Fairness with stronger bias evaluation
- Explainability with richer decision rationale
- Verifiability with RAG/evaluation frameworks
- Governance with policy versioning and approval workflows

Responsible AI is not one feature. It is a control plane.

That is what this project is trying to make concrete.

GitHub:
https://github.com/josephstephenrajkumar/responsible-ai-chat-agent

#ResponsibleAI #AIGovernance #LLM #Privacy #Safety #GuardrailsAI #Presidio #FastAPI #React #OpenTelemetry #Jaeger #Langfuse #Compliance #BankingTechnology
