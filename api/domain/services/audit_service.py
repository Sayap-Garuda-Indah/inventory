import json
from typing import Optional, Dict
from fastapi import HTTPException, status
from core.logging import get_logger
from db.repositories.audit_session_repo import AuditSessionRepository
from db.repositories.audit_scans_repo import AuditScansRepository
from db.repositories.audit_log_repo import AuditLogRepository
from db.repositories.item_repo import ItemRepository
from db.repositories.stock_levels_repo import StockLevelsRepository
from schemas.audit import (
    AuditSessionCreate,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditScanCreate,
    AuditScanResponse,
    AuditReconciliationResponse,
    AuditItemSummary,
    AuditScanListResponse,
    AuditSessionNotesUpdate
)

logger = get_logger(__name__)

class AuditService:
    @staticmethod
    def create_session(data: AuditSessionCreate, user_id: int) -> AuditSessionResponse:
        try:
            expected_count = StockLevelsRepository.count_expected_items(data.location_id)
            session = AuditSessionRepository.create(
                location_id=data.location_id,
                started_by=user_id,
                note=data.note,
                expected_count=expected_count
            )
            AuditLogRepository.create(
                actor_user_id=user_id,
                action="AUDIT_SESSION_CREATE",
                entity_type="AUDIT_SESSION",
                entity_id=session['id'],
                session_id=session['id'],
                payload_json={"location_id": data.location_id, "note": data.note}
            )
            response = AuditSessionResponse.model_validate(session)
            
            return response
        except Exception as e:
            logger.error("Failed to create audit session", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create audit session"
            )

    @staticmethod
    def get_session(session_id: int) -> AuditSessionResponse:
        session = AuditSessionRepository.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Audit session not found"
            )
        response = AuditSessionResponse.model_validate(session)

        return response

    @staticmethod
    def _parse_scanned_code(scanned_code: str) -> Dict[str, Optional[str]]:
        code = scanned_code.strip()
        try:
            payload = json.loads(code)
            if isinstance(payload, dict):
                response = {
                    "item_code": payload.get("item_code"),
                    "serial_number": payload.get("serial_number")
                }

                return response
        except json.JSONDecodeError:
            pass
        return {"item_code": code, "serial_number": None}

    @staticmethod
    def list_sessions(
        page: int,
        page_size: int = 50,
        session_status: Optional[str] = None,
        location_id: Optional[int] = None
    ) -> AuditSessionListResponse:
        try:
            if page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page number must be at least 1"
                )
            
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page size must be between 1 and 100"    
            )
            sessions = AuditSessionRepository.list_sessions(
                page=page,
                page_size=page_size,
                status=session_status,
                location_id=location_id
            )

            total = AuditSessionRepository.count_sessions(
                status=session_status,
                location_id=location_id
            )

            response = AuditSessionListResponse(
                sessions=[AuditSessionResponse.model_validate(s) for s in sessions],
                total=total,
                page=page,
                page_size=page_size
            )

            return AuditSessionListResponse.model_validate(response)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to list audit sessions", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list audit sessions"
            )

    @staticmethod
    def create_scan(
        session_id: int, 
        data: AuditScanCreate, 
        user_id: int
    ) -> AuditScanResponse:
        try:
            session = AuditSessionRepository.get_by_id(session_id)
            if not session: 
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audit session not found"
                )
            if session['status'] != 'OPEN':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Audit session is not open"
                )
            
            parsed = AuditService._parse_scanned_code(data.scanned_code)
            item = None
            if parsed.get('item_code'):
                item = ItemRepository.get_by_item_code(parsed['item_code'])
            if not item and parsed.get('serial_number'):
                item = ItemRepository.get_by_serial_number(parsed['serial_number'])

            result = 'UNKNOWN'
            item_id = None

            if item:
                item_id = item['id']
                if not item['active']:
                    result = 'INACTIVE'
                else:
                    level = StockLevelsRepository.get_by_item_location(item_id, session['location_id'])
                    if level and float(level['qty_on_hand']) > 0:
                        result = 'FOUND'
                    else:
                        result = 'WRONG_LOCATION'
                
                if AuditScansRepository.exists_item_in_session(session_id, item_id):
                    result = 'DUPLICATE'
            
            scan = AuditScansRepository.create(
                session_id=session_id,
                scanned_by=user_id,
                scanned_code="",
                item_id=item_id,
                location_id=session['location_id'],
                result=result,
                note=data.note
            )

            unknown_delta = 1 if result == 'UNKNOWN' else 0
            unexpected_delta = 1 if result in ('WRONG_LOCATION', 'INACTIVE') else 0
            AuditSessionRepository.increment_counts(session_id, 1, unknown_delta, unexpected_delta)

            AuditLogRepository.create(
                actor_user_id=user_id,
                action="AUDIT_SCAN",
                entity_type="AUDIT_SESSION",
                entity_id=session_id,
                session_id=session_id,
                payload_json={
                    "result": result,
                    "item_id": item_id,
                    "scanned_code": data.scanned_code
                }
            )

            return AuditScanResponse(**scan)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create audit scan", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create audit scan"
            )
    @staticmethod
    def list_scans(
        session_id: int,
        result: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> AuditScanListResponse:
        try:
            session = AuditSessionRepository.get_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audit session not found"
                )
            
            scans = AuditScansRepository.list_by_session(session_id, result, page, page_size)
            total = AuditScansRepository.count_by_session(session_id)
            response = AuditScanListResponse(
                scans=[AuditScanResponse.model_validate(s) for s in scans],
                total=total,
                page=page,
                page_size=page_size
            )
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to list audit scans", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list audit scans"
            )

    @staticmethod
    def reconcile(session_id: int) -> AuditReconciliationResponse:
        try:
            session = AuditSessionRepository.get_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audit session not found"
                )
            
            expected = StockLevelsRepository.list_expected_by_location(session['location_id'])
            expected_by_id = {row['item_id']: row for row in expected}

            found_ids = set(AuditScansRepository.list_distinct_item_ids_by_result(session_id, ['FOUND', 'DUPLICATE']))
            unexpected_ids = set(AuditScansRepository.list_distinct_item_ids_by_result(session_id, ['WRONG_LOCATION', 'INACTIVE']))
            missing_ids = [item_id for item_id in expected_by_id.keys() if item_id not in found_ids]

            missing_notes = {
                row["item_id"]: row.get("note")
                for row in AuditScansRepository.list_notes_by_result(session_id, "MISSING")
            }
            unexpected_notes = {
                row["item_id"]: row.get("note")
                for row in AuditScansRepository.list_notes_by_result(session_id, "WRONG_LOCATION")
            }
            for row in AuditScansRepository.list_notes_by_result(session_id, "INACTIVE"):
                unexpected_notes[row["item_id"]] = row.get("note")

            found = []
            for item_id in found_ids:
                if item_id in expected_by_id:
                    row = expected_by_id[item_id]
                    found.append(AuditItemSummary(
                        item_id=row['item_id'],
                        item_code=row['item_code'],
                        name=row['name'],
                        active=row['active'],
                        qty_on_hand=float(row['qty_on_hand']),
                        note=None
                    ))
            
            missing = []
            for item_id in missing_ids:
                row = expected_by_id[item_id]
                missing.append(AuditItemSummary(
                    item_id=row['item_id'],
                    item_code=row['item_code'],
                    name=row['name'],
                    active=row['active'],
                    qty_on_hand=float(row['qty_on_hand']),
                    note=missing_notes.get(item_id)
                ))
            
            unexpected = []
            if unexpected_ids:
                for item_id in unexpected_ids:
                    item = ItemRepository.get_by_id(item_id)
                    if item:
                        unexpected.append(AuditItemSummary(
                            item_id=item['id'],
                            item_code=item['item_code'],
                            name=item['name'],
                            active=item['active'],
                            qty_on_hand=None,
                            note=unexpected_notes.get(item_id)
                        ))

            unknown_count = AuditScansRepository.count_unknown(session_id)
            scanned_count = AuditScansRepository.count_by_session(session_id)

            result = AuditReconciliationResponse(
                session_id=session_id,
                expected_count=session['expected_count'],
                scanned_count=scanned_count,
                found_count=len(found),
                missing_count=len(missing),
                unexpected_count=len(unexpected),
                unknown_count=unknown_count,
                found=found,
                missing=missing,
                unexpected=unexpected
            )

            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to reconcile audit session", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reconcile audit session"
            )

    @staticmethod
    def save_notes(session_id: int, payload: AuditSessionNotesUpdate, user_id: int) -> None:
        try:
            session = AuditSessionRepository.get_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audit session not found"
                )

            for note in payload.missing_notes:
                AuditScansRepository.upsert_missing_note(
                    session_id=session_id,
                    item_id=note.item_id,
                    location_id=session["location_id"],
                    user_id=user_id,
                    note=note.note
                )

            for note in payload.unexpected_notes:
                AuditScansRepository.update_note_by_item_results(
                    session_id=session_id,
                    item_id=note.item_id,
                    results=["WRONG_LOCATION", "INACTIVE"],
                    note=note.note
                )

            for note in payload.unknown_notes:
                AuditScansRepository.update_note_by_scan_id(
                    session_id=session_id,
                    scan_id=note.scan_id,
                    note=note.note
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to save audit notes", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save audit notes"
            )
    
    @staticmethod
    def close_session(session_id: int, user_id: int) -> AuditSessionResponse:
        try:
            session = AuditSessionRepository.get_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audit session not found"
                )
            if session['status'] != 'OPEN':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Audit session is not open"
                )
            
            reconciliation = AuditService.reconcile(session_id)
            AuditSessionRepository.update_counts(
                session_id=session_id,
                scanned_count=reconciliation.scanned_count,
                missing_count=reconciliation.missing_count,
                unexpected_count=reconciliation.unexpected_count,
                unknown_count=reconciliation.unknown_count
            )

            AuditSessionRepository.update_status(session_id, 'CLOSED', user_id)

            AuditLogRepository.create(
                actor_user_id=user_id,
                action="AUDIT_SESSION_CLOSE",
                entity_type="AUDIT_SESSION",
                entity_id=session_id,
                session_id=session_id,
                payload_json={}
            )

            updated = AuditSessionRepository.get_by_id(session_id)

            return AuditSessionResponse.model_validate(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to close audit session", extra={"error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close audit session"
            )
    
