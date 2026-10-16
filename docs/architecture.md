# Architecture

This document describes the current public main implementation. Product Core schema v13 and SANO-X2 are published; historical phase notes remain in the roadmap and ADRs. Runtime ownership and dependency rules are canonical in [module boundaries](architecture/module-boundaries.md), while dated delivery facts are recorded in [project status](project-status.md).

## Product flow

~~~text
user-owned source
  -> immutable Source registration
  -> extraction or candidate fact
  -> provenance and human review
  -> canonical Person-scoped record
  -> timeline / Visit preparation
  -> selected authorized context
  -> validated answer or refusal
  -> audit / Execution Receipt
~~~

AI output never promotes itself into canonical truth. Document summaries and document questions are separate, consent-gated projections; they do not create reviewed health records.

## Current module map

| Area | Ownership |
| --- | --- |
| app/product_core | Product Core schema v13: Sources, candidates, canonical records, timeline, Visits, Visit Briefs, document processing, genetics persistence, export, backup, and recovery. |
| app/family_access | Actor sessions, Person authorization, relationships, assignments, consent, and frozen Family Access generations. |
| app/agent_trust | Generic Trust Envelope, policy-bound authorization, schemas, validation, and portable trust package contracts. |
| app/agent | Minimized context, providers, disclosure, consent-gated execution, validation, and audit. |
| app/genetics | Consumer-genotype parsing, normalization, evidence, comparison, and bounded Research contracts. |
| app/health_vault | Synthetic reviewer/demo vault, deterministic read model, artifact generation, and trace graph. It is separate from live Actor-scoped Product Core data. |
| app/static and app/templates | Authenticated workspace, Documents, Genetics, Family Access, chat, demo, and shared product-shell surfaces. |
| evals and tests | Deterministic phase reviewers, trust metrics, contract tests, security checks, and browser acceptance helpers. |

## Evidence and authorization boundaries

Product Core preserves original source bytes and integrity metadata before any derived extraction. Candidate facts retain source and locator provenance until a person reviews them. Unsupported, conflicting, absent, no-call, build-incompatible, and ambiguous states remain explicit.

Every live health operation resolves the authenticated Actor, explicit Person, assignment and scope generation through the centralized policy. Relationships do not grant access. Genetics grants (genetics.read, genetics.write, genetics.research, genetics.compare, and genetics.export) remain separate from ordinary Family Access. Revocation applies to the next authorization decision.

The agent receives a selected projection, never unrestricted vault or database access. External disclosure requires purpose-bound consent. Provider responses are strictly validated, citations are checked against selected evidence, and receipts record the result. Agent output and Research hypotheses cannot mutate canonical records.

## Documents and genetics

The document path supports bounded local TXT/PDF text extraction and local Tesseract OCR for PDF, TXT, JPG, and PNG flows. The original bytes and extracted page text remain source/provenance material. Normal agent context contains only an explicitly selected authorized projection.

Genetics imports are bounded consumer-genotype workflows. Raw genome bytes are highly sensitive and never enter provider context. Ambiguous orientation, missing chip coverage, incompatible builds, and unresolved evidence fail closed; absence from supplied coverage is not treated as a negative finding. Family comparison is compatibility/IBS-style evidence, not legal or forensic kinship proof.

## Synthetic reviewer surfaces

The legacy Health/Family Vault pipeline remains useful for deterministic review:

~~~text
data/demo_patients/demo_family_vault.json
  -> app.health_vault.loader
  -> app.health_vault.read_model
  -> app.health_vault.artifacts
  -> docs/assets/health_vault/
~~~

The /demo/health-vault route is read-only and uses synthetic data. It does not share live Actor sessions, Product Core authorization, or user-owned records. The original Medication-to-Doctor Briefing and PGx demo path remains separate from the live workspace.

## Trust and ecosystem status

G1 through G5, P1, P2, D1, and P3 are implemented on public main; there is no G6. Agent Skills interoperability is verified across OMP 17.3.5 and Hermes Agent 0.19.0. The root Agent Plugins two-client evidence gate remains exactly READY_FOR_SECOND_CLIENT_SMOKE. The current capability and validation boundaries are in the [capability matrix](capability-matrix.md) and [live validation record](sano-live-validation.md).
