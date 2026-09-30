# SANO-A1 local validation — 2026-09-26

## Scope

Local branch `codex/sano-a1`, based on UI-R4.1 commit
`1a8f21788768ae6a67d9e62ba71858eae7dcf95a`. No merge, push, release or remote deployment.

- Sano identity, login/registration titles, favicon, and six primary destinations.
- Documents are the default destination. Health uses one selected view and a compact
  selector for the existing records, review, timeline, visits and export functions.
  Family and Settings present separate views of the existing authorized workspace.
- Immutable PDF/TXT originals, including valid PDFs with no text, year groups,
  undated group, title/filename search, original view/download and editable metadata.
- Local PDF rendering with page controls and enlargement for small screens; TXT uses
  escaped text rendering. Vendored PDF.js assets do not request an external CDN.
- Metadata migration v12 preserves existing Source identities, content and record lifecycle.
- Person-scoped hash deduplication preserves user edits. Originals require document.read;
  metadata edits require document.write. Integrity and safe filenames are checked.
- Upload does not call D2 or providers and does not create candidate/canonical health facts.

## Verification

Python 3.12 in an isolated local runtime environment. All test inputs and browser screenshots
are synthetic; no user document, genome, credential or account identifier is included here.

- Archive focused tests: 10 passed.
- Backup/recovery/source and migration compatibility tests: 39 passed.
- Local account login after v11 recovery is exercised with synthetic credentials.
- Ruff, mypy (134 source files), pip check and changed JavaScript syntax checks pass.
- Deterministic runner, trust metrics, G5, P1, P2, D1 and P3 evaluators pass.
  G5 evaluator success does not change the external root plugin gate.
- Desktop archive and PDF/TXT originals were inspected. On a 390px viewport, TXT wraps;
  date clearing moves the card to the undated group, edits persist after runtime restart,
  and PDF enlargement is available. Keyboard activation was exercised.
- Full migration run: 1094 passed, 4 skipped, 4 existing deprecation warnings;
  one navigation ownership assertion failed. Routing was moved into the shared shell,
  keeping the health-data script free of URL access. The unchanged security assertion
  and related shell/Person checks then passed: 29 passed. No remaining known failure.
- Final browser check after that repair: selecting Review leaves only the Review section
  visible; navigation state is owned by the shared shell. The temporary preview tab closes
  and only the persistent Sano login destination remains.

## Installation migration (de-identified)

The process serving `127.0.0.2:8100` was identified before migration. Writes were stopped;
its existing installation was backed up and verified, recovered to adjacent staging,
upgraded to v12, then verified again. A verified v12 backup was recovered into the absent
final target. No nonempty directory was overwritten.

- Target: `%LOCALAPPDATA%/Sano/workspace`.
- Pre-migration backup: `%LOCALAPPDATA%/Sano/backups/sano-a1-before-20260926T134318Z`.
- Prepared v12 backup: `%LOCALAPPDATA%/Sano/backups/sano-a1-prepared-20260926T134318Z`.
- Private migration report: `%LOCALAPPDATA%/Sano/runtime/migration-a1.json`.
- Original installation, both backups, and staging are retained.
- All old table rows except schema history are unchanged. Accounts, password verifiers,
  grants, Sources, extractions and prior candidates are preserved. Sessions were copied
  using SQLite backup into a separate runtime database.
- Counts after migration: 2 People, 3 Actors, 1 Source, 26 existing candidates,
  0 canonical records, 1 metadata row. No new medical fact was created.
- Source file existence, byte sizes and SHA-256 were verified; the application service
  also successfully read the recovered original. No real content is reproduced here.
- An initial staging check found that re-backing-up recovery-layout payloads used the
  wrong path. The old runtime was restored, the fail-closed recovery fallback was fixed,
  and a second-backup/second-recovery test now passes. Final activation succeeded.
- Repeating the migration returns `already_migrated` after schema, foreign keys,
  file sizes and hashes are checked. Unknown existing targets are refused.
- Runtime uses an isolated Python 3.12 environment and the persistent `sano.env` file.
  The server is detached from the agent session and keeps the same local URL.
- HTTP health, Sano login and local viewer assets pass. Real password entry was not
  performed by the agent; stored credentials and assignments are unchanged, and
  a user with an expired browser session signs in with the existing account.

## A1 limits

PDF/TXT only; bounded local text-layer extraction and conservative contextual dates.
Ambiguous dates remain unknown and can be entered manually. No OCR, image upload,
external AI, AI summary, new processing queue, indicators table or batch promotion.
Originals remain available independently of AI. Existing health review and genetics
contracts retain their authorization and provenance boundaries.

## Project statuses (unchanged)

```text
R7 = DONE / published
UI-R4.1 = COMPLETE locally at 1a8f21788768ae6a67d9e62ba71858eae7dcf95a
merge/push пока не подтверждены
SANO Brand Direction v1 = FIXED
G5 = READY_FOR_SECOND_CLIENT_SMOKE
AlphaGenome = PAUSED after C.1
```
