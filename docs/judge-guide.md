# SANO Judge Guide

> **Candidate checkout:** This branch includes SANO-X2. The published `main` is still at the X1 document boundary until the candidate is published. The walkthrough below describes the code in this checkout.

## 30-second summary

SANO is an open-source, self-hosted personal and family health workspace. It keeps source documents, reviewed health history, visits, optional genetics, and explicit family access in one Person-scoped system. Its key difference from generic document chat is an inspectable evidence lifecycle: source, provenance, human review, canonical record, and then bounded assistance. SANO is not an AI doctor and does not diagnose or prescribe.

## 3–5 minute walkthrough

Start with the [README Docker quickstart](../README.md#run-sano-locally). The development configuration opens a local installation with a deterministic assistant; it does not need a provider key to inspect the screens.

1. Create the installation account at `/bootstrap`. In `/workspace`, create or select a Person you control.
2. Open `/documents`. This candidate accepts PDF, TXT, JPG, and PNG. Embedded PDF text is used where available; image and scanned-PDF recognition runs locally with Russian and English OCR language data (`rus+eng`). The original is stored before recognition. **Uploading does not create a reviewed health record.**
3. Open a document to inspect its source and recognized text. “Create description” opens an explicit consent step. “Ask about this document” opens the document-scoped assistant. These actions use selected recognized text and page references; they do not automatically promote facts into the health record. A live X2 summary through OpenAI has not been verified.
4. Open `/workspace` to inspect records, provenance, review, and timeline. A source-backed candidate must be reviewed or corrected before it becomes canonical. Visit preparation builds a clinician-reviewable brief from selected confirmed records.
5. Open `/family-access` to see explicit access and consent controls. Relationships alone do not grant access.
6. Open `/genetics` only if useful. Genetics is optional and uses separate permissions; it is not needed for the core workflow.

A fresh Person can have an empty health workspace. `/demo/health-vault` is a separate synthetic, read-only reviewer surface rather than live user data.

## Privacy and safety boundaries

- Product Core data is stored in the self-hosted installation.
- Each health operation is Person-scoped; a family relationship alone is not a grant.
- External provider disclosure for document or chat actions requires explicit consent and produces an execution receipt. X2 document actions are bounded to the selected document's recognized text and page references; the original file and unrelated health records are not in that document context.
- Raw genome data is excluded from supported provider context, and genetics permissions are separate.
- Model output does not mutate canonical health records.
- SANO does not diagnose, prescribe, recommend dosage, or claim clinical validation.

## Current candidate evidence and limits

- [Project status](project-status.md) and the [capability matrix](capability-matrix.md)
- [SANO-X1 validation record](sano-x1-validation.md) documents the earlier published X1 baseline; it is not X2 validation evidence.
- [Published CI](https://github.com/KirillNedoboy/open-care-proof-kit/actions)
- Schema v13 and local Russian/English OCR (`rus+eng`) are part of the candidate. The runtime needs Tesseract plus both language packs; the Docker image includes them.
- General OpenRouter consent and receipt use has been verified. A live OpenAI X2 document-summary request remains unverified; Ollama live smoke is deferred/unverified.
- G5 machine state is exactly `READY_FOR_SECOND_CLIENT_SMOKE`; root Agent Plugins two-client validation is pending external evidence. AlphaGenome is paused after C.1.

## Engineering references

[Architecture](architecture.md) · [Privacy threat model](privacy_safety_threat_model.md) · [Family authorization](security/family-access-authorization-matrix.md) · [Provenance](provenance_semantics.md) · [Visit Brief lifecycle](architecture/visit-brief-lifecycle.md) · [Genetics boundaries](architecture/p3-genetics-research-studio.md) · [Deployment](deployment.md)
