"""G2 executions restricted to one selected document's verified pages."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC
from typing import Any

from app.agent.document_summary_trust import (
    _document_input_hash,
    _select_pages,
    encode_document_question,
)
from app.agent.g2_runtime import G2Runtime
from app.agent.policy import classify_question
from app.product_core.errors import DocumentValidationError, SourceNotFoundError
from app.product_core.runtime import ProductCoreRuntime


class DocumentQuestionService:
    def __init__(
        self, runtime: ProductCoreRuntime, g2_runtime: G2Runtime, trust_adapter: Any
    ) -> None:
        self.runtime = runtime
        self.g2_runtime = g2_runtime
        self.trust_adapter = trust_adapter

    def prepare(
        self, person_id: str, source_id: str, question: str, session_token: str
    ) -> dict[str, Any]:
        policy = classify_question(question)
        if policy.decision != "allowed":
            return {
                "status": "refused",
                "reason_code": policy.reason_code,
                "answer": policy.response_text,
            }
        source, extraction = self.runtime.documents.get(source_id)
        processing = self.runtime.documents.get_text_processing(source_id)
        if source.person_id != person_id:
            raise SourceNotFoundError("document not found")
        if processing.status != "ready" or extraction is None:
            raise DocumentValidationError("document_text_not_ready")
        selected = _select_pages(
            self.runtime.documents.list_pages(source_id, extraction.extraction_id)
        )
        input_hash = _document_input_hash(selected)
        encoded = encode_document_question(
            person_id=person_id,
            source_id=source_id,
            extraction_id=extraction.extraction_id,
            input_text_hash=input_hash,
            user_question=question,
        )
        result = self.g2_runtime.prepare(
            session_token,
            encoded,
            purpose_id="document_question",
            action_id="document.answer_question",
        )
        descriptor = self.g2_runtime.provider.descriptor
        session = self.g2_runtime.sessions.resolve(session_token)
        if session is None:
            raise PermissionError("session_or_person_unavailable")
        actor_id = session.actor_id
        try:
            with self.runtime.database.uow(begin_mode="IMMEDIATE") as uow:
                assert uow.connection is not None
                uow.connection.execute(
                    """INSERT INTO document_question_bindings (
                        execution_id, actor_id, person_id, source_id, extraction_id,
                        input_text_hash, request_hash, provider_id,
                        provider_descriptor_hash, model_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        result.execution_id,
                        actor_id,
                        person_id,
                        source_id,
                        extraction.extraction_id,
                        input_hash,
                        hashlib.sha256(question.encode("utf-8")).hexdigest(),
                        descriptor.provider_id,
                        descriptor.descriptor_hash,
                        descriptor.model_id,
                        self.runtime.clock().astimezone(UTC).isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise DocumentValidationError("document_question_already_prepared") from exc
        return {
            "status": "prepared",
            "execution_id": result.execution_id,
            "preview": result.preview,
            "covered_pages": [number for number, _ in selected],
        }

    def consent(
        self,
        person_id: str,
        source_id: str,
        execution_id: str,
        question: str,
        fields: list[str],
        session_token: str,
    ) -> dict[str, Any]:
        row, encoded = self._binding(person_id, source_id, execution_id, question, session_token)
        self.trust_adapter.load_snapshot(
            {
                "person_id": person_id,
                "source_id": source_id,
                "extraction_id": row["extraction_id"],
                "input_text_hash": row["input_text_hash"],
            }
        )
        result = self.g2_runtime.grant_disclosure_consent(
            session_token, execution_id, fields=fields, question=encoded
        )
        return {"consent_id": result.consent_id, "execution_id": execution_id}

    def execute(
        self,
        person_id: str,
        source_id: str,
        execution_id: str,
        question: str,
        session_token: str,
    ) -> dict[str, Any]:
        row, encoded = self._binding(person_id, source_id, execution_id, question, session_token)
        self.trust_adapter.load_snapshot(
            {
                "person_id": person_id,
                "source_id": source_id,
                "extraction_id": row["extraction_id"],
                "input_text_hash": row["input_text_hash"],
            }
        )
        result = self.g2_runtime.execute(session_token, execution_id, encoded)
        receipt = self.g2_runtime.get_receipt(session_token, execution_id)
        answer = result.answer or {}
        page_numbers = answer.get("page_numbers", []) if isinstance(answer, dict) else []
        citations = [{"source_id": source_id, "claim": f"Page {number}"} for number in page_numbers]
        receipt_id = (
            receipt.get("receipt_id")
            if isinstance(receipt, dict)
            else None
            if receipt is None
            else receipt.receipt_id
        )
        return {
            "status": result.status,
            "answer": {
                "answer": answer.get("answer", "") if isinstance(answer, dict) else "",
                "citations": citations,
                "unknowns": answer.get("unknowns", []) if isinstance(answer, dict) else [],
                "doctor_questions": [],
                "boundary_notices": [
                    "This answer uses only the selected document and does not provide "
                    "diagnosis or treatment guidance."
                ],
            },
            "reason_code": result.reason_code,
            "receipt_id": receipt_id,
        }

    def receipt(
        self, person_id: str, source_id: str, execution_id: str, session_token: str
    ) -> dict[str, Any] | None:
        session = self.g2_runtime.sessions.resolve(session_token)
        if session is None or session.active_person_id != person_id:
            raise PermissionError("session_or_person_unavailable")
        with self.runtime.database.uow() as uow:
            assert uow.connection is not None
            row = uow.connection.execute(
                """SELECT 1 FROM document_question_bindings WHERE execution_id = ?
                   AND actor_id = ? AND person_id = ? AND source_id = ?""",
                (execution_id, session.actor_id, person_id, source_id),
            ).fetchone()
        if row is None:
            raise SourceNotFoundError("document question is unavailable")
        receipt = self.g2_runtime.get_receipt(session_token, execution_id)
        if receipt is None:
            return None
        return receipt if isinstance(receipt, dict) else receipt.model_dump(mode="json")

    def _binding(
        self,
        person_id: str,
        source_id: str,
        execution_id: str,
        question: str,
        session_token: str,
    ) -> tuple[Any, str]:
        session = self.g2_runtime.sessions.resolve(session_token)
        if session is None or session.active_person_id != person_id:
            raise PermissionError("session_or_person_unavailable")
        with self.runtime.database.uow() as uow:
            assert uow.connection is not None
            row = uow.connection.execute(
                """SELECT * FROM document_question_bindings WHERE execution_id = ?
                   AND person_id = ? AND source_id = ? AND actor_id = ?""",
                (execution_id, person_id, source_id, session.actor_id),
            ).fetchone()
        descriptor = self.g2_runtime.provider.descriptor
        if (
            row is None
            or row["request_hash"] != hashlib.sha256(question.encode("utf-8")).hexdigest()
            or row["provider_id"] != descriptor.provider_id
            or row["provider_descriptor_hash"] != descriptor.descriptor_hash
            or row["model_id"] != descriptor.model_id
        ):
            raise SourceNotFoundError("document question is unavailable")
        encoded = encode_document_question(
            person_id=person_id,
            source_id=source_id,
            extraction_id=row["extraction_id"],
            input_text_hash=row["input_text_hash"],
            user_question=question,
        )
        return row, encoded
