# ADR 0007: Server-owned document summary coverage

- Status: Accepted
- Date: 2026-10-07
- Decision owners: SANO maintainers
- Implementation: Published on main; no schema or public endpoint change

## Context

Document summaries are prepared from an immutable, selected text projection. The provider can describe summary content and cite selected pages, but it does not know the extraction limit that produced the projection. Provider-authored coverage flags could therefore disagree with the source text actually bound to the run. General chat also uses saved, source-backed records; it does not receive raw uploaded document pages. Questions about an uploaded file need the separate selected-document flow.

## Decision

Coverage is a server-owned fact. The provider-facing summary contract contains only summary, key_points, discussion_questions, and page_numbers. After strict content and citation validation, the summary service compares the exact selected immutable text projection with the extraction total and derives the existing coverage_complete and coverage_note result fields. Complete input coverage reports coverage_complete=true with no note. Bounded input reports coverage_complete=false with a server-generated explanation. Provider output cannot choose either field.

page_numbers remains model output used for citation allowlisting; it is not a measure of how much extracted text was processed. The summary prompt contract version is bumped when this provider contract changes so failed runs from the older contract are not reused.

General chat explains that it uses saved source-backed records and directs uploaded-file questions to Documents → “Ask about this document”. Document-scoped chat uses only the selected document's recognized pages and keeps its existing disclosure, consent, citation, authorization, and receipt boundaries. Raw document pages are not added to general chat context.

## Consequences

The existing result fields and persistence remain compatible; no database migration or public endpoint change is required. Coverage status remains truthful when extraction is bounded, while citation validation continues to protect the selected-page boundary. The decision preserves local/self-hosted execution, Person authorization, human review, provenance, medical-safety limits, and the rule that document summaries do not create canonical records.

## Verification

Deterministic tests cover complete and bounded input, strict rejection of provider-supplied coverage fields, selected-page citation validation, the consent and receipt path, and distinct English/Russian general and document-scoped chat guidance.
