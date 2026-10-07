# SANO Reviewer Quickstart

SANO is a private, source-grounded personal and family health workspace with
auditable AI. The packaged reviewer path takes 3–5 minutes: open Documents,
inspect an original and its provenance, review a consented summary or Q&A,
inspect attribution and the execution receipt, then check Family Access.
Genetics is an optional secondary path.

The current repository truth is recorded in the canonical [judge guide](https://github.com/KirillNedoboy/open-care-proof-kit/blob/main/docs/judge-guide.md),
[project status](https://github.com/KirillNedoboy/open-care-proof-kit/blob/main/docs/project-status.md),
and [live validation record](https://github.com/KirillNedoboy/open-care-proof-kit/blob/main/docs/sano-live-validation.md).
Public `main` at the dated `84fb682` baseline already contains Product Core
schema v13 and SANO-X2: PDF/TXT/JPG/PNG documents, local Russian/English OCR,
and document summary/Q&A. The seven post-`84fb682` production/product
refinements are now integrated in the published main; they do not introduce
those capabilities.

The product name is SANO. The repository name `open-care-proof-kit` and
`opencare-*` package and protocol identifiers remain stable for compatibility.

## Reviewer route

1. Open the live product at [sanobot.art](https://sanobot.art), or run the
   local Docker quickstart from the repository README with synthetic data.
2. In **Documents**, inspect an original PDF, TXT, JPG, or PNG, recognized text,
   and source provenance. Originals remain available before and after OCR.
3. Start a document description or Q&A action. The selected text and page
   references are bounded to the chosen document; external disclosure requires
   explicit per-action consent.
4. Inspect the validated answer, source/page attribution, and execution
   receipt. Model output cannot mutate canonical health records.
5. Open **Workspace** and **Family Access** to inspect review, Person scope,
   explicit revocable grants, and the deny-by-default boundary.
6. Read the [G5 evidence](https://github.com/KirillNedoboy/open-care-proof-kit/blob/main/docs/architecture/sentient-g5-ecosystem-validation.md)
   when reviewing reusable trust infrastructure. The exact G5 state is
   `READY_FOR_SECOND_CLIENT_SMOKE`.

## Local deterministic checks

The packaged commands use synthetic fixtures and do not require a model
provider or external API:

```bash
pytest tests/test_repository_truth.py tests/test_release_metadata.py -q
ruff check app tests evals
mypy app evals
python -m evals.runner
python -m evals.trust_metrics
```

The current validation record preserves the last full canonical run and its
evidence classes. GitHub CI verifies deterministic tests, lint, typing, evals,
trust metrics, and reviewers; it does not execute paid live provider calls.

## Boundaries

- Public fixtures, screenshots, and examples are synthetic or de-identified.
- SANO does not diagnose, recommend treatment or dosage, direct medication
  changes, or claim clinical validation.
- Original documents and provenance remain inspectable; upload does not create
  a reviewed canonical health record.
- Raw genome data never enters the supported provider context.
- OpenRouter/DeepSeek summary and document Q&A production checks are
  operator-confirmed. The OpenAI adapter is tested, while OpenAI live X2 is
  unverified.
