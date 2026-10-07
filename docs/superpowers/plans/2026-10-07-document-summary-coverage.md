# SANO document summary coverage and chat guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make summary coverage metadata server-derived, clarify the general assistant's record-only context in RU/EN, and deploy the tested fix to sanobot.art.

**Architecture:** Keep the consent-gated document flow and citations unchanged. Remove coverage flags from the provider output contract, derive the existing result coverage fields from the exact selected text bound to each run, and render accurate localized status. The general chat copy will distinguish saved source-backed records from the existing selected-document question path.

**Tech Stack:** Python 3.12, Pydantic, FastAPI, SQLite, pytest, vanilla JavaScript, Docker Compose, system Caddy.

---

### Task 1: Make coverage metadata server-owned

**Files:**
- Modify: `app/agent/document_summary_trust.py`
- Modify: `app/product_core/document_summary.py`
- Test: `tests/test_product_core_api_documents.py`

- [ ] **Step 1: Update deterministic validator tests first**

Remove `coverage_complete` and `coverage_note` from `_summary_answer()` and synthetic provider answers. Replace the old provider-coverage mismatch cases with tests that a summary without coverage fields validates, citations remain restricted to selected pages, and unexpected provider-supplied coverage fields fail the strict schema. Assert the provider schema and `allowed_fields` omit both metadata keys.

- [ ] **Step 2: Run focused tests and confirm the contract tests fail**

Run: `pytest tests/test_product_core_api_documents.py -q`

Expected: failures identify the old required coverage fields and schema disclosure assertions; all unrelated cases remain unchanged.

- [ ] **Step 3: Remove provider-authored coverage from the trust contract**

Make `DocumentSummaryAnswer` contain only `summary`, `key_points`, `discussion_questions`, and `page_numbers`. Remove coverage keys from `_SUMMARY_DIAGNOSTIC_FIELDS`, `allowed_fields`, and the summary instruction text. Keep page allowlisting, strict validation, unsafe-output rejection, and `summary_invalid` behavior. Bump `SUMMARY_PROMPT_VERSION` from `sano-document-summary-v2` to `sano-document-summary-v3` so prior failed runs are not reused under the new contract.

- [ ] **Step 4: Add one deterministic coverage helper and use it in both response paths**

In `app/product_core/document_summary.py`, use the existing extraction total and selected immutable text projection:

```python
def _coverage_fields(total_chars: int, selected: tuple[tuple[int, str], ...]) -> dict[str, Any]:
    complete = sum(len(text) for _, text in selected) == total_chars
    return {
        "coverage_complete": complete,
        "coverage_note": None
        if complete
        else "Some extracted text was omitted by the document-processing limit.",
    }
```

Use this helper when building the prepare response and after a validated answer returns in `consent_and_execute`. Load the bound extraction snapshot once for the run and use its `total_chars` plus the exact selected projection. Set final status from the derived `coverage_complete`, never from provider output. Keep the existing result fields and database schema.

- [ ] **Step 5: Add full-input and bounded-input service tests**

