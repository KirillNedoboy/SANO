# SANO-X1 local validation

SANO-X1 converges the public landing page, account flows, and authenticated
workspace on the existing SANO-A1 archive foundation. This report records a
local-only implementation; it does not change the installation serving
`127.0.0.2:8100`, user data, or any published deployment.

## Branch and base

- Local branch: `codex/sano-x1-public-product-convergence`.
- Base: UI-R4.1 commit `1a8f21788768ae6a67d9e62ba71858eae7dcf95a`.
- SANO-A1 was copied selectively and committed as the local base
  `87e42d7` (`feat(sano): establish archive-first product foundation`).
- X1 changes are layered above that base. No merge, push, or deployment was
  performed.

## Delivered in X1

- One SANO visual language across landing, login, registration, invitation,
  and product shell, using common `--ui-*` tokens and the existing SANO
  direction.
- A new original editorial hero image and a clean SVG wordmark/favicon derived
  from the Evidence Path concept.
- Clearer landing copy in English and Russian, public-auth branding, mobile
  layout, visible navigation affordance, and a shared keyboard focus style.
- Account registration now opens `/documents`; an authenticated visit to `/`
  continues to return to `/documents`.
- The SANO-A1 archive and its schema/API/lifecycle remain the product entry
  point. Assistant, health, genetics, family, and settings remain available in
  the product navigation.

## Local route and visual checks

The app was run on `http://127.0.0.1:8102` with an isolated Product Core
database, session store, and synthetic account. The real installation at
`http://127.0.0.2:8100` was not used or changed.

- Public landing, login, registration, invitation, documents, assistant,
  health, genetics, family access, and workspace routes returned successfully.
- A synthetic registration completed and landed on `/documents`; requesting
  `/` while authenticated returned to `/documents`.
- The language control switched the archive and navigation from English to
  Russian. Public auth and landing localization are covered by tests.
- The mobile navigation opened and exposed all six workspace destinations.
- Landing and document archive were visually checked at 1440×900, 1024×900,
  and 390×844. No horizontal page overflow was measured at those widths.
- Browser console reported zero errors or warnings on the inspected landing,
  archive, registration, and return-to-archive flow.
- Screenshots use synthetic preview data only:

| Screen | 1440×900 | 1024×900 | 390×844 |
| --- | --- | --- | --- |
| Landing | [1440](assets/sano-x1/landing-1440.webp) | [1024](assets/sano-x1/landing-1024.webp) | [390](assets/sano-x1/landing-390.webp) |
| Documents | [1440](assets/sano-x1/documents-1440.webp) | [1024](assets/sano-x1/documents-1024.webp) | [390](assets/sano-x1/documents-390.webp) |

## Automated validation

- Full suite: `py -3.12 -m pytest` — **1098 passed, 4 skipped**. Four existing
  httpx per-request-cookie deprecation warnings were reported.
- Focused X1 landing, brand, registration, and navigation tests — **5 passed**.
- `py -3.12 -m mypy app evals` — passed (134 source files).
- `node --check` passed for `account_registration.js`,
  `product_core_workspace.js`, and `genetics.js`.
- `ruff check` passed for the changed Python test files. The full requested
  `ruff check app tests evals` still reports **40 E501 lines already present in
  the SANO-A1 base**: the A1 landing copy in `app/ui_localization.py` and the
  `/` route docstring in `app/main.py`. X1-added lines pass the 100-character
  limit.
- `git diff --check` passed; Git emitted only expected LF-to-CRLF working-copy
  notices on Windows.

The SANO-A1 backup/migration evidence remains in
[sano-a1-validation.md](sano-a1-validation.md); X1 did not repeat or change
that migration.

## Limits

- X1 does not add OCR, external AI processing, document summaries, or a new
  review workflow.
- The isolated browser pass verified navigation and empty archive states;
  archive save/open/download and metadata behavior remain covered by the
  SANO-A1 implementation and its tests.
- The persistent installation and account at `127.0.0.2:8100` remain on their
  existing deployment/runtime configuration.

## Project statuses

```text
R7 = DONE / published
UI-R4.1 = COMPLETE locally at 1a8f21788768ae6a67d9e62ba71858eae7dcf95a
merge/push пока не подтверждены
SANO Brand Direction v1 = FIXED
G5 = READY_FOR_SECOND_CLIENT_SMOKE
AlphaGenome = PAUSED after C.1
```
