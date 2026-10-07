# SANO live and repository validation

**Record date:** 7 October 2026. **Purpose:** Preserve the evidence checked while preparing the SANO Sentient grant baseline. This report contains no credentials, private deployment details, or health data.

## Repository baseline

The dated public-main baseline was `84fb682429c94f7c589530063c8753d882008d58`. That SHA already contains Product Core migration v13 and SANO-X2 document understanding: PDF/TXT/JPG/PNG, local OCR, and document summary/Q&A. The code is directly inspectable in `app/product_core/migrations.py` and the X2 document modules at that revision.

The production branch `codex/sano-production-deployment` at `089a5eb678b198a8e71e5cb15d038083ae0f7085` was the dated seven-commit integration input beyond `84fb682`; those post-main production/product refinements do not introduce v13, X2, OCR, or document summary/Q&A. The final publication commit `b378fe28f8798ff41d72f1244ecb9b68d5d4bbbd` was pushed to public `main` on 7 October 2026 and includes that input plus the redirect-test correction. These are dated baselines, not a claim that either identifier remains the current value of a mutable branch.

## GitHub Actions evidence

GitHub Actions is a separate evidence class. The workflow checks deterministic
tests, lint, typing, evals, trust metrics, and reviewer gates; it does not run
paid OpenRouter or other live provider calls.

- The dated pre-integration public-main run was [run 37200437345](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/37200437345), created 4 October 2026 for `84fb682429c94f7c589530063c8753d882008d58`. Its required job contexts were `validate`, `Family access credentials (ubuntu-latest)`, and `Family access credentials (windows-latest)`.
- [Run 37644787220](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/37644787220), created 7 October 2026 for the dated `089a5eb678b198a8e71e5cb15d038083ae0f7085` input, failed with 1 failed, 1,197 passed, and 2 skipped. The failed assertion expected an authenticated `/chat` request without an active Person to return 404. The route intentionally redirects to the Person picker; the corrected test asserts `307` and the safe `/documents?next=%2Fchat` path. This is historical input-branch evidence.
- Final public-main run [37683527310](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/37683527310) for `b378fe28f8798ff41d72f1244ecb9b68d5d4bbbd` passed. Its required contexts were `validate`, `Family access credentials (ubuntu-latest)`, and `Family access credentials (windows-latest)`.

## Automated and local validation

After the redirect assertion was updated, the focused Python 3.12 command

```text
py -3.12 -m pytest tests/test_product_core_access_enforcement.py tests/test_product_shell.py tests/test_assistant_document_flow.py -q --tb=short
```

completed with **42 passed**. After the reviewer route and repository metadata
were aligned, the expanded focused set completed with **55 passed**. It covers
the redirect contract, authenticated and revoked access, chat, document
assistant, reviewer links, release metadata, and repository truth.

Final canonical validation on the prepared tree, using Python 3.12.10:

- `py -3.12 -m pytest`: **1,197 passed, 4 skipped**; four upstream `httpx`
  cookie deprecation warnings.
- `py -3.12 -m ruff check app tests evals`: passed.
- `py -3.12 -m mypy app evals`: passed, 138 source files.
- `python -m evals.runner`: 30/30; zero unsafe-advice, missing-source,
  uncertainty, audit, or pipeline failures.
- `python -m evals.trust_metrics`: completed; the report explicitly says this
  is not clinical validation.
- G5: 20/20, machine state remains exactly
  `READY_FOR_SECOND_CLIENT_SMOKE`; P1, P2, D1, and P3 reviewers passed.
- Node syntax checks passed for `product_core_workspace.js`, `genetics.js`,
  `chat.js`, and `sano_documents.js`; Markdown local-link/image checks passed
  through the release metadata test. The built wheel contains both `LICENSE`
  and `NOTICE`; `git diff --check` passed.
- `py -3.12 -m pip check` reports an environment-level conflict:
  `aiogram 3.27.0` requires `pydantic<2.13`, while this Python environment has
  `pydantic 2.13.4`. `aiogram` is not a project dependency; no dependency
  declaration was changed to mask this conflict.

## Live endpoint checks

On 7 October 2026, `https://sanobot.art/health` returned HTTP 200 and `{"status":"ok"}`. `https://sanobot.art/readyz` returned HTTP 200 and `{"status":"ready"}`. These endpoint checks establish HTTP health and readiness only; they do not establish a public demo session or a workflow-level result.

## Operator-confirmed model testing

