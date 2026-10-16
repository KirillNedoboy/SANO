# Release Checklist

Use this checklist before preparing a tagged release or publishing a reviewed repository snapshot. A release does not imply clinical validation or public SaaS readiness.

## Isolated Python 3.12 environment

PowerShell:

~~~powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -c constraints/python312.txt -e ".[dev]"
~~~

POSIX shell:

~~~sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -c constraints/python312.txt -e '.[dev]'
~~~

## Required repository checks

Run once from the repository root after changes stabilize:

~~~text
python -m pytest
python -m ruff check app tests evals
python -m mypy app evals
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
~~~

The pytest run includes wheel build/install coverage and runtime-resource smoke checks. Do not replace a failing safety, authorization, release, or evaluator assertion with a weaker assertion.

## Docker configuration and local smoke

When Docker Engine is available, validate configuration without printing environment values:

~~~text
docker compose config --quiet
docker compose -f docker-compose.yml -f deploy/docker-compose.system-caddy.yml config --quiet
~~~

The local smoke may start the Compose application with synthetic data only. Do not deploy to production or send real documents or provider requests as part of this checklist.

## Reviewer and capture evidence

- [ ] The reviewer path covers the source original and provenance, bounded local OCR, consented document summary/Q&A, Execution Receipt, and Person-scoped Family Access.
- [ ] Review `/workspace`, `/family-access`, `/genetics`, and `/demo/health-vault` with synthetic fixtures only; the demo surface remains read-only.
- [ ] External-provider disclosure is optional, minimized to selected evidence, consented per action, and receipted. OpenAI live X2 remains explicitly unverified in the dated validation record.
- [ ] Follow [docs/screenshots.md](screenshots.md) before adding or replacing a public visual; reject real patient/genetic data, secrets, private URLs, tokens, API keys, and non-demo provider responses.

## Documentation and repository hygiene

- [ ] README, [docs/README.md](README.md), project status, capability matrix, and release notes describe the same published behavior.
- [ ] v0.3.0, G5 READY_FOR_SECOND_CLIENT_SMOKE, AlphaGenome pause, and OpenAI live X2 unverified status are represented accurately.
- [ ] Public fixtures, screenshots, reviewer artifacts, and examples are synthetic or de-identified.
- [ ] Generated files remain ignored; reports/.gitkeep and evals/results/.gitkeep remain tracked.
- [ ] No secrets, .env, production data, or generated reports are staged.
- [ ] Local Markdown links, images, and anchors resolve.
