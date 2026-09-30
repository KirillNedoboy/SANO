from __future__ import annotations

import hashlib
import io
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.family_access.credentials import hash_password
from app.family_access.policy import build_scopes
from app.family_access.service import FamilyAccessService
from app.product_core.installation_backup import InstallationBackupService
from app.product_core.installation_recovery import (
    InstallationRecoveryError,
    InstallationRecoveryService,
    verify_recovered_installation,
)
from app.product_core.migrations import (
    PRODUCT_MIGRATIONS,
    MigrationRunner,
    _backfill_document_metadata_dates,
)
from tests.test_sano_a1_documents import _service

NOW = datetime(2026, 9, 1, 12, tzinfo=UTC).isoformat()
PRESERVED_TABLES = (
    "sources",
    "document_extractions",
    "document_extraction_pages",
    "actors",
    "actor_credentials",
    "installation_admin_assignments",
    "person_access_consent_history",
    "person_access_assignments",
    "own_person_links",
)


def _seed_v11_document(tmp_path: Path, text: str) -> tuple[Path, Path, dict[str, tuple]]:
    database_path = tmp_path / "legacy.sqlite3"
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    MigrationRunner(
        lambda: sqlite3.connect(database_path), migrations=PRODUCT_MIGRATIONS[:11]
    ).migrate()

    payload = text.encode("utf-8")
    source_id = "legacy-document"
    relative_path = f"{source_id}.txt"
    (source_dir / relative_path).write_bytes(payload)
    page_hash = hashlib.sha256(payload).hexdigest()
    text_digest = hashlib.sha256()
    text_digest.update(len(payload).to_bytes(8, "big"))
    text_digest.update(payload)
    credential = hash_password("legacy password value")
    owner_scopes = json.dumps(sorted(build_scopes("owner")))
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO people(
                person_id, display_name, date_of_birth, created_at, updated_at, is_active
            ) VALUES (?, ?, NULL, ?, ?, 1)
            """,
            ("person-1", "Synthetic person", NOW, NOW),
        )
        connection.execute(
            """
            INSERT INTO actors(
                actor_id, username_normalized, display_name, status, created_at
            ) VALUES ('legacy-actor', 'legacy-user', 'Legacy owner', 'active', ?)
            """,
            (NOW,),
        )
        connection.execute(
            """
            INSERT INTO actor_credentials(
                credential_id, actor_id, credential_type, algorithm, algorithm_version,
                salt, verifier, created_at, revoked_at, replaced_by_credential_id
            ) VALUES (
                'legacy-credential', 'legacy-actor', 'local_password', ?, ?, ?, ?, ?, NULL, NULL
            )
            """,
            (
                credential.algorithm,
                credential.algorithm_version,
                credential.salt,
                credential.verifier,
                NOW,
            ),
        )
        connection.execute(
            """
            INSERT INTO installation_admin_assignments(
                admin_assignment_id, actor_id, assigned_by_actor_id, is_active,
                assigned_at, revoked_at, revoked_by_actor_id, reason_code
            ) VALUES ('legacy-admin', 'legacy-actor', 'legacy-actor', 1, ?, NULL, NULL, ?)
            """,
            (NOW, "synthetic_fixture"),
        )
        connection.execute(
            """
            INSERT INTO person_access_consent_history(
                consent_event_id, event_type, acting_owner_actor_id, recipient_actor_id,
                person_id, role, scopes_json, reason_code, created_at
            ) VALUES ('legacy-consent', 'grant', 'legacy-actor', 'legacy-actor',
                      'person-1', 'owner', ?, 'synthetic_fixture', ?)
            """,
            (owner_scopes, NOW),
        )
        connection.execute(
            """
            INSERT INTO person_access_assignments(
                assignment_id, actor_id, person_id, role, scopes_json, consent_event_id,
                granted_by_actor_id, is_active, granted_at, revoked_at,
                revoked_by_actor_id, revision_of_assignment_id, scope_generation
            ) VALUES ('legacy-assignment', 'legacy-actor', 'person-1', 'owner', ?,
                      'legacy-consent', 'legacy-actor', 1, ?, NULL, NULL, NULL,
                      'family-access-v4')
            """,
            (owner_scopes, NOW),
        )
        connection.execute(
            """
            INSERT INTO own_person_links(
                own_person_link_id, actor_id, person_id, is_active, created_at,
                revoked_at, revoked_by_actor_id
            ) VALUES ('legacy-own-link', 'legacy-actor', 'person-1', 1, ?, NULL, NULL)
            """,
            (NOW,),
        )
        connection.execute(
            """
            INSERT INTO sources(
                id, person_id, source_type, relative_path, content_hash, size_bytes,
                media_type, created_at, provenance_json, original_filename, document_kind
            ) VALUES (?, ?, 'document', ?, ?, ?, 'text/plain', ?, ?, ?, 'text')
            """,
            (
                source_id,
                "person-1",
                relative_path,
                hashlib.sha256(payload).hexdigest(),
                len(payload),
                NOW,
                json.dumps({"entry_method": "document_upload"}),
                "legacy.txt",
            ),
        )
        connection.execute(
            """
            INSERT INTO document_extractions(
                extraction_id, source_id, person_id, extractor, extractor_version,
                status, text_hash, total_chars, page_count, extracted_at
            ) VALUES (?, ?, ?, 'text', '1', 'complete', ?, ?, 1, ?)
            """,
            (
                "legacy-extraction",
                source_id,
                "person-1",
                text_digest.hexdigest(),
                len(text),
                NOW,
            ),
        )
        connection.execute(
            """
            INSERT INTO document_extraction_pages(
                extraction_id, source_id, person_id, page_number, normalized_text,
                decoded_content_bytes, extracted_chars, page_hash
            ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
            """,
            (
                "legacy-extraction",
                source_id,
                "person-1",
                text,
                len(payload),
                len(text),
                page_hash,
            ),
        )
    with sqlite3.connect(database_path) as connection:
        before = {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in PRESERVED_TABLES
        }
    return database_path, source_dir, before


def test_schema11_backup_verifies_then_migration12_preserves_document_rows_and_backfills_date(
    tmp_path: Path,
) -> None:
    database_path, source_dir, before = _seed_v11_document(
        tmp_path,
        "Report date: 2024-03-12\nDate of birth: 1990-01-01",
    )
    backup = tmp_path / "backup"
    report = InstallationBackupService(database_path, source_dir).backup(backup)

    assert report.valid is True
    assert report.product_core_schema_version == 11
    assert InstallationBackupService(database_path, source_dir).verify(backup).valid is True

    target = tmp_path / "recovered"
    recovered = InstallationRecoveryService().recover(backup, target, confirm_maintenance=True)
    assert recovered.valid is True
    assert recovered.product_core_schema_version == 11
    assert verify_recovered_installation(target).valid is True
    with sqlite3.connect(target / "database.sqlite3") as connection:
        recovered_rows = {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in PRESERVED_TABLES
        }
    assert recovered_rows == before

    MigrationRunner(lambda: sqlite3.connect(target / "database.sqlite3")).migrate()
    with sqlite3.connect(target / "database.sqlite3") as connection:
        after = {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in PRESERVED_TABLES
        }
        metadata = connection.execute(
            "SELECT title, document_date, document_date_source FROM document_metadata"
        ).fetchone()
        assert metadata == ("legacy.txt", "2024-03-12", "extracted")
    assert after == before
    authenticated = FamilyAccessService(
        __import__("app.product_core.sqlite", fromlist=["SQLiteDatabase"]).SQLiteDatabase(
            target / "database.sqlite3"
        )
    ).authenticate("LEGACY-USER", "legacy password value")
    assert authenticated is not None


def test_document_date_backfill_is_idempotent_and_preserves_user_override(
    tmp_path: Path,
) -> None:
    database_path, _source_dir, _before = _seed_v11_document(
        tmp_path,
        "Report date: 2024-03-12",
    )
    MigrationRunner(lambda: sqlite3.connect(database_path)).migrate()
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE document_metadata
            SET document_date = '2025-04-05', document_date_source = 'user'
            WHERE source_id = 'legacy-document'
            """
        )
        _backfill_document_metadata_dates(connection)
        connection.commit()
        assert connection.execute(
            "SELECT document_date, document_date_source FROM document_metadata"
        ).fetchone() == ("2025-04-05", "user")

    MigrationRunner(lambda: sqlite3.connect(database_path)).migrate()
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT document_date, document_date_source FROM document_metadata"
        ).fetchone() == ("2025-04-05", "user")


