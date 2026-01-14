from typing import Optional, List
from core.logging import get_logger
from domain.services.issue_item_service import IssueItemService
from app.dependencies import require_role, get_current_user
from schemas.users import UserRole
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from schemas.issue_items import (
    IssueItemCreate,
    IssueItemUpdate,
    IssueItemResponse,
    IssueItemListResponse,
    IssueItemBulkCreate
)

logger = get_logger(__name__)
router = APIRouter(prefix="/issue-items", tags=["Issue Items"])

@router.get("/", response_model=IssueItemListResponse)
def list_issue_items(
    issue_id: Optional[int] = Query(None, description="Filter by issue ID"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    current_user: dict = Depends(get_current_user)
) -> IssueItemListResponse:
    try:
        logger.info(
            "Issue item list requested",
            extra={
                "requested_by": current_user['id'],
                "issue_id": issue_id,
                "item_id": item_id,
                "page": page,
                "page_size": page_size
            }
        )

        items_data = IssueItemService.get_all_issue_items(
            issue_id=issue_id,
            item_id=item_id,
            page=page,
            page_size=page_size
        )

        return items_data
    except Exception as e:
        logger.error(f"Error listing issue items: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    
@router.get("/issue/{issue_id}", response_model=List[IssueItemResponse])
def get_items_by_issue(
    issue_id: int = Path(..., gt=0, description="ID of the issue"),
    current_user: dict = Depends(get_current_user)
) -> List[IssueItemResponse]:
    try:
        logger.info(
            "Items for issue requested",
            extra={
                "requested_by": current_user['id'],
                "issue_id": issue_id
            }
        )

        items = IssueItemService.get_items_by_issue_id(issue_id=issue_id)

        logger.info(
            "Items for issue retrieved",
            extra={
                "requested_by": current_user['id'],
                "issue_id": issue_id,
                "item_count": len(items)
            }
        )

        return items
    except Exception as e:
        logger.error(f"Error retrieving items for issue {issue_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    
@router.get("/{issue_item_id}", response_model=IssueItemResponse)
def get_issue_item(
    issue_item_id: int = Path(..., gt=0, description="ID of the issue item"),
    current_user: dict = Depends(get_current_user)
) -> IssueItemResponse:
    try:
        logger.info(
            "Issue item detail requested",
            extra={
                "requested_by": current_user['id'],
                "issue_item_id": issue_item_id
            }
        )

        item = IssueItemService.get_issue_item_by_id(issue_item_id=issue_item_id)
        if not item:
            logger.warning(
                "Issue item not found",
                extra={
                    "requested_by": current_user['id'],
                    "issue_item_id": issue_item_id
                }
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue item not found")
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve issue item",
            extra={"error": str(e), "issue_item_id": issue_item_id}
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.post("/", response_model=IssueItemResponse, status_code=status.HTTP_201_CREATED)
def create_issue_item(
    issue_item_data: IssueItemCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> IssueItemResponse:
    try:
        logger.info(
            "Issue item creation requested",
            extra={
                "created_by": current_user['id'],
                "issue_id": issue_item_data.issue_id,
                "item_id": issue_item_data.item_id,
                "qty": issue_item_data.qty
            }
        )

        response = IssueItemService.create_issue_item(issue_item_data)

        logger.info(
            "Issue item created successfully",
            extra={
                "created_by": current_user['id'],
                "issue_item_id": response.id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create issue item",
            extra={
                "error": str(e),
                "issue_id": issue_item_data.issue_id,
                "item_id": issue_item_data.item_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@router.post("/bulk", response_model=List[IssueItemResponse], status_code=status.HTTP_201_CREATED)
def create_bulk_issue_items(
    bulk_data: IssueItemBulkCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> List[IssueItemResponse]:
    try:
        logger.info(
            "Bulk issue item creation requested",
            extra={
                "created_by": current_user['id'],
                "issue_id": bulk_data.issue_id,
                "item_count": len(bulk_data.items)
            }
        )

        response = IssueItemService.create_bulk_issue_items(bulk_data)

        logger.info(
            "Bulk issue items created successfully",
            extra={
                "created_by": current_user['id'],
                "issue_id": bulk_data.issue_id,
                "created_count": len(response)
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create bulk issue items",
            extra={
                "error": str(e),
                "issue_id": bulk_data.issue_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
    
@router.put("/{issue_item_id}", response_model=IssueItemResponse)
def update_issue_item(
    issue_item_data: IssueItemUpdate,
    issue_item_id: int = Path(..., gt=0, description="ID of the issue item to update"),
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> IssueItemResponse:
    try:
        logger.info(
            "Issue item update requested",
            extra={
                "updated_by": current_user['id'],
                "issue_item_id": issue_item_id,
                "new_qty": issue_item_data.qty
            }
        )

        response = IssueItemService.update_issue_item(issue_item_id, issue_item_data)

        logger.info(
            "Issue item updated successfully",
            extra={
                "updated_by": current_user['id'],
                "issue_item_id": issue_item_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update issue item",
            extra={
                "error": str(e),
                "issue_item_id": issue_item_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
    
@router.delete("/{issue_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_issue_item(
    issue_item_id: int = Path(..., gt=0, description="ID of the issue item to delete"),
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> None:
    try:
        logger.info(
            "Issue item deletion requested",
            extra={
                "deleted_by": current_user['id'],
                "issue_item_id": issue_item_id
            }
        )

        result = IssueItemService.delete_issue_item(issue_item_id)

        logger.info(
            "Issue item deleted successfully",
            extra={
                "deleted_by": current_user['id'],
                "issue_item_id": issue_item_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete issue item",
            extra={
                "error": str(e),
                "issue_item_id": issue_item_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
