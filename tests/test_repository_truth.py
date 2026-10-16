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

    assert "Public " + chr(96) + "main" + chr(96) + " is a mutable Git ref." in status
    assert "P3-final implementation" in status
    assert "R1 repository-truth" in status
    assert (
        "Private, source-grounded personal and family health workspace with auditable AI."
        in readme
    )
    assert (
        "P3 Genetics Research Studio is implemented and published on public "
        + chr(96)
        + "main"
        + chr(96)
        in status
    )
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
    assert "integrated in published " + chr(96) + "main" + chr(96) in status
    assert "b378fe28f8798ff41d72f1244ecb9b68d5d4bbbd" in status
    assert "PUBLISHED STABLE (8 October 2026)" in status
    assert "2730d65fea3a5a1909b05f5b25e9144fe2376215" in status
    assert "prepared for integration" not in status


def test_public_reviewer_copy_exposes_current_ai_validation_boundary() -> None:
    readme = _read("README.md")
    validation = _read("docs/sano-live-validation.md")

    assert "## Validation status" in readme
    for required in (
        "OpenRouter/DeepSeek live provider flow",
        "OpenAI live X2 is",
        "unverified",
        "operator-confirmed",
    ):
        assert required in readme
    assert "[SANO live validation](docs/sano-live-validation.md)" in readme
    assert "[project status](docs/project-status.md)" in readme
    assert "READY_FOR_SECOND_CLIENT_SMOKE" not in readme
    assert "AlphaGenome" not in readme
    assert "LIVE PASS / operator-confirmed" in validation
    assert "Backup / verify / recovery" in validation
    assert "Q&A source/page citations" in validation
    assert "G5 machine state remains exactly" in validation
    assert "READY_FOR_SECOND_CLIENT_SMOKE" in validation


def test_current_authentication_truth_keeps_registration_and_sharing_boundaries() -> None:
    status = _read("docs/project-status.md")
    matrix = _read("docs/capability-matrix.md")
    readme = _read("README.md")
    agents = _read("AGENTS.md")
    environment = _read(".env.example")

    assert "OPENCARE_PUBLIC_REGISTRATION=false" in environment
    assert "invitations are an explicit family-sharing mechanism" in status
    assert "Optional public self-registration is disabled by default" in status
    assert (
        "Email verification / password recovery | "
        + chr(96)
        + "NOT IMPLEMENTED"
        + chr(96)
        in matrix
    )
    assert "Deployment security, backups," in readme
    assert "never creates installation-admin status" in agents
    assert "READY_FOR_SECOND_CLIENT_SMOKE" in status
    assert "G5: READY_FOR_SECOND_CLIENT_SMOKE" in status
    assert "AlphaGenome: PAUSED after C.1" in status
    assert "SANO v0.3.0 is the published stable release" in readme
    assert "OpenAI live X2 is unverified" in readme
    assert "8 October 2026" in readme
    assert "READY_FOR_SECOND_CLIENT_SMOKE" not in readme
    assert "AlphaGenome" not in readme
    assert "prepared for integration" not in readme


def test_public_documentation_entrypoints_and_cleanup_contracts() -> None:
    index = _read("docs/README.md")
    architecture = _read("docs/architecture.md")
    checklist = _read("docs/release_checklist.md")
    adr = _read("docs/adr/0007-document-summary-coverage.md")
    reviewer_pack = _read("docs/final_reviewer_pack.md")
    screenshots = _read("docs/screenshots.md")

    required_paths = (
        "docs/project-status.md",
        "docs/capability-matrix.md",
        "docs/architecture.md",
        "docs/architecture/module-boundaries.md",
        "docs/roadmap/product-core-roadmap.md",
        "docs/sano-live-validation.md",
        "docs/adr/0007-document-summary-coverage.md",
        "docs/screenshots.md",
        "docs/assets/sano-x2/documents-1440.webp",
        "docs/assets/sano-promo/sano-promo-t056.250.png",
        "reports/.gitkeep",
        "evals/results/.gitkeep",
    )
    for path in required_paths:
        assert (ROOT / path).is_file(), path

    for required in (
        "Project status",
        "Capability matrix",
        "Architecture",
        "Product Core roadmap",
        "Live validation",
        "release checklist",
        "CONTRIBUTING.md",
        "LICENSE",
    ):
        assert required in index

    assert "current public main implementation" in architecture
    assert "app/product_core" in architecture
    assert "Raw genome bytes" in architecture
    assert "python -m evals.p3_review" in checklist
    assert "CHECKPOINT.md" not in checklist
    assert "SESSION_NOTES.md" not in checklist
    assert "docs/screenshots.md" in checklist
    assert "OpenAI live X2 remains explicitly unverified" in checklist
    assert "Release checklist" in reviewer_pack
    assert "final_submission_checklist.md" not in reviewer_pack
    assert "documents-1440.webp" in screenshots
    assert "sano-promo-t056.250.png" in screenshots
    assert "real patient" in screenshots
    assert "coverage is a server-owned fact" in adr.lower()
    assert "Raw document pages are not added to general chat context." in adr

    deleted = (
        "FIRST_CODEX_PROMPT.md",
        "CHECKPOINT.md",
        "SESSION_NOTES.md",
        "sentient-g1-trust-envelope-plan.md",
        "docs/grant_application_pack.md",
        "docs/grant_pitch.md",
        "docs/grant_short_pitch.md",
        "docs/grant_submission_answers.md",
        "docs/master_plan.md",
        "docs/project_status.md",
        "docs/demo_script.md",
        "docs/demo_video_script.md",
        "docs/product_brief.md",
        "docs/darktech_chat_ui_reference.md",
        "docs/roadmap.md",
        "docs/superpowers/plans/2026-10-07-document-summary-coverage.md",
        "docs/superpowers/specs/2026-10-04-document-summary-coverage-design.md",
        "docs/final_submission_checklist.md",
        "docs/assets/screenshots/landing.png",
        "docs/assets/screenshots/demo.png",
        "docs/assets/screenshots/sertraline-report.png",
        "docs/assets/screenshots/aspirin-safe-no-claim.png",
    )
    for path in deleted:
        assert not (ROOT / path).exists(), path


def test_document_summary_contract_is_documented_without_provider_authority() -> None:
    adr = _read("docs/adr/0007-document-summary-coverage.md")

    for required in (
        "summary, key_points, discussion_questions, and page_numbers",
        "Provider output cannot choose either field.",
        "page_numbers remains model output used for citation allowlisting",
        "Documents → “Ask about this document”",
        "no database migration or public endpoint change",
    ):
        assert required in adr


def test_current_eval_and_capability_documents_do_not_overclaim() -> None:
    eval_results = _read("docs/eval_results.md")
    matrix = _read("docs/capability-matrix.md")
    reviewer = _read("docs/reviewer_quickstart.md")

    assert "## Latest Validation Result" not in eval_results
    assert "Historical Phase 1.5 / Legacy Demo Eval Baseline" in eval_results
    assert "| Guarded chat | " + chr(96) + "IMPLEMENTED" + chr(96) + " |" in matrix
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
