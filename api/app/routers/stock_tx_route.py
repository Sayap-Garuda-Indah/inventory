from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status, Body
from app.dependencies import require_role, get_current_user
from schemas.users import UserRole
from schemas.stock_tx import StockTxCreate, StockTxUpdate, StockTxListResponse, StockTxResponse
from schemas.stock_levels import StockLevelListResponse
from domain.services.stock_service import StockService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=StockTxListResponse)
def list_transactions(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of transactions per page"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    tx_type: Optional[str] = Query(None, description="Filter by transaction type"),
    search: Optional[str] = Query(None, description="Search term for item/location/ref/note"),
    current_user=Depends(get_current_user)
) -> StockTxListResponse:
    try:
        return StockService.list_transactions(
            page=page,
            page_size=page_size,
            item_id=item_id,
            location_id=location_id,
            tx_type=tx_type,
            search=search
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list transactions", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{tx_id}", response_model=StockTxResponse)
def get_transaction(
    tx_id: int = Path(..., gt=0, description="Transaction ID"),
    current_user=Depends(get_current_user)
) -> StockTxResponse:
    try:
        return StockService.get_transaction(tx_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get transaction", extra={"error": str(e), "tx_id": tx_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/stock-levels", response_model=StockLevelListResponse)
def list_stock_levels(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of stock levels per page"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    search: Optional[str] = Query(None, description="Search term for item/location"),
    current_user=Depends(get_current_user)
) -> StockLevelListResponse:
    try:
        return StockService.list_stock_levels(
            page=page,
            page_size=page_size,
            item_id=item_id,
            location_id=location_id,
            search=search
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list stock levels", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/", response_model=StockTxResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_data: StockTxCreate,
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> StockTxResponse:
    try:
        return StockService.create_transaction(tx_data, current_user["id"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create transaction", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/{tx_id}", response_model=StockTxResponse)
def update_transaction(
    tx_data: StockTxUpdate = Body(...),
    tx_id: int = Path(..., gt=0, description="Transaction ID"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> StockTxResponse:
    try:
        return StockService.update_transaction(tx_id, tx_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update transaction", extra={"error": str(e), "tx_id": tx_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{tx_id}", status_code=status.HTTP_200_OK)
def delete_transaction(
    tx_id: int = Path(..., gt=0, description="Transaction ID"),
    current_user=Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> dict:
    try:
        return StockService.delete_transaction(tx_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete transaction", extra={"error": str(e), "tx_id": tx_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