def _blank_pdf() -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(output)
    return output.getvalue()


def test_schema12_blank_pdf_metadata_recovers_and_repeated_recovery_refuses_target(
    tmp_path: Path,
) -> None:
    database, documents = _service(tmp_path)
    created = documents.register(
        "person-1",
        _blank_pdf(),
        "application/pdf",
        original_filename="blank.pdf",
    )
    backup = tmp_path / "backup"
    backup_service = InstallationBackupService(database.path, tmp_path / "sources")
    assert backup_service.backup(backup).product_core_schema_version == 13

    target = tmp_path / "recovered"
    recovery = InstallationRecoveryService()
    report = recovery.recover(backup, target, confirm_maintenance=True)
    assert report.valid is True
    assert report.product_core_schema_version == 13
    with sqlite3.connect(target / "database.sqlite3") as connection:
        assert connection.execute(
            "SELECT title, document_date, document_date_source FROM document_metadata"
        ).fetchone() == ("blank.pdf", None, "unknown")
    recovered_payload = target / "sources" / created.source.id / "payload.bin"
    assert (
        recovered_payload.read_bytes()
        == (tmp_path / "sources" / created.source.relative_path).read_bytes()
    )
    recovered_backup = tmp_path / "recovered-backup"
    recovered_service = InstallationBackupService(target / "database.sqlite3", target / "sources")
    assert recovered_service.backup(recovered_backup).valid
    assert recovered_service.verify(recovered_backup).valid
    second_target = tmp_path / "recovered-again"
    assert recovery.recover(recovered_backup, second_target, confirm_maintenance=True).valid
    assert (second_target / "sources" / created.source.id / "payload.bin").read_bytes() == (
        recovered_payload.read_bytes()
    )
    report_bytes = (target / "RECOVERY_REPORT.json").read_bytes()

    with pytest.raises(InstallationRecoveryError, match="target_not_empty"):
        recovery.recover(backup, target, confirm_maintenance=True)
    assert (target / "RECOVERY_REPORT.json").read_bytes() == report_bytes
    assert not list(tmp_path.glob(".opencare-recovery-*"))