Assert a complete synthetic source produces `completed`, `coverage_complete=true`, and `coverage_note=null`, even though the synthetic provider returns no coverage keys. In a separate synthetic test, lower `MAX_DOCUMENT_AI_TEXT_CHARS` with `monkeypatch`, process text longer than that limit, and assert `partial`, `coverage_complete=false`, a non-empty server note, and the unchanged citation allowlist. Confirm the provider cannot choose either coverage field.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/test_product_core_api_documents.py -q`

Expected: all document summary and document question tests pass, including safety and receipt assertions.

### Task 2: Explain general versus document-scoped chat

**Files:**
- Modify: `app/ui_localization.py`
- Modify: `app/templates/chat.html`
- Modify: `app/static/sano_documents.js`
- Test: `tests/test_api.py`
- Test: `tests/test_product_shell.py`

- [ ] **Step 1: Update exact localization expectations first**

Add exact RU/EN assertions for the general-chat subtitle directing uploaded-file questions to Documents → “Ask about this document”. Add document-chat subtitle assertions stating questions use only the selected document. Change summary coverage expectations to say the processed extracted text is complete or partial, without using model citation page numbers as a measure of extraction coverage.

- [ ] **Step 2: Run the two affected test modules and confirm the new copy expectations fail**

Run: `pytest tests/test_api.py tests/test_product_shell.py -q`

Expected: only new or updated localization assertions fail.

- [ ] **Step 3: Update localized chat guidance and selected-document subtitle**

Set `chat.subtitle` in both locales to explain that general chat uses saved, source-backed records and that uploaded-file questions belong in the selected-document flow. Add `chat.document_subtitle` in both locales. Select it only when `selected_document` exists in `chat.html`; preserve the existing selected-document context banner, API route, consent, and disclosure behavior.

- [ ] **Step 4: Render truthful coverage status**

In `sano_documents.js`, keep `page_numbers` for citations only. Render the full/partial message from localized coverage strings without interpolating provider citations. Update both locale strings to say whether all or only part of the extracted text was used to prepare the description.

- [ ] **Step 5: Run the two affected test modules**

Run: `pytest tests/test_api.py tests/test_product_shell.py -q`

Expected: both modules pass and both locales expose the distinct chat guidance and truthful coverage text.

### Task 3: Run release checks and deploy the tested commit

**Files:**
- Verify: `docs/production_deployment.md`
- Deploy: tracked application snapshot only; preserve production env, data, backups, and existing system Caddy configuration.

- [ ] **Step 1: Run the canonical validation set once after implementation stabilizes**

Run these commands from the repository root with Python 3.12:

```text
pytest
ruff check app tests evals
mypy app evals
python -m evals.runner
python -m evals.trust_metrics
python -m evals.g5_review
python -m evals.p1_review
python -m evals.p2_review
python -m evals.d1_review
python -m evals.p3_review
python -m pip check
git diff --check
node --check app/static/product_core_workspace.js
node --check app/static/genetics.js
```

Expected: every command exits successfully. Do not weaken a failing test or evaluator.

- [ ] **Step 2: Build and validate the production Compose application**

Run the tracked SANO Compose configuration with the system-Caddy override. Require `docker compose ... config --quiet`, a successful `opencare` image build, and `pip check` inside the built image. Do not start or reload containerized Caddy.

- [ ] **Step 3: Create and verify a pre-deploy backup on the VPS**

Use the existing production Compose project and secret env file without printing their contents. Create a uniquely named Product Core backup under `/opt/sano/backups` and run `backup_cli verify` on that artifact before changing the active release. Record the current release, container image, and rollback tag in the operator notes.

- [ ] **Step 4: Publish the committed tracked snapshot with rollback material intact**

Copy only tracked application files to a new immutable release directory under `/opt/sano/releases`. Preserve `/opt/sano/secrets/env.production` mode `0600`, `/opt/sano/data`, `/opt/sano/backups`, the previous release, previous image, and existing Caddy configuration. Keep app publication bound to `127.0.0.1:18000`; do not expose a new public app port.

- [ ] **Step 5: Recreate only the application container and verify service health**

Run Compose `config --quiet`, build the new application image, and recreate only `opencare`. Verify container health, HTTPS `/healthz` and `/readyz`, HTTP-to-HTTPS redirect, apex/www behavior, and that the only app host binding is `127.0.0.1:18000`. Do not send the real uploaded document to the provider or trigger live summary/Q&A requests. If any gate fails, restore the saved release/image and recheck health before reporting the outcome.

- [ ] **Step 6: Commit the implementation and plan locally; do not push to GitHub**

Commit the source, tests, localization, and plan on `codex/sano-production-deployment`. The requested remote action is publication to the existing VPS; it does not authorize a GitHub push, PR, or merge.
