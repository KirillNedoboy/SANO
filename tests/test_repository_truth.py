from __future__ import annotations

import tomllib
from pathlib import Path

from app import __version__
from app.product_core.migrations import PRODUCT_MIGRATIONS

ROOT = Path(__file__).resolve().parents[1]
def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_repository_truth_is_published_and_versioned() -> None:
    status = _read("docs/project-status.md")
    matrix = _read("docs/capability-matrix.md")
    readme = _read("README.md")
    project = tomllib.loads(_read("pyproject.toml"))["project"]

    assert "Public `main` is a mutable Git ref." in status
    assert "P3-final implementation" in status
    assert "R1 repository-truth" in status
    assert (
        "Private, source-grounded personal and family health workspace with auditable AI."
        in readme
    )
    assert "P3 Genetics Research Studio is implemented and published on public `main`" in status
    assert "P3 is part of the published" in matrix
    assert "P3 branch" not in matrix
    assert "pending integration" not in matrix
    assert "84fb682429c94f7c589530063c8753d882008d58" in status
    assert "schema v13" in status and "SANO-X2" in status
    assert "v13 PUBLISHED" in matrix
    assert "v13 CANDIDATE / v12 ON PUBLIC MAIN" not in matrix
    assert "Genetics remains a future layer" not in readme
    assert "no document ingestion" not in readme.lower()
    assert project["version"] == __version__ == "0.3.0"
    assert PRODUCT_MIGRATIONS[-1].version == 13
    assert "SANO-X2" in status
    assert "Product Core schema v13" in status
    assert "already contains Product Core schema v13 and SANO-X2" in status
    assert "post-main production/product refinements" in status
    assert "integrated in published `main`" in status
    assert "b378fe28f8798ff41d72f1244ecb9b68d5d4bbbd" in status
    assert "PUBLISHED STABLE (8 October 2026)" in status
    assert "2730d65fea3a5a1909b05f5b25e9144fe2376215" in status
    assert "prepared for integration" not in status


def test_public_reviewer_copy_exposes_current_ai_validation_boundary() -> None:
    readme = _read("README.md")
    validation = _read("docs/sano-live-validation.md")

    assert "## AI / LLM validation" in readme
    for required in (
        "SANO document summary through OpenRouter/DeepSeek",
        "SANO document Q&A through OpenRouter/DeepSeek",
        "OpenAI live X2",
        "UNVERIFIED",
    ):
        assert required in readme
    assert "LIVE PASS / operator-confirmed" in validation
    assert "Backup / verify / recovery" in validation
    assert "Q&A source/page citations" in validation
    assert "G5 machine state remains exactly `READY_FOR_SECOND_CLIENT_SMOKE`" in validation


def test_current_authentication_truth_keeps_registration_and_sharing_boundaries() -> None:
    status = _read("docs/project-status.md")
    matrix = _read("docs/capability-matrix.md")
    readme = _read("README.md")
    agents = _read("AGENTS.md")
    environment = _read(".env.example")

    assert "OPENCARE_PUBLIC_REGISTRATION=false" in environment
    assert "invitations are an explicit family-sharing mechanism" in status
    assert "Optional public self-registration is disabled by default" in status
    assert "Email verification / password recovery | `NOT IMPLEMENTED`" in matrix
    assert "not a claim of public SaaS readiness" in readme
    assert "never creates installation-admin status" in agents
    assert "READY_FOR_SECOND_CLIENT_SMOKE" in status
    assert "SANO v0.3.0 is the published stable release" in readme
    assert "OpenAI live X2 is unverified" in readme
    assert "published stable release dated 8 October 2026" in readme
    assert "prepared for integration" not in readme


def test_root_agent_artifacts_are_unmistakably_historical() -> None:
    first_prompt = _read("FIRST_CODEX_PROMPT.md")
    checkpoint = _read("CHECKPOINT.md")
    session_notes = _read("SESSION_NOTES.md")

    assert first_prompt.startswith("# HISTORICAL PROJECT ARTIFACT")
    assert "DO NOT USE AS CURRENT REPOSITORY INSTRUCTIONS" in first_prompt
    for document in (first_prompt, checkpoint, session_notes):
        assert "AGENTS.md" in document
        assert "AGENTS.product-direction.md" in document
        assert "docs/project-status.md" in document


def test_current_eval_and_capability_documents_do_not_overclaim() -> None:
    eval_results = _read("docs/eval_results.md")
    matrix = _read("docs/capability-matrix.md")
    reviewer = _read("docs/reviewer_quickstart.md")

    assert "## Latest Validation Result" not in eval_results
    assert "Historical Phase 1.5 / Legacy Demo Eval Baseline" in eval_results
    assert "| Guarded chat | `IMPLEMENTED` |" in matrix
    assert "first-five-minute reviewer path" in reviewer


def test_reviewer_commands_and_ci_gates_are_current() -> None:
    ci = _read(".github/workflows/ci.yml")
    for module in ("g5_review", "p1_review", "p2_review", "d1_review", "p3_review"):
        assert (ROOT / "evals" / f"{module}.py").is_file()
        assert f"python -m evals.{module}" in ci or module == "g5_review"
    assert "python -m pip check" in ci
    assert "git diff --check" in ci
    assert "node --check app/static/product_core_workspace.js" in ci
    assert "node --check app/static/genetics.js" in ci
