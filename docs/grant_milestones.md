# SANO Future Milestones

> Supporting grant context. These are proposed future work areas; they do not
> define a release schedule, funding amount, product phase, or current
> capability. See [project status](project-status.md) for current evidence.

SANO is a self-hosted, source-grounded health workspace and a reusable trust
infrastructure reference for sensitive personal agents. Future work should
make the trust boundary more reproducible and useful while preserving
Person-scoped authorization, provenance, consent, receipts, and the clinical
safety boundary.

Approved short pitch: **SANO: private, source-grounded health workspace with auditable AI.**

## Current baseline

Public GitHub `main` at the dated `84fb682` baseline already contains SANO-X2
and Product Core schema v13. Seven post-`84fb682` production/product
refinements through `089a5eb` are prepared for integration and do not introduce
those capabilities. No future milestone below should be read as evidence of
Sentient integration or confidential-compute deployment. See the dated
[validation record](sano-live-validation.md) for exact source identities.

G5 remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`. AlphaGenome remains paused
after C.1. Local inference without an external API and the OpenRouter/DeepSeek
live provider flow, including document summary/Q&A, attribution, citations, and
receipts, are operator-confirmed. OpenAI live X2 is unverified. See the dated
validation record for the evidence boundary.

## Milestone 1 — Reproducible fully local open-weight inference

Build a reproducible profile for fully local open-weight inference behind the
existing policy-bound context and receipt boundary. The profile should include
RU/EN quality, resource, and safety benchmarks, with pinned inputs, documented
runtime requirements, repeatable commands, and clear refusal behavior.

Acceptance evidence:

- a reviewer can reproduce the run on a documented local setup without an
  external API;
- RU and EN quality results are reported with the task set and limitations;
- resource measurements identify model/runtime requirements and failure modes;
- safety tests cover unsupported claims, disclosure, provenance, and refusal;
- model output remains an interface layer and cannot mutate canonical records.

This milestone does not promise a particular model, score, hardware profile, or
clinical performance.

## Milestone 2 — Standalone sensitive-agent security testbed

Extract the trust checks into a standalone, reproducible security testbed for
agents handling sensitive personal context. It should exercise authorization,
Person isolation, purpose-bound consent, minimized disclosure, provenance,
receipt integrity, provider failure, and fail-closed refusal across repeatable
fixtures.

Acceptance evidence:

- a clean checkout can run the testbed without private user data;
- fixtures are synthetic or de-identified and include both allowed and denied
  paths;
- reports identify the exact contract, fixture, and check that produced each
  result;
- the testbed cannot mint live authorization or grant access by test setup;
- security findings are separated from clinical validation claims.

This milestone does not create a SaaS tenancy model, a diagnosis system, or a
new authority source for health records.

## Milestone 3 — Conditional confidential-compute evaluation

Evaluate confidential-compute options only if the relevant public interface is
stable and appropriate for SANO’s consent, disclosure, provenance, and receipt
requirements. Any integration decision would follow a documented privacy and
security review and the official public interface, such as the [Sentient
product requests](https://sentient.foundation/product-requests).

Acceptance evidence, if the condition is met:

- the public interface and version are identified and independently reviewable;
- the data path, trust assumptions, failure behavior, and operator controls are
  documented;
- per-action consent, minimized context, and execution receipts remain intact;
- a local or no-integration result is acceptable when the interface is not
  stable or appropriate.

No confidential-compute, Enclave, or Sentient deployment is claimed today.

## Guardrails for all milestones

- Keep the repository’s public fixtures synthetic or de-identified.
- Preserve the source -> provenance -> review -> canonical record lifecycle.
- Keep external disclosure optional, minimized, explicitly consented per action,
  and recorded in a receipt.
- Keep raw genome data outside supported provider context.
- Do not add diagnosis, treatment, dosage, medication start/stop authority, or
  clinical validation claims.
- Do not invent a grant amount, deadline, delivery date, or integration result.
