# SANO Grant Submission Answers

> Copy-ready English answers for a public-good or Sentient-related grant form.
> They describe the published SANO baseline and post-main refinements prepared
> for integration. Current implementation truth remains in [project status](project-status.md)
> and the [capability matrix](capability-matrix.md).

## Submission facts

Public GitHub `main` at the dated `84fb682` baseline already contains Product
Core schema v13 and SANO-X2, including local OCR and bounded document
understanding. Seven post-`84fb682` production/product refinements through
`089a5eb` are prepared for integration; they do not introduce those features.
See the dated [live-validation record](sano-live-validation.md) for revision
and CI evidence.

G5 remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`: Agent Skills
interoperability is verified for OMP 17.3.5 and Hermes Agent 0.19.0, while root
Agent Plugins two-client validation remains pending. No production Sentient
integration, Enclave deployment, or confidential-compute support is claimed.

Local-model inference without an external API and the OpenRouter/DeepSeek live
provider flow, including document summary/Q&A, are operator-confirmed. Summary
attribution, Q&A citations, and execution receipts are included in that
confirmation. OpenAI live X2 is unverified. Model,
endpoint, prompt, output, and workflow-specific smoke details are included only
when recorded in the [dated validation report](sano-live-validation.md).

## A. Project title

SANO: private, source-grounded health workspace with auditable AI.

## B. One-sentence pitch

SANO is an open-source, self-hosted health workspace and reusable trust
infrastructure that keeps source, provenance, consent, Person-scoped access,
bounded AI context, validation, and execution receipts inspectable.

## C. Short summary

SANO is a self-hosted workspace for personal and family health information. It
keeps source documents, reviewed health history, visits, optional genetics, and
explicit family access in one Person-scoped system. A source is preserved with
provenance and reviewed before it becomes canonical; model output cannot mutate
canonical records. Public SANO-X2 provides bounded OCR and consented
document description and Q&A. SANO is not a diagnostic or treatment system.

## D. Longer summary

SANO addresses a simple trust problem: a sensitive agent should show what source
it used, which Person and purpose authorized the action, what context was
disclosed, and why it refused unsupported work.

The workspace implements source registration, provenance, human review,
canonical health records, timeline and Visit Brief preparation, family access,
optional genetics, export, recovery, audit, and bounded assistant context. The
reusable trust infrastructure composes actor identity, Person scope, delegated
access, purpose-bound consent, selected evidence, disclosure preview, output
validation, and an execution receipt.

Public fixtures are synthetic or de-identified. A local installation is
designed for user-owned sensitive data. External providers are optional and may
receive only a minimized authorized projection after explicit per-action
consent; each such action produces a receipt. Raw genome data is excluded from
supported provider context. SANO does not diagnose, prescribe, recommend
dosage, direct medication changes, or claim clinical validation.

## E. Problem

Health context is scattered across PDFs, portals, notes, and memory. Generic
chat tools can hide provenance, bypass Person boundaries, or state unsupported
health claims. Open-source builders need a concrete trust pattern that can be
run locally and inspected before a model receives sensitive context.

## E2. Why now?

SANO has moved from a trust prototype to a working, source-grounded health
workspace. The next useful step is to make local inference reproducible with
quality, resource, and safety benchmarks in both Russian and English, so
builders can judge the trade-offs on ordinary hardware.

## F. Solution

SANO implements:

- immutable source registration and provenance;
- extraction or candidates followed by human review before canonical records;
- Person-scoped, deny-by-default access with separate genetics grants;
- selected, authorized context with disclosure preview and purpose-bound
  consent;
- bounded provider execution, validated answer or refusal, and an execution
  receipt;
- documents, health records, visits, Visit Briefs, family access, genetics,
  export, recovery, audit, and deterministic evaluation;
- in the published SANO-X2 baseline, local Russian/English OCR and
  consented document description and Q&A using selected text and page
  references.

## G. Why open source?

Trust behavior is more useful when others can inspect and reproduce it. The
repository exposes schemas, provenance rules, authorization contracts, safety
boundaries, receipts, eval cases, security models, and synthetic fixtures.
Builders can adapt the trust layer without adopting a closed health assistant.

## G2. Why this project and builder?

The repository shows a continuous implementation path from reusable trust
contracts to a self-hosted personal and family workspace, including source
provenance, consent, Person-scoped access, validation, and receipts. The grant
would extend this shipped work with reproducible evaluation and an independent
security testbed. This answer makes no claims about private user or team
credentials.

## H. Why self-hosted and local-first?

The installation keeps storage and configuration under the operator’s control,
and public artifacts contain only synthetic or de-identified data. Local
operation supports review of the evidence path without requiring raw health or
genetic data to be uploaded to a hosted service.

When an external provider is deliberately used, the relevant action requires
explicit per-action consent and an execution receipt. The context is minimized
and selected; this does not promise absolute privacy or remove operator and
provider risk.

## I. Who benefits?

- people who want an inspectable private workspace for health context;
- families that need explicit, revocable Person-scoped sharing;
- open-source builders working on sensitive local agents;
- reviewers who need visible sources, policy decisions, and receipts;
- public-good funders seeking reusable trust infrastructure rather than a
  black-box medical assistant.

## J. What is built?

The published baseline includes SANO’s workspace, Person-scoped document
and health-record lifecycle, family access, optional genetics, export, recovery,
bounded assistant context, policy and receipt contracts, provider portability,
security docs, deterministic evals, and synthetic reviewer fixtures. Public
`main` already contains schema v13, local OCR, and bounded document
understanding. Seven post-main production/product refinements remain prepared
for integration.

The exact G5 machine state is `READY_FOR_SECOND_CLIENT_SMOKE`. AlphaGenome is
paused after C.1.

## K. Technical architecture

```text
user-owned source
  -> immutable source and provenance
  -> candidate / review
  -> canonical record
  -> selected Person-scoped context
  -> policy and consent
  -> validated provider result or refusal
  -> audit / execution receipt
