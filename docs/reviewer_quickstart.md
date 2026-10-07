# SANO reviewer quickstart

Use the [first-five-minute reviewer path](judge-guide.md) for the live SANO product and the current repository boundary. It begins with the [live site](https://sanobot.art) when the operator has supplied reviewer access. The [local Docker quickstart](../README.md#run-sano-locally) is available for synthetic-data review.

For the quickest trust-infrastructure review, follow the evidence in this order:

1. Inspect the Person-scoped source and its original/provenance.
2. Select document text for a description or document Q&A and inspect the explicit consent step.
3. Review the validated response and execution receipt.
4. Check Family Access grants, Person isolation, and revocation behavior.
5. Read the [G5 status and evidence](architecture/sentient-g5-ecosystem-validation.md).

The open-source product name is SANO. The repository name `open-care-proof-kit` and `opencare-*` package and protocol identifiers remain for stability. Public GitHub `main` at the dated `84fb682` baseline already has Product Core schema v13, SANO-X2, PDF/TXT/JPG/PNG support, and local Russian/English OCR. Seven post-main production/product refinements are prepared for integration.

Local-model inference without an external API and OpenRouter/DeepSeek document
summary/Q&A are operator-confirmed, including attribution, citations, and
execution receipts. OpenAI live X2 is unverified. The current G5 machine state
is exactly `READY_FOR_SECOND_CLIENT_SMOKE`; it is not a PASS for the pending
root Agent Plugins gate. SANO makes no clinical-validation, diagnosis,
prescribing, or treatment-authority claim.

See the [dated live-validation record](sano-live-validation.md), [privacy and safety threat model](privacy_safety_threat_model.md), [capability matrix](capability-matrix.md), and [security reporting](../SECURITY.md).
