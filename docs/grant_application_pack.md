# SANO Grant Application Pack

> Supporting grant material. This pack describes the published SANO baseline,
> post-main refinements prepared for integration, and proposed future work; it
> does not define runtime semantics. See [project
> status](project-status.md), the [capability matrix](capability-matrix.md),
> and the [judge guide](judge-guide.md) for repository truth.

## Project title

SANO: private, source-grounded health workspace with auditable AI.

SANO is an open-source, self-hosted personal and family health workspace plus
reusable trust infrastructure for agents handling sensitive personal context.

## Prepared baseline and public-main boundary

Public GitHub `main` at the dated `84fb682` baseline already includes Product
Core schema v13 and SANO-X2: PDF/TXT/JPG/PNG support, local OCR, and bounded
document summary/Q&A. The seven post-`84fb682` production/product refinements
through `089a5eb` are prepared for integration; they do not introduce those
capabilities. Exact revisions are in the dated [live-validation
record](sano-live-validation.md).

The exact G5 machine state is `READY_FOR_SECOND_CLIENT_SMOKE`. Agent Skills
interoperability is verified for OMP 17.3.5 and Hermes Agent 0.19.0; root Agent
Plugins two-client evidence remains pending. No production Sentient integration,
Enclave deployment, or confidential-compute support is claimed.

Local-model inference without an external API and the OpenRouter/DeepSeek live
provider flow, including document summary/Q&A, are operator-confirmed; summary
attribution, Q&A citations, and execution receipts are included in that
operator confirmation. See the dated evidence in [project status](project-status.md).
OpenAI live X2 document summary/Q&A is unverified: no separate evidence for
that workflow was supplied. Model identities,
deployed SHAs, endpoints, prompts, response samples, and workflow-specific
smoke details are not invented here.

## Approved short pitch

> SANO: private, source-grounded health workspace with auditable AI.

## Short description

SANO gives people and families a self-hosted place to organize source
documents, reviewed health history, visits, optional genetics, and family
access. The product preserves the path from source to provenance to human review
before a record becomes canonical. A bounded assistant can explain selected
authorized evidence, but model output cannot mutate canonical health records.

The shared trust layer makes actor identity, Person scope, consent, selected
context, disclosure, validation, and execution receipts explicit. It is useful
without genetics and without a particular LLM.

## Problem

Sensitive personal context is scattered across documents, portals, notes, and
memory. Generic chat tools can hide provenance, blur authorization, and produce
unsupported health language. Builders need an inspectable way to determine what
data was used, what policy allowed access, what left the local installation,
and why a request was refused.

Health is a demanding reference domain because documents, medications, visits,
family context, and genetics are private and uncertainty matters. The trust
pattern should be available before a builder connects an agent to a model or a
hosted service.

## What SANO provides

- Person-scoped documents, health records, visits and Visit Briefs, family
  access, optional genetics, export, recovery, and audit;
- immutable source registration and provenance with human review before
  canonical promotion;
- deny-by-default authorization and separate genetics grants;
- policy-bound assistant context, explicit disclosure preview, output
  validation, bounded refusal, and execution receipts;
- the published SANO-X2 path for PDF/TXT/JPG/PNG, local `rus+eng` OCR, and
  consented document description and Q&A over selected recognized text and
  page references;
- deterministic evals, trust metrics, security documentation, and synthetic
  reviewer fixtures.

These SANO-X2 capabilities are already part of public `main`. The seven
post-main production/product refinements are prepared separately for
integration.

## Reusable trust infrastructure

```text
user-owned source
  -> immutable registration
  -> extraction or candidate
  -> provenance and human review
  -> canonical record
  -> selected authorized context
  -> policy and disclosure decision
  -> validated answer or refusal
  -> audit / execution receipt
```

The infrastructure is intentionally inspectable and domain-shaped. It can be
adapted to other sensitive-agent workflows, but SANO does not claim to be a
general cross-domain platform in production.

## Privacy and safety

Public fixtures, screenshots, and reviewer artifacts are synthetic or
de-identified. A self-hosted installation is designed for user-owned sensitive
data. External context is optional; when used, it is a minimized authorized
projection sent only after explicit per-action consent and recorded in an
execution receipt. Raw genome data never enters supported provider context.
Operator host security, configuration, credentials, backups, and provider
terms remain part of the deployment boundary.

SANO is not an AI doctor, diagnostic authority, treatment planner, dosage or
medication authority, clinical decision-support system, or clinically validated
software. Explore hypotheses stay labelled and cannot silently become canonical
facts.

## Reviewer route

Use the [judge guide](judge-guide.md) for a 3–5 minute walkthrough:

1. Start in `/documents` and inspect an original, recognized text, and
   provenance.
2. Review the bounded summary or document Q&A flow and its selected context.
3. Inspect disclosure and consent before an external action, then inspect its
   receipt.
4. Open `/workspace` and `/family-access` to see review, Person scope, and
   revocable grants.
5. Treat `/genetics` as an optional secondary path; it is separately
   authorized and not required for the core workspace.

## Why open source and why this grant

Open source lets reviewers and downstream builders inspect contracts, schemas,
authorization, provenance, receipts, evals, and security models. A public-good
grant would support reproducible local inference evidence, a standalone
sensitive-agent security testbed, and careful evaluation of future interfaces
without turning the project into a closed health chatbot.

The proposed future work is described in [grant milestones](grant_milestones.md).
It does not specify an amount or schedule. Confidential compute is a
conditional research path only if its public interface is stable and
appropriate; the [Sentient product requests](https://sentient.foundation/product-requests)
page is a public reference for that evaluation, not evidence of integration.

## Evidence statement

Operator-confirmed evidence includes local inference without an external API
and OpenRouter/DeepSeek live document summary/Q&A, with attribution, citations,
and execution receipts. OpenAI live X2 document summary/Q&A remains unverified
because no evidence for that workflow was provided. See the dated [validation
record](sano-live-validation.md); model
names, endpoints, prompts, outputs, and run details are stated only where
recorded there.

## Guardrails

Use “source-grounded”, “self-hosted”, “Person-scoped”, “explicit consent”,
“minimized projection”, “execution receipt”, and `READY_FOR_SECOND_CLIENT_SMOKE`.

Do not claim current Sentient integration, Enclaves, confidential-compute
deployment, clinical authority, or a funding amount/date.
