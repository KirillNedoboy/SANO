# SANO Grant Pitch

> Supporting grant language for the prepared local baseline. Current runtime
> truth is maintained in [project status](project-status.md) and the
> [capability matrix](capability-matrix.md).

## Approved short pitch

SANO: private, source-grounded health workspace with auditable AI.

## Repository and evidence boundary

SANO is the product name for an open-source, self-hosted personal and family
health workspace plus reusable trust infrastructure for agents handling
sensitive personal context. Historical OpenCare names remain in some code and
architecture documents; they do not change the product identity.

Public GitHub `main` at the dated `84fb682` baseline already contains Product
Core schema v13 and SANO-X2, including local OCR and bounded document
understanding. Seven post-`84fb682` production/product refinements through
`089a5eb` are prepared for integration; they do not introduce X2. See the dated
[live-validation record](sano-live-validation.md) for exact source identities
and CI status.

The G5 machine state is exactly `READY_FOR_SECOND_CLIENT_SMOKE`. This records
verified Agent Skills interoperability for OMP 17.3.5 and Hermes Agent 0.19.0
while root Agent Plugins two-client evidence remains pending. No production
Sentient integration or Enclave deployment is claimed.

Local-model inference without an external API and the OpenRouter/DeepSeek live
provider flow, including document summary/Q&A, are operator-confirmed. Summary
attribution, Q&A citations, and execution receipts are included in that
confirmation. OpenAI live X2 is unverified. Model
identities, deployed SHAs, endpoint details, prompts, outputs, and
workflow-specific smoke details are included only when recorded in the dated
[validation report](sano-live-validation.md).

## Problem

Sensitive personal agents need an inspectable path from user-owned context to an
answer. A fluent model response does not show which source was used, whether
the actor was authorized for that Person, what data left the installation, or
why the system refused an unsupported request. Health makes these gaps clear:
documents, medications, visits, family context, and genetics are private, and
unsupported language can cause harm.

Open-source builders need a small trust substrate that can be tested locally
before it is connected to a model or another application.

## Solution

SANO implements a source-grounded lifecycle:

```text
user-owned source
  -> immutable registration and provenance
  -> extraction or candidate
  -> human review
  -> canonical record
  -> timeline / visit preparation
  -> selected authorized context
  -> validated answer or refusal
  -> audit / execution receipt
```

The workspace covers Person-scoped documents, health records, visits and Visit
Briefs, explicit family access, optional genetics, export, and recovery. The
prepared SANO-X2 baseline adds bounded local text recognition and consented
document description and Q&A for selected recognized text and page references.

The reusable trust layer composes actor identity, Person scope, delegated access,
purpose-bound consent, selected evidence, provenance, disclosure preview,
constrained execution, output validation, and a receipt. It is useful without a
genetics workflow and without a particular LLM.

## Privacy and external context

Self-hosting keeps the installation and its operator in control of storage and
configuration. Public fixtures and reviewer artifacts are synthetic or
de-identified. An external provider is optional: when used, the action must
have explicit per-action consent and a receipt, and the context is a minimized
authorized projection. Raw genome data is excluded from supported provider
context. Operator host security, backups, provider terms, and configuration
remain part of the deployment boundary.

This framing describes a system boundary; it does not promise absolute privacy,
zero disclosure, confidential compute, or a secure enclave.

## Reusable trust infrastructure

The pattern is intentionally domain-shaped but reusable:

```text
authorized context
  -> evidence and provenance
  -> policy and disclosure decision
  -> constrained provider execution
  -> validated output or refusal
  -> receipt and audit
```

Health is the reference stress test because it requires strict access, visible
sources, uncertainty, and safety limits. The infrastructure can inform other
sensitive-agent applications without claiming that SANO is already a general
cross-domain platform.

## Why this fits an open public-good grant

The project makes trust behavior reviewable. Builders can inspect the schemas,
authorization contracts, provenance rules, provider boundary, receipts, evals,
security models, and synthetic fixtures. The repository can be run locally and
tested without surrendering raw user context to a hosted service.

The public-good contribution is the reusable boundary around sensitive-agent
behavior: no source, no supported claim; no authorization, no access; no
consent, no external disclosure; provider failure stays bounded; and every
supported external action leaves a receipt.

## Future work

The proposed future milestones are:

1. a reproducible profile for fully local open-weight inference with RU/EN
   quality, resource, and safety benchmarks;
2. a standalone reproducible security testbed for sensitive agents;
3. conditional confidential-compute evaluation or integration only if its public
   interface is stable and appropriate.

The third item is a conditional research path, not a current Sentient or
Enclave integration. It would follow the relevant official public interface,
including the [Sentient product requests](https://sentient.foundation/product-requests),
and preserve consent, minimized context, provenance, and receipts.

No grant amount, delivery date, or funding commitment is specified here.

## Safety boundary

SANO does not claim to diagnose, recommend treatment or dosage, choose or stop
medication, provide clinical decision support, or be clinically validated.
Model output cannot mutate canonical health records. Genetics Research remains
bounded, separately authorized, evidence-labelled, and unable to turn a
hypothesis into a canonical fact.
