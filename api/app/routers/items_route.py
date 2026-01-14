from typing import Optional
from core.logging import get_logger
from domain.services.item_service import ItemService
from app.dependencies import require_role
from schemas.users import UserRole
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from schemas.items import ItemResponse, ItemListResponse, ItemCreate, ItemUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/items", tags=["Items"])

@router.get("/", response_model=ItemListResponse)
def list_items(
    active_only: int = Query(1, description="Filter to only active items"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search term for SKU or name"),
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> ItemListResponse:
    try:
        logger.info(
            "Item list requested",
            extra={
                "requested_by": current_user,
                "search": search,
                "active_only": active_only,
                "page": page,
                "page_size": page_size
            }
        )

        items_data = ItemService.get_all_items(
            active_only=bool(active_only),
            page=page,
            page_size=page_size,
            search=search
        )

        logger.info(
            "Item list retrieved",
            extra={
                "requested_by": current_user,
                "item_count": len(items_data.items)
            }
        )

        return items_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in list_items.",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve"),
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> ItemResponse:
    try:
        logger.info(
            "Item detail requested",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )

        item_data = ItemService.get_item_by_id(item_id)
        
        logger.info(
            "Item detail retrieved",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )

        return item_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_item.",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "item_id": item_id
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.STAFF))])
def create_item(
    item_data: ItemCreate,
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> ItemResponse:
    try:
        logger.info(
            "Item creation requested",
            extra={
                "requested_by": current_user,
                "item_unit_id": item_data.unit_id
            }
        )

        response = ItemService.create_item(item_data)
        
        logger.info(
            "Item created successfully",
            extra={
                "requested_by": current_user,
                "item_id": response.id,
                "item_unit_id": response.unit_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in create_item. ",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
    
@router.put("/{item_id}", response_model=ItemResponse, dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.STAFF))])
def update_item(
    item_data: ItemUpdate,
    item_id: int = Path(..., gt=0, description="The ID of the item to update"),
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> ItemResponse:
    try:
        logger.info(
            "Item update requested",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )
        
        response = ItemService.update_item(item_id, item_data)
        
        logger.info(
            "Item updated successfully",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
    
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(UserRole.ADMIN))])
def delete_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to delete"),
    current_user: UserRole = Depends(require_role(UserRole.ADMIN))
) -> None:
    try:
        logger.info(
            "Item deletion requested",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )

        ItemService.delete_item(item_id)

        logger.info(
            "Item deleted successfully",
            extra={
                "requested_by": current_user,
                "item_id": item_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in delete_item.",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "item_id": item_id
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