Local-model inference without an external API is operator-confirmed. The
OpenRouter/DeepSeek live provider flow, including SANO document summary and
document Q&A, is **LIVE PASS / operator-confirmed**. Summary attribution, Q&A
citations, and execution receipts are also operator-confirmed PASS results.
OpenAI **live X2 is UNVERIFIED**: the OpenAI adapter is tested, but no separate
OpenAI X2 production workflow evidence was supplied. Models, hardware, test
count, and workflow-specific smoke details are not inferred. External providers
are not used by default.

## Production and operator validation

The following statuses are operator-confirmed production evidence supplied for
this packaging pass. They do not include credentials, private health data,
model identifiers, deployed SHAs, hardware details, or raw smoke logs.

| Surface | Status | Evidence class |
| --- | --- | --- |
| `https://sanobot.art` | LIVE | operator-confirmed |
| `healthz` / `readyz` | PASS | operator-confirmed |
| PDF/TXT/JPG/PNG document support | PASS | operator-confirmed |
| Local OCR (`rus+eng`) | PASS | operator-confirmed |
| Persistence | PASS | operator-confirmed |
| Backup / verify / recovery | PASS | operator-confirmed |
| OpenRouter live connectivity | LIVE PASS | operator-confirmed |
| OpenRouter exact model binding | LIVE PASS | operator-confirmed |
| DeepSeek strict structured output | LIVE PASS | operator-confirmed |
| Document summary through OpenRouter/DeepSeek | LIVE PASS | operator-confirmed |
| Document Q&A through OpenRouter/DeepSeek | LIVE PASS | operator-confirmed |
| Summary page attribution | PASS | operator-confirmed |
| Q&A source/page citations | PASS | operator-confirmed |
| Execution Receipts | PASS | operator-confirmed |

## Current integration and release boundary

- After the repository-truth, release-metadata, wheel-packaging, Markdown
  link/image, stale-claim, secret-pattern, and diff checks passed on this
  prepared tree, the local packaging state is
  `SANO_GRANT_PACKAGING_LOCAL=READY`.
- Repository publication and exact-SHA CI are complete at
  `b378fe28f8798ff41d72f1244ecb9b68d5d4bbbd`; the local packaging state and
  public repository state are `SANO_GRANT_PACKAGING_LOCAL=READY` and
  `SANO_SENTIENT_GRANT_REPO=READY`. Release creation, deployment, settings
  changes, and remote branch cleanup remain separate manual actions.
- Public `main` at the dated `84fb682` baseline already includes Product Core schema v13, PDF/TXT/JPG/PNG document support, local Tesseract `rus+eng` OCR, and consent-gated descriptions and document Q&A. The seven post-main refinements through `089a5eb` do not introduce those capabilities.
- SANO stores health context in the self-hosted installation. External disclosure is optional, minimized to selected evidence, consented per action, and receipted. Raw genome data never enters supported provider context.
- Agent Skills interoperability is verified; G5 machine state remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`. Root Agent Plugins two-client evidence remains pending. AlphaGenome is paused after C.1.
- No diagnosis, prescribing, dosage, autonomous canonical-record mutation, clinical validation, or general-purpose public SaaS readiness is claimed.
- Version `0.3.0` and release notes are prepared locally. There is no published `v0.3.0` tag or release.

## GitHub repository settings checked

GitHub API and repository metadata were inspected on 7 October 2026. Homepage was empty; `main` was not protected; Dependabot security updates and vulnerability alerts were disabled; secret scanning and push protection were enabled. The repository had no Code of Conduct or issue/PR templates at that point. The repository description did not name SANO; topics did not include `sentient` or `ocr`. Code-scanning status could not be confirmed through the available repository API and remains a Security-tab check. No remote setting was changed.

## Remote branch review candidates

`git branch --remotes --merged origin/main`, ahead/behind counts, exact-head
Actions runs, and the repository's pull-request list were inspected on 7 October
2026. The only returned pull request was [PR #1](https://github.com/KirillNedoboy/open-care-proof-kit/pull/1),
merged from `phase-1-demo-assets`; no other listed branch had a returned PR.
The following refs were ancestors of `origin/main` and therefore possible
stale-branch review candidates:

- `origin/master`
- `origin/phase-1-demo-assets` (PR #1 is merged)
- `origin/phase-1-evidence-hardening`
- `origin/phase-1-github-grant-readiness`
- `origin/phase-1-pipeline-evals`
- `origin/phase-1-web-demo`
- `origin/codex/fix-demo-medication-citations`
- `origin/codex/opencare-guarded-chat-ui`
- `origin/codex/sentient-grant-positioning`

The production branch `origin/codex/sano-production-deployment` remains a dated input branch containing the seven post-main production/product refinements. Keep it until current PR/ref review; no branch was deleted. Recheck current refs and pull requests before proposing any cleanup.
