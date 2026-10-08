# SANO judge guide

## 30-second overview

SANO is an open-source, self-hosted personal and family health workspace. It keeps source documents, reviewed health history, visit preparation, and explicit family access in one Person-scoped system. Its reusable Trust Envelope, authorization, consent, output validation, receipts, portable schemas, and deterministic evaluations also provide a proving ground for sensitive personal AI agents. SANO does not diagnose or prescribe.

## 3–5 minute reviewer path

Open the [live product](https://sanobot.art) with reviewer access provided by the operator. Alternatively, follow the [local Docker quickstart](../README.md#run-sano-locally) using synthetic sample data.

1. In **Documents**, select or upload a synthetic PDF, TXT, JPG, or PNG. Recognition of scanned PDFs and images uses local Tesseract OCR with Russian and English data (`rus+eng`). The original is retained before recognition.
2. Open the original and inspect its recognized text and provenance. An upload does not create a canonical health record.
3. Try **Create description** or **Ask about this document**. These are separate actions, use selected document text and page references, and request explicit consent before an external provider disclosure.
4. Inspect the generated response and execution receipt. The receipt records provider identity and outcome; model output cannot edit health records.
5. Open **Family Access** to inspect explicit Person-scoped grants. A family relationship alone grants no access. Open **Workspace** to review source-backed facts and the human review step before promotion.
6. If time permits, inspect **Trust & security** or the optional Genetics area. Genetics uses separate permissions and is not needed for the core product.

The product may have no records for a newly selected Person. `/demo/health-vault` is a separate synthetic, read-only surface and is not a view of live user data.

## Privacy and safety

- Each health action is authorized for an explicit Person. Access is deny-by-default and revocable.
- Provider context is limited to the selected authorized projection. External disclosure is optional and requires consent for each action.
- Originals and provenance remain inspectable. Candidate facts require human review before becoming canonical.
- Raw genome data never enters supported provider context. Model output and Research hypotheses cannot mutate canonical records.
- SANO makes no diagnosis, treatment, dosage, clinical authority, or clinical-validation claim.

## Evidence and current boundaries

- Public GitHub `main` at the dated `84fb682` baseline includes Product Core schema v13, SANO-X2, PDF/TXT/JPG/PNG support, local `rus+eng` OCR, and document summary/Q&A. The seven post-main production/product refinements through `089a5eb` are now integrated in the published main.
- Local-model inference without an external API and the OpenRouter/DeepSeek live
  provider flow, including document summary/Q&A, are operator-confirmed. Summary
  attribution, Q&A citations, and execution receipts are also operator-confirmed.
  OpenAI live X2 is unverified; see the dated live-validation record.
- The [dated live-validation record](sano-live-validation.md) records the dated CI, local validation, operator checks, and remaining declared limitations.
- The G5 state is exactly `READY_FOR_SECOND_CLIENT_SMOKE`. AlphaGenome is paused after C.1.

## Engineering references

[Architecture](architecture.md) · [Privacy threat model](privacy_safety_threat_model.md) · [Family authorization](security/family-access-authorization-matrix.md) · [Provenance](provenance_semantics.md) · [Genetics boundaries](architecture/p3-genetics-research-studio.md) · [Deployment](deployment.md)