```

The architecture keeps health data and authorization upstream of any model. A
model is an interface layer; it is never canonical truth.

## L. Safety model

The system denies access by default, keeps operations Person-scoped, requires
human review for canonical promotion, and refuses unsupported or ungrounded
outputs. Raw genome data never enters supported provider context. Genetics
research uses separate grants and explicit evidence labels.

SANO does not provide diagnosis, treatment recommendation, dosage guidance,
medication selection or start/stop authority, clinical decision support, or
clinical validation.

## M. Evaluation and audit

Repository tests, deterministic evals, trust metrics, security documentation,
and receipts provide engineering evidence. Local inference without an
external API and the OpenRouter/DeepSeek live document summary/Q&A flow are
operator-confirmed, including attribution and citations. OpenAI live X2 is
unverified, and no claim of a reproducible
quality or safety benchmark is made.

## N. Why Sentient / public-good alignment?

The project addresses the same public-good question faced by any ecosystem that
helps agents act on private context: how can users and builders inspect the
authorization, evidence, disclosure, validation, and failure behavior?

SANO offers a runnable health reference and reusable trust contracts. It does
not assume current Sentient integration, a Sentient identity bridge, Enclave
deployment, or confidential compute. Any future ecosystem work is conditional
on a stable, appropriate public interface and must preserve explicit consent,
minimized context, provenance, and receipts. See the [official product
requests](https://sentient.foundation/product-requests) as a public input to
that evaluation.

## O. Proposed future milestones

1. Fully local open-weight inference with reproducible RU/EN quality, resource,
   and safety benchmarks.
2. A standalone reproducible security testbed for sensitive agents.
3. Conditional evaluation or integration of confidential compute only if its
   public interface is stable and appropriate.

These are outcome areas, not a promised amount, calendar, or release date.

## P. Public reviewer route

Use the [judge guide](judge-guide.md) for a 3–5 minute path through Documents,
the original and provenance, bounded summary/Q&A, disclosure and consent,
execution receipt, and Family Access. Genetics is an optional secondary path.

## P2. Live demo

https://sanobot.art

## Q. Non-goals

SANO does not claim clinical authority, diagnosis, treatment planning, dosage
recommendation, medication start/stop authority, clinical validation, public
SaaS readiness, raw-genome provider upload, or current Sentient/Enclave
integration.
