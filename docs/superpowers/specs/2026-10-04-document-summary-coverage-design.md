# SANO document summary coverage and chat guidance

## Problem

A production document-summary attempt reached the provider and then failed local
validation with the safe diagnostic `coverage_inconsistent`. The provider's
coverage flags can disagree with the extraction and page projection already
known by SANO. Separately, the general assistant does not receive raw uploaded
document pages; it answers from saved, source-backed records. The current page
copy does not make the separate document-question path clear enough.

## Design

Coverage is a server-owned fact. The provider-facing summary contract will
contain summary content and page citations, but not `coverage_complete` or
`coverage_note`. After successful content validation, the summary service will
derive whether all extracted text was included from the exact immutable page
projection bound to the run. It will populate the existing result coverage
fields consistently: complete input coverage has `coverage_complete=true` and
no note; truncated input has `coverage_complete=false` and a truthful
server-generated note. Provider citations remain model output and continue to
be checked against the selected pages. The displayed coverage message will
describe how much source text was processed; it will not claim every page is
represented in the generated summary. No database migration or public endpoint
change is needed.

The general assistant will state in Russian and English that it uses
source-backed saved records. It will direct people asking about an uploaded
file to open that file in Documents and choose “Ask about this document”. The
existing document-scoped chat continues to use only the selected document's
recognized pages, with its existing disclosure and consent flow. No raw
document pages will be added to general chat context.

## Safety and scope

The fix preserves local schema, authorization, consent, citations, provenance,
output validation, and medical-safety boundaries. It does not retry the prior
provider request, inspect or disclose the uploaded report, or make medical
claims. It does not change providers, OCR, persistence architecture, public API
contracts, or production data and configuration.

## Verification

Deterministic tests will cover full and truncated source coverage, invalid
citations and summary content, server ownership of coverage metadata, and the
general-versus-document chat guidance in both locales. Tests will also verify
that the successful synthetic summary still follows prepare, consent,
execution, validation, and receipt without a live provider call. Relevant
focused tests and the repository's required checks for changed Python code
will run after implementation. Production rollout is a separate action and is
not included in this code change.
