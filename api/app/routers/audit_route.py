from typing import Optional
from core.logging import get_logger
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from app.dependencies import require_role
from schemas.users import UserRole
from schemas.audit import (
    AuditSessionCreate,
    AuditSessionResponse,
    AuditSessionListResponse,
    AuditScanCreate,
    AuditScanResponse,
    AuditReconciliationResponse,
    AuditScanListResponse
)
from domain.services.audit_service import AuditService

logger = get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.post(
        "/sessions", 
        response_model=AuditSessionResponse, 
        dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def create_session(
    payload: AuditSessionCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditSessionResponse:
    try:
        logger.info(
            "Audit session creation requested",
            extra={
                "requested_by": current_user,
                "location_id": payload.location_id
            }
        )

        return AuditService.create_session(payload, current_user['id'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error logging audit session creation request.",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
        "/sessions", 
        response_model=AuditSessionListResponse, 
        dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def list_sessions(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of sessions per page"),
    session_status: Optional[str] = Query(None, description="Filter by session status"),
    location_id: Optional[int] = Query(None, gt=0, description="Filter by location ID"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditSessionListResponse:
    try:
        logger.info(
            "Audit session list requested",
            extra={
                "requested_by": current_user,
                "session_status": session_status,
                "location_id": location_id,
                "page": page,
                "page_size": page_size
            }
        )

        return AuditService.list_sessions(page, page_size, session_status, location_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in list_sessions.",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
        "/sessions/{session_id}", 
        response_model=AuditSessionResponse, 
        dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def get_session(
    session_id: int = Path(..., gt=0, description="ID of the audit session"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditSessionResponse:
    try:
        logger.info(
            "Audit session detail requested",
            extra={
                "requested_by": current_user,
                "session_id": session_id
            }
        )

        return AuditService.get_session(session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_session.",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/sessions/{session_id}/scans", 
    response_model=AuditScanResponse, 
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def create_scan(
    payload: AuditScanCreate,
    session_id: int = Path(..., gt=0, description="ID of the audit session"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditScanResponse:
    try:
        logger.info(
            "Audit scan creation requested",
            extra={
                "requested_by": current_user,
                "session_id": session_id,
                "scanned_code": payload.scanned_code
            }
        )
        
        return AuditService.create_scan(session_id, payload, current_user['id'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in create_scan.",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "session_id": session_id,
                "scanned_code": payload.scanned_code
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/sessions/{session_id}/scans", 
    response_model=AuditScanListResponse, 
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def list_scans(
    session_id: int = Path(..., gt=0, description="ID of the audit session"),
    result: Optional[str] = Query(None, description="Filter by scan result"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditScanListResponse:
    try:
        logger.info(
            "Audit scan list requested",
            extra={
                "requested_by": current_user,
                "session_id": session_id,
                "result": result
            }
        )

        return AuditService.list_scans(session_id, result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in list_scans.",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "session_id": session_id
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/sessions/{session_id}/reconciliation", 
    response_model=AuditReconciliationResponse, 
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def get_reconciliation(
    session_id: int = Path(..., gt=0, description="ID of the audit session"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditReconciliationResponse:
    try:
        logger.info(
            "Audit reconciliation requested",
            extra={
                "requested_by": current_user,
                "session_id": session_id
            }
        )

        return AuditService.reconcile(session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_reconciliation.",
            extra={
                "error": str(e),
                "session_id": session_id,
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/sessions/{session_id}/close", 
    response_model=AuditSessionResponse, 
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))]
)
def close_session(
    session_id: int = Path(..., gt=0, description="ID of the audit session"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR))
) -> AuditSessionResponse:
    try:
        logger.info(
            "Audit session close requested",
            extra={
                "requested_by": current_user,
                "session_id": session_id
            }
        )

        return AuditService.close_session(session_id, current_user['id'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in close_session.",
            extra={
                "error": str(e),
                "session_id": session_id,
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
