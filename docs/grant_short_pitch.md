# SANO Grant Short Pitch

> Supporting grant language. This file describes the prepared local grant
> baseline and does not change product or runtime behavior. Current repository
> truth remains in [project status](project-status.md) and the [capability
> matrix](capability-matrix.md).

## Approved short pitch

> SANO: private, source-grounded health workspace with auditable AI.

## State and evidence boundary

Public GitHub `main` at the dated `84fb682` baseline already contains Product
Core schema v13 and SANO-X2, including local OCR and bounded document
understanding. Seven post-`84fb682` production/product refinements through
`089a5eb` are prepared for integration; they do not introduce those features.
See the dated [validation record](sano-live-validation.md) for exact revision
identities.

The exact G5 machine state remains `READY_FOR_SECOND_CLIENT_SMOKE`. Agent
Skills interoperability is verified for OMP 17.3.5 and Hermes Agent 0.19.0;
the root Agent Plugins two-client evidence remains pending.

Local-model inference without an external API and the OpenRouter/DeepSeek live
provider flow, including document summary/Q&A, are operator-confirmed. Summary
attribution, Q&A citations, and execution receipts are included in that
confirmation. OpenAI live X2 is unverified. Model,
endpoint, prompt, output, and workflow-specific smoke details are limited to the
dated [validation record](sano-live-validation.md).

## 15-second pitch

SANO is an open-source, self-hosted health workspace that keeps source
documents, reviewed health history, access decisions, and AI receipts together.
It gives sensitive-agent builders a small, inspectable trust boundary instead
of an opaque health chatbot.

## 30-second pitch

SANO is a private, source-grounded workspace for personal and family health
information. It preserves originals and provenance, scopes every health action
to a Person, requires human review before canonical records, and makes consent,
selected context, disclosure, validation, and execution receipts visible. The
same trust infrastructure can be reused by agents handling other sensitive
personal context. SANO does not diagnose, prescribe, or change canonical
records through model output.

## 60-second pitch

SANO starts with the evidence lifecycle: a user-owned source is registered,
kept with provenance, transformed into a candidate when supported, reviewed by
a person, and only then used in a timeline, Visit Brief, or bounded assistant
context. The self-hosted workspace covers documents, health history, visits,
family access, optional genetics, export, recovery, and audit. The trust layer
adds deny-by-default authorization, purpose-bound consent, selected evidence,
disclosure previews, output validation, and execution receipts.

The public repository contains synthetic or de-identified fixtures. A local
installation is designed for user-owned sensitive data. An external provider
may receive only an authorized, minimized projection after explicit per-action
consent, and the action produces a receipt; raw genome data is excluded from
supported provider context. SANO is a trust and workspace reference, not an AI
doctor, diagnostic authority, treatment planner, dosage authority, or clinically
validated system.

## Reviewer summary

- SANO is open-source and self-hosted, with health as the reference stress test.
- The evidence path is source -> provenance -> human review -> canonical record
  -> bounded context -> validated answer or refusal -> receipt.
- Person-scoped access, separate genetics grants, explicit consent, and
  fail-closed authorization protect sensitive context.
- The published baseline includes SANO-X2 document text processing, local
  Russian/English OCR, and consented document description and Q&A flows.
- The reusable trust layer is inspectable through contracts, tests, evals,
  receipts, and security documentation.

## Technical summary

- Public `main` includes Product Core schema v13 and SANO-X2.
- Documents retain original bytes and provenance; local OCR uses `rus+eng`
  when the runtime supplies Tesseract and language data.
- Document descriptions and questions use selected recognized text and page
  references after explicit provider-bound consent.
- Family access is explicit and revocable; relationships alone do not grant
  health or genetics access.
- Trust contracts cover policy-bound context, disclosure, validation, receipts,
  provider portability, audit, and deterministic evaluation.

## Safety summary

- Public fixtures, screenshots, and reviewer artifacts are synthetic or
  de-identified.
- Uploading a document does not create a reviewed health record.
- Model output cannot mutate canonical records.
- Raw genome data never enters supported provider context.
- Explore hypotheses remain labelled and cannot become diagnosis, treatment,
  medication, or dosage instructions.
- Evals and trust metrics are engineering evidence, not clinical validation.

## Wording guardrails

Use:

- “SANO” for the product and “reusable trust infrastructure” for the shared
  agent boundary;
- “self-hosted”, “source-grounded”, “Person-scoped”, “explicit consent”, and
  “execution receipt”;
- “operator-confirmed” for the local inference and OpenRouter/DeepSeek live
  summary/Q&A evidence above;
- `READY_FOR_SECOND_CLIENT_SMOKE` exactly for the G5 state.

Avoid:

- claims that SANO is integrated with Sentient or deployed in Enclaves;
- “zero-knowledge”, “fully private” without the operator and consent caveat,
  or any promise of confidential compute;
- “AI doctor”, diagnosis, treatment recommendation, dosage guidance, medication
  authority, clinical decision support, or clinical validation.
