# Sentient Alignment for SANO

> Supporting grant context. This document explains a possible public-good
> relationship; it is not evidence of current Sentient integration, Enclave
> deployment, or confidential-compute support.

## Positioning

SANO is an open-source, self-hosted personal and family health workspace with a
reusable trust boundary for sensitive personal agents. Its approved short pitch
is:

> SANO: private, source-grounded health workspace with auditable AI.

Health is the reference stress test. It forces the system to make authorization,
provenance, uncertainty, disclosure, and safety visible from the first run. The
trust boundary is intended to be useful to other sensitive-agent builders while
SANO remains a health workspace rather than a generic platform claim.

## Fit with Sentient principles

| Principle | SANO alignment |
| --- | --- |
| Open | Open source contracts, schemas, evals, security docs, and synthetic fixtures are reviewable. |
| Yours to keep | A self-hosted installation keeps the workspace and backups under the operator's control. |
| Accessible | The product is runnable locally with Docker and deterministic checks; accessibility remains part of the UI contract. |
| Good for humanity | The health reference domain keeps uncertainty, human review, and safety boundaries visible. |
| Private by default | Person-scoped authorization and local storage are defaults; external disclosure is optional and consented per action. |
| Empowering rather than extractive | Users retain sources, provenance, review, export, receipts, and explicit sharing decisions. |

## Current repository boundary

Public GitHub `main` at the dated `84fb682` baseline already contains Product
Core schema v13 and SANO-X2, including OCR and bounded document understanding.
The seven post-`84fb682` production/product refinements through `089a5eb` are
now integrated in the published main and do not introduce those capabilities. See the
dated [validation record](sano-live-validation.md) for exact revisions and CI.

G5 remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`: Agent Skills
interoperability is verified for OMP 17.3.5 and Hermes Agent 0.19.0, while root
Agent Plugins two-client evidence is pending. There is no claim of a production
Sentient identity bridge, Sentient-hosted health workspace, Enclave deployment,
or confidential-compute integration.

Local-model inference without an external API and the OpenRouter/DeepSeek live
provider flow, including document summary/Q&A, are operator-confirmed. Summary
attribution, Q&A citations, and execution receipts are included in that
confirmation. OpenAI live X2 is unverified. Model,
endpoint, prompt, output, and workflow-specific smoke details are stated only
when recorded in the dated validation report.

## Fit with public-good infrastructure

| Public-good concern | SANO evidence |
| --- | --- |
| Inspectable behavior | Source, provenance, schemas, authorization rules, receipts, evals, and security docs are reviewable. |
| User control | Actor identity, Person scope, delegated access, human review, explicit consent, and export are explicit boundaries. |
| Private-by-default operation | The reference deployment is self-hosted and public fixtures are synthetic or de-identified. |
| Fail-closed behavior | Missing authorization, consent, provenance, supported evidence, or valid provider output produces a bounded refusal or denial. |
| Reusable trust pattern | The same policy-bound context and receipt model can guard other sensitive personal-agent workflows. |
| Honest ecosystem claims | G5 keeps its exact pending state; no current Sentient or Enclave integration is implied. |

## Trust boundary

SANO follows this sequence:

```text
actor identity and Person scope
  -> delegated access and purpose-bound consent
  -> selected evidence and provenance
  -> disclosure preview
  -> constrained provider execution
  -> output validation
  -> answer or refusal plus execution receipt
```

An external provider is optional. If an action sends context outside the local
installation, the projection must be minimized and authorized for that action;
the user must give explicit per-action consent and the runtime records a
receipt. Raw genome data never enters supported provider context. A self-hosted
operator still owns host, backup, credential, and provider configuration risk.

## Why health is the proving ground

Health context combines high sensitivity with a need for source-backed answers:
documents, medications, labs, visits, family access, and optional genetics all
need clear provenance and boundaries. SANO preserves the original source,
requires human review before canonical promotion, and keeps the assistant from
mutating canonical records. That makes the trust pattern concrete without
claiming diagnosis, treatment, dosage, or clinical authority.

## Existing implementation evidence

The published baseline provides:

- Person-scoped documents, health history, visits and Visit Briefs, family
  access, optional genetics, export, recovery, and audit;
- a policy-bound context contract with explicit disclosure and validation;
- bounded SANO-X2 document text processing, local Russian/English OCR, and
  consented document description and Q&A over selected text and page references;
- provider portability with receipts and fail-closed error handling;
- deterministic evals and security documentation using synthetic or
  de-identified fixtures.

The SANO-X2 capabilities above are already in public `main`. The seven
post-main production/product refinements are integrated in the published main;
`089a5eb` remains their dated pre-integration baseline.

## Future alignment path

The proposed future milestones are:

1. fully local open-weight inference with reproducible RU/EN quality, resource,
   and safety benchmarks;
2. a standalone reproducible sensitive-agent security testbed;
3. conditional evaluation or integration of confidential compute only if its
   public interface is stable and appropriate.

The third milestone is conditional. It may be informed by the [Sentient
product requests](https://sentient.foundation/product-requests), but no
particular Sentient API, Enclave, or deployment is assumed. If the public
interface is unstable or does not preserve SANO’s consent and receipt boundary,
the correct result is a documented evaluation without integration.

## Claims we will preserve

- SANO is self-hosted infrastructure and a reference health workspace.
- Public fixtures are synthetic or de-identified.
- External context is optional, minimized, explicitly consented per action, and
  recorded in a receipt.
- G5 is `READY_FOR_SECOND_CLIENT_SMOKE`, not PASS.
- Evals and benchmarks describe engineering behavior; they do not establish
  clinical validation or medical authority.
