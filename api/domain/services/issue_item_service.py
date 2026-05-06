from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from db.repositories.issue_item_repo import IssueItemRepository
from db.repositories.issue_repo import IssueRepository
from db.repositories.item_repo import ItemRepository
from schemas.users import UserRole
from schemas.issue_items import (
    IssueItemCreate,
    IssueItemUpdate,
    IssueItemResponse,
    IssueItemListResponse,
    IssueItemBulkCreate
)
from core.logging import get_logger

logger = get_logger(__name__)

class IssueItemService:
    @staticmethod
    def _is_staff(current_user: Dict[str, Any]) -> bool:
        return str(current_user.get("role", "")).upper() == UserRole.STAFF.value
    
    @staticmethod
    def _assert_issue_access(issue_id: int, current_user: dict) -> dict:
        issue = IssueRepository.get_by_id(issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue {issue_id} not found"
            )
        if IssueItemService._is_staff(current_user) and issue.get("requested_by") != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access items for this issue"
             )
        
        return issue

    @staticmethod
    def _assert_item_access(item_id: int, current_user: dict) -> dict:
        item = ItemRepository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found"
            )
        
        if IssueItemService._is_staff(current_user) and item.get("owner_user_id") != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this item"
             )

        return item


    @staticmethod
    def get_all_issue_items(
        issue_id: Optional[Any] = None,
        item_id: Optional[Any] = None,
        page: int = 1,
        page_size: int = 50,
        current_user: Dict[str, Any] | None = None
    ) -> IssueItemListResponse:
        try:
            if current_user and IssueItemService._is_staff(current_user) and not issue_id and not item_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Issue ID or item ID is required for staff users to filter issue items"
                )
            if issue_id and current_user:
                IssueItemService._assert_issue_access(issue_id, current_user)
            if item_id and current_user:
                IssueItemService._assert_item_access(item_id, current_user)

            offset = (page - 1) * page_size
            issue_items_data = IssueItemRepository.get_all(issue_id=issue_id, item_id=item_id, limit=page_size, offset=offset)

            if current_user and IssueItemService._is_staff(current_user):
                filtered = []
                for row in issue_items_data:
                    item = ItemRepository.get_by_id(row['item_id'])
                    if item and item.get("owner_user_id") == current_user.get("id"):
                        filtered.append(row)
                issue_items_data = filtered
            
            total = IssueItemRepository.count(issue_id=issue_id, item_id=item_id)
            issue_items = [IssueItemResponse(**item) for item in issue_items_data]

            response = IssueItemListResponse(
                issue_item=issue_items,
                total=total,
                page=page,
                page_size=page_size,
            )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve issue items",
                extra={
                    "error": str(e),
                    "issue_id": issue_id,
                    "item_id": item_id,
                })
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def get_issue_item_by_id(issue_item_id: int, current_user: dict) -> IssueItemResponse:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue item ID")
            
            issue_item_data = IssueItemRepository.get_by_id(issue_item_id)
            if not issue_item_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue item {issue_item_id} not found")
            
            IssueItemService._assert_issue_access(issue_item_data['issue_id'], current_user)
            IssueItemService._assert_item_access(issue_item_data['item_id'], current_user)
            response = IssueItemResponse(**issue_item_data)

            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve issue item by ID",
                extra={
                    "error": str(e),
                    "issue_item_id": issue_item_id,
                })
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    @staticmethod
    def get_items_by_issue_id(issue_id: int, current_user: dict) -> List[IssueItemResponse]:
        try:
            if not isinstance(issue_id, int) or issue_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue ID")
            
            IssueItemService._assert_issue_access(issue_id, current_user)
            issue_items_data = IssueItemRepository.get_by_issue_id(issue_id)

            if IssueItemService._is_staff(current_user):
                filtered = []
                for row in issue_items_data:
                    item = ItemRepository.get_by_id(row['item_id'])
                    if item and item.get("owner_user_id") == current_user.get("id"):
                        filtered.append(row)
                issue_items_data = filtered

            issue_items = [IssueItemResponse(**item) for item in issue_items_data]

            return issue_items
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve items by issue ID",
                extra={
                    "error": str(e),
                    "issue_id": issue_id,
                })
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def create_issue_item(issue_item_data: IssueItemCreate, current_user: dict) -> IssueItemResponse:
        try:
            if not IssueRepository.exists_by_id(issue_item_data.issue_id):
                logger.warning(
                    "Issue item creation failed: issue not found",
                    extra={"issue_id": issue_item_data.issue_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Issue {issue_item_data.issue_id} not found"
                )
            
            if not ItemRepository.exists_by_id(issue_item_data.item_id):
                logger.warning(
                    "Issue item creation failed: item not found",
                    extra={"item_id": issue_item_data.item_id}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {issue_item_data.item_id} not found"
                )
            
            IssueItemService._assert_issue_access(issue_item_data.issue_id, current_user)
            IssueItemService._assert_item_access(issue_item_data.item_id, current_user)
            
            if IssueItemRepository.exists_by_issue_and_item(issue_item_data.issue_id, issue_item_data.item_id):
                logger.warning(
                    "Issue item creation failed: issue item already exists",
                    extra={
                        "issue_id": issue_item_data.issue_id,
                        "item_id": issue_item_data.item_id
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Issue item with issue ID {issue_item_data.issue_id} and item ID {issue_item_data.item_id} already exists"
                )
            
            # Check if issue is in DRAFT status (can't add items to approved/issued issues)
            issue = IssueRepository.get_by_id(issue_item_data.issue_id)
            if issue and issue['status'] not in ['DRAFT']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add items to approved or issued issues")
            
            created_item = IssueItemRepository.create(issue_item_data)
            if not created_item:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create issue item")

            logger.info(
                "Issue item created sucessfully",
                extra={
                    "issue_item_id": created_item['id'],
                    "issue_id": issue_item_data.issue_id,
                    "item_id": issue_item_data.item_id
                }
            )

            response = IssueItemResponse(**created_item)

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
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def create_bulk_issue_items(bulk_data: IssueItemBulkCreate, current_user: dict) -> List[IssueItemResponse]:
        created_items = []
        try:
            if not IssueRepository.exists_by_id(bulk_data.issue_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Issue {bulk_data.issue_id} not found"
                )
            
            IssueItemService._assert_issue_access(bulk_data.issue_id, current_user)

            # Check if issue is in DRAFT status
            issue = IssueRepository.get_by_id(bulk_data.issue_id)
            if issue and issue['status'] not in ['DRAFT']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot add items to approved or issued issues")
            
            # Validate all items before creation
            for item in bulk_data.items:
                if not ItemRepository.exists_by_id(item['item_id']):
                    logger.warning(
                        "Bulk issue item creation failed: item not found",
                        extra={"item_id": item['item_id']}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Item {item['item_id']} not found"
                    )
                
            created_items_data = IssueItemRepository.create_bulk(bulk_data.issue_id, bulk_data.items)

            logger.info(
                "Bulk issue items created successfully",
                extra={
                    "issue_id": bulk_data.issue_id,
                    "num_items": len(created_items_data)
                }
            )

            created_items = [IssueItemResponse(**item) for item in created_items_data]

            return created_items
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to create bulk issue items",
                extra={
                    "error": str(e),
                    "bulk_data": bulk_data.model_dump()
                }
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def delete_issue_item(issue_item_id: int, current_user: dict) -> dict:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue item ID")

            existing_item = IssueItemRepository.get_by_id(issue_item_id)
            if not existing_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue item {issue_item_id} not found")
            
            IssueItemService._assert_issue_access(existing_item['issue_id'], current_user)
            IssueItemService._assert_item_access(existing_item['item_id'], current_user)

            # Check if parent issue is in DRAFT status
            issue = IssueRepository.get_by_id(existing_item['issue_id'])
            if issue and issue['status'] not in ['DRAFT']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete items from approved or issued issues")
            
            success = IssueItemRepository.delete(issue_item_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete issue item")
            
            logger.info(
                "Issue item deleted successfully",
                extra={
                    "issue_item_id": issue_item_id,
                    "issue_id": existing_item['issue_id'],
                    "item_id": existing_item['item_id']
                }
            )

            message = {"message": f"Issue item {issue_item_id} deleted successfully"}

            return message
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to delete issue item",
                extra={
                    "error": str(e),
                    "issue_item_id": issue_item_id,
                })
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def update_issue_item(issue_item_id: int, issue_item_data: IssueItemUpdate, current_user: dict) -> IssueItemResponse:
        try:
            if not isinstance(issue_item_id, int) or issue_item_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid issue item ID")
            
            # Check if issue item exists
            existing_item = IssueItemRepository.get_by_id(issue_item_id)
            if not existing_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Issue item {issue_item_id} not found")
            
            IssueItemService._assert_issue_access(existing_item['issue_id'], current_user)
            IssueItemService._assert_item_access(existing_item['item_id'], current_user)

            # Check if parent issue is in DRAFT status
            issue = IssueRepository.get_by_id(existing_item['issue_id'])
            if issue and issue['status'] not in ['DRAFT']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update items from approved or issued issues")

            updated_item = IssueItemRepository.update(issue_item_id, issue_item_data)
            if not updated_item:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update issue item")
            
            logger.info(
                "Issue item updated successfully",
                extra={
                    "issue_item_id": issue_item_id,
                    "issue_id": existing_item['issue_id'],
                    "item_id": existing_item['item_id']
                }
            )

            response = IssueItemResponse(**updated_item)

            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to update issue item",
                extra={
                    "error": str(e),
                    "issue_item_id": issue_item_id,
                })
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
