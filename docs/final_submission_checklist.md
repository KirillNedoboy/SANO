# SANO Sentient grant readiness checklist

This checklist is for review before submitting a Sentient Foundation public-goods grant application. It does not authorize publishing, release creation, deployment, GitHub settings changes, or remote branch deletion.

## Repository and product truth

- [ ] Confirm the seven post-`84fb682` production/product refinements and their CI are green on GitHub.
- [ ] Integrate the post-main refinements into public `main`; check the resulting commit against the dated validation baseline.
- [ ] Confirm README, project status, capability matrix, judge guide, reviewer pack, and grant materials tell the same current story.
- [ ] Keep `SANO_SENTIENT_GRANT_REPO=BLOCKED` while the post-main refinements are unintegrated or CI is not green.
- [ ] Preserve G5 exactly as `READY_FOR_SECOND_CLIENT_SMOKE` and AlphaGenome as paused after C.1.
- [ ] State plainly that clinical validation and clinical authority are not claimed.

## Product reviewer path

- [ ] README shows SANO, the live URL, CI and Apache-2.0 badges, the synthetic screenshot, and links to the live demo, judge guide, Docker quickstart, and trust/security evidence.
- [ ] The 3–5 minute judge path covers the document original and provenance, local OCR, consented summary and Q&A, receipt, and Person-scoped Family Access.
- [ ] Public fixtures, screenshots, and examples contain only synthetic or de-identified data.
- [ ] External-provider disclosure is described as optional, minimized to selected evidence, consented per action, and receipted.

## Grant and validation evidence

- [ ] Grant copy uses the approved 80-character pitch and describes SANO plus reusable sensitive-agent trust infrastructure.
- [ ] Future milestones cover local open-weight inference and RU/EN benchmarks, a reproducible security testbed, and conditional evaluation of confidential compute.
- [ ] No amount or calendar commitment is invented; confirm the current Typeform questions before submission.
- [ ] The dated validation artifact separates local checks, GitHub Actions evidence, and operator-confirmed model tests.
- [ ] Add final refinement/main SHA, smoke details, test counts, and provider/model identities only when directly evidenced.
- [ ] Review the live demo with the intended judge access and the planned synthetic sample.

## Release and repository hygiene

- [ ] Package metadata and runtime report version `0.3.0`; the prepared notes explicitly say that no tag/release has been created.
- [ ] Changelog and release notes state the comparison boundary `v0.2.0` and the non-clinical scope.
- [ ] GitHub detects Apache-2.0 after the canonical license is integrated; project attribution remains in `NOTICE`.
- [ ] Community profile includes Code of Conduct, issue templates, and a pull-request template with sensitive-data guidance.
- [ ] Inspect the merged-into-main branch candidates listed in the validation report against current open pull requests before requesting deletion.

## Remote branch snapshot

Read-only snapshot inspected 7 October 2026. Ahead/behind counts compare each
remote head with `origin/main` at `84fb682429c94f7c589530063c8753d882008d58`.
CI is reported only when a GitHub Actions run was found for that exact head SHA.
Recheck refs, runs, and open pull requests before any cleanup request.

| Remote branch | Head SHA | Ahead / behind | Latest CI for exact SHA | Purpose and recommendation |
| --- | --- | ---: | --- | --- |
| `origin/main` | `84fb682429c94f7c589530063c8753d882008d58` | 0 / 0 | success ([run 37200437345](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/37200437345)) | Published baseline; keep. |
| `origin/codex/sano-production-deployment` | `089a5eb678b198a8e71e5cb15d038083ae0f7085` | 7 / 0 | failure ([run 37644787220](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/37644787220)) | Seven post-84fb production/product refinements; keep for integration. |
| `origin/codex/fix-demo-medication-citations` | `b30733cf7fde66ee9f35e5b5677e4f0929e3b3c5` | 0 / 228 | success ([run 29511166104](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/29511166104)) | Medication citation fix; cleanup candidate after PR/ref review. |
| `origin/codex/opencare-guarded-chat-ui` | `b7f978e11743fa793002afd8edd4aa65559a5d95` | 0 / 230 | success ([run 29439170817](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/29439170817)) | Guarded chat UI; cleanup candidate after PR/ref review. |
| `origin/codex/sentient-grant-positioning` | `14283ae4027a32407f33f76a7a070c944539e816` | 0 / 250 | no run found for exact head SHA | Grant positioning history; cleanup candidate after PR/ref review. |
| `origin/master` | `f380cd6b1621e1ebb41d4a7895a153c6dc0abbb3` | 0 / 262 | no run found for exact head SHA | Legacy default branch; cleanup candidate after PR/ref review. |
| `origin/phase-1-demo-assets` | `ba6b4f90a4344b350438ed0246924b9fc6d4146b` | 0 / 256 | no run found for exact head SHA | Historical demo assets; PR #1 is merged; cleanup candidate after PR/ref review. |
| `origin/phase-1-evidence-hardening` | `dda7958fe484728dae4b5341baf472350a4e2d22` | 0 / 260 | no run found for exact head SHA | Historical evidence validation work; cleanup candidate after PR/ref review. |
| `origin/phase-1-github-grant-readiness` | `0a74740fb30ba87922d8f01d069de78260f724c5` | 0 / 252 | success ([run 28376292489](https://github.com/KirillNedoboy/open-care-proof-kit/actions/runs/28376292489)) | Historical repository readiness docs; cleanup candidate after PR/ref review. |
| `origin/phase-1-pipeline-evals` | `608fc11c8f86024810a6d44e7443619b5863e89f` | 0 / 259 | no run found for exact head SHA | Historical pipeline evals; cleanup candidate after PR/ref review. |
| `origin/phase-1-web-demo` | `b46e3365ebdbda0b5433a8831a78557ee94163d6` | 0 / 261 | no run found for exact head SHA | Historical local web demo; cleanup candidate after PR/ref review. |

No branch cleanup is authorized by this checklist.

## GitHub settings to check manually

- [ ] Homepage: `https://sanobot.art`.
- [ ] Description: `SANO — open-source, self-hosted health workspace with provenance, consent-gated AI and auditable agent trust.`
- [ ] Topics: `self-hosted`, `health-ai`, `agent-safety`, `privacy`, `local-first`, `provenance`, `open-source`, `fastapi`, `evals`, `ocr`, `agentic-ai`, `sentient`.
- [ ] Protect `main`; require the existing `validate`, `Family access credentials (ubuntu-latest)`, and `Family access credentials (windows-latest)` checks; block force pushes and branch deletion.
- [ ] Review Dependabot alerts and updates, secret-scanning alerts, push protection, code-scanning availability, and security advisories. Report only observed states.
- [ ] Open the repository page and verify its README, license detection, and local links render after integration.

## Local validation commands

Run the documentation and packaging checks once on the final stabilized
candidate with Python 3.12. The full product run recorded in the validation
artifact is not repeated while runtime and JavaScript files remain unchanged:

```powershell
py -3.12 -m pytest tests/test_repository_truth.py tests/test_release_metadata.py -q
py -3.12 -m pytest tests/test_wheel_runtime_assets.py -q
git diff --check
```
