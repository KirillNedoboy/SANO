# SANO

**Your private health workspace, grounded in evidence.**

SANO is an open-source, self-hosted workspace for personal and family health information. It keeps source documents, reviewed health history, visits, optional genetics, and explicit access controls in one Person-scoped system. Its purpose is to help people organize evidence and prepare for conversations with clinicians—not to diagnose or prescribe.

![SANO X2 document view with a synthetic sample and consent controls](docs/assets/sano-x2/documents-1440.webp)

*The X2 document view from this candidate checkout. The sample is fictional. A description requires consent; the screenshot does not show or claim a live OpenAI result.*

> **Candidate status:** This checkout includes SANO-X2. The currently published `main` remains at the X1 document boundary until a later publication; this README describes the candidate represented by this branch.

## What makes SANO different

A generic document chat can send a file to a model and return an answer. SANO centers the source and the path from evidence to a reviewed health record:

```text
source → provenance → Person scope → human review → health record
       → timeline / visit preparation → bounded assistant
```

Uploading a document stores its original and supports local text recognition. **It does not automatically create a reviewed medical record.** In supported extraction flows, a person reviews or corrects source-backed candidates before they enter canonical health history. The assistant is a bounded interface to selected information; it cannot write canonical records.

## Capabilities in this checkout

- **Documents:** Person-scoped storage for PDF, TXT, JPG, and PNG. Embedded PDF text is used where available; scanned PDFs and images can use local OCR with Russian and English language data (`rus+eng`). Original bytes are retained if recognition fails.
- **Document understanding:** An optional short description and “Ask about this document” action use selected recognized text and page references. Each provider action requires explicit consent. A live X2 summary call through OpenAI has **not been verified**.
- **Health history:** medication, recorded-condition, and lab records with source provenance, review, correction history, and a timeline. A recorded condition is not a diagnosis.
- **Visit preparation:** save visits and questions, build a clinician-reviewable Visit Brief from selected confirmed records, and export it.
- **Family access:** explicit, revocable Person-scoped grants; a family relationship alone does not grant access.
- **Optional genetics:** bounded local consumer-genotype workflows, reviewed findings, and family comparison under separate genetics permissions. This is not clinical interpretation.
- **Assistant:** explain selected authorized evidence through a consent-aware runtime. Provider execution produces a receipt; model output cannot mutate canonical health records.

Product Core schema v13 adds document text-processing and summary state in this candidate. OCR requires the documented runtime to include Tesseract and its `eng` and `rus` language packs; the Docker image includes them.

## Evidence stays inspectable

Sources remain available alongside provenance. Derived text and summaries do not replace the original. Where a supported workflow extracts candidate facts, a person reviews or corrects them before promotion. The timeline and Visit Brief use selected confirmed information, not model-generated claims.

## Run SANO locally

Requires Docker with Compose. This is a local development quickstart for inspection, not an internet-facing production setup.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open [http://127.0.0.1:8000/bootstrap](http://127.0.0.1:8000/bootstrap) and create the first local account. Then visit `/documents`, `/workspace`, `/family-access`, `/genetics`, and `/chat`. The development configuration uses demo mode and a deterministic local assistant by default; no provider key is needed to inspect the UI. To use an external provider, an operator must configure it and the user must grant the action's explicit consent. See [local deployment](docs/deployment.md) and [production deployment](docs/production_deployment.md) for their respective setup boundaries.

## Privacy and safety

SANO is designed for self-hosting. Stored Product Core data stays in the operator's installation. Requests are authorized for a specific Person, and external provider disclosure follows an explicit consent flow and creates an execution receipt. For X2 document actions, the selected document's recognized text and page references form the relevant context; the original file and unrelated health records are not part of that document action. Raw genome data is excluded from supported model context.

Repository fixtures, screenshots, and reviewer examples use synthetic or de-identified data. A self-hosted deployment still depends on the operator's host security, configuration, and backup practices.

## Current limits

- OCR and X2 document understanding are included in this local candidate, not the currently published X1 `main`.
- Live OpenRouter consent and receipt flow has been verified for the general guarded runtime. A live OpenAI X2 document-summary call is unverified; Ollama live smoke is deferred/unverified.
- G5 machine state remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`; the root Agent Plugins two-client gate awaits external evidence.
- AlphaGenome is paused after C.1.
- SANO is not clinically validated software, an AI doctor, diagnostic authority, treatment planner, medication or dosage authority, or clinical decision-support system.

See [current candidate status](docs/project-status.md), the [capability matrix](docs/capability-matrix.md), and the [judge guide](docs/judge-guide.md) for an accurate tour of this checkout. Historical validation reports describe their recorded runs, not a guarantee about the current environment.

## Engineering references

- [Architecture overview](docs/architecture.md) · [module boundaries](docs/architecture/module-boundaries.md)
- [Privacy and safety threat model](docs/privacy_safety_threat_model.md) · [Family authorization matrix](docs/security/family-access-authorization-matrix.md)
- [Evidence provenance](docs/provenance_semantics.md) · [Visit Brief lifecycle](docs/architecture/visit-brief-lifecycle.md)
- [Genetics Research Studio boundaries](docs/architecture/p3-genetics-research-studio.md) · [Trust runtime threat model](docs/security/agent-trust-threat-model.md)
- [Deployment](docs/deployment.md) · [Security reporting](SECURITY.md)

The repository retains historical OpenCare and Sentient names where they identify internal modules, APIs, and engineering history. SANO is the product name.
