from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from db.repositories.item_repo import ItemRepository
from db.repositories.category_repo import CategoryRepository
from db.repositories.units_repo import UnitsRepository
from schemas.users import UserRole
from schemas.items import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from core.logging import get_logger

logger = get_logger(__name__)

class ItemService:
    @staticmethod
    def _is_staff(current_user: Dict[str, Any]) -> bool:
        return str(current_user.get("role", "")).upper() == UserRole.STAFF.value
    
    @staticmethod
    def _ensure_item_owner_for_staff(item_data: dict, current_user: Dict[str, Any]) -> None:
        if ItemService._is_staff(current_user) and item_data.get("owner_user_id") != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff users can only manage their own items"
            )

    @staticmethod
    def get_all_items(
        active_only: bool = True,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] | None = None
    ) -> ItemListResponse:
        """ 
        Get paginated list of items with optional filters.
        """
        try:
            if page < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
            if page_size < 1 or page_size > 100:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")
            
            owner_scope = None
            if current_user and ItemService._is_staff(current_user):
                owner_scope = current_user["id"]

            offset = (page - 1) * page_size
            items_data = ItemRepository.get_all(active_only, page_size, offset, search, owner_scope)
            total = ItemRepository.count(active_only, search, owner_scope)
            items = [ItemResponse(**item) for item in items_data]

            results = ItemListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )

            return results
        except HTTPException:
            raise 
        except Exception as e:
            logger.error(f"Error in get_all_items: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def get_item_by_id(item_id: int, current_user: Dict[str, Any]) -> ItemResponse:
        """
        Get an item by its ID.
        """
        try:
            if not isinstance(item_id, int) or item_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid item ID")
            
            item_data = ItemRepository.get_by_id(item_id)
            if not item_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found")
            
            ItemService._ensure_item_owner_for_staff(item_data, current_user)
            
            return ItemResponse(**item_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve item by ID {item_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def create_item(item_data: ItemCreate, current_user: Dict[str, Any]) -> ItemResponse:
        """
        Create a new item.
        """
        try:
            payload = item_data.model_dump()
            if ItemService._is_staff(current_user):
                payload["owner_user_id"] = current_user["id"]

            validated_item = ItemCreate(**payload)

            # # Validate foreign keys
            # if not CategoryRepository.exists_by_sku(item_data.category_id):
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {item_data.category_id} does not exist")
            
            # validate category exists
            if not CategoryRepository.exists_by_id(validated_item.category_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {validated_item.category_id} does not exist")
            
            # Validate unit exists
            if not UnitsRepository.exists_by_id(validated_item.unit_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit ID {validated_item.unit_id} does not exist")

            # Check by Item Code uniqueness
            if ItemRepository.exists_by_item_code(validated_item.item_code):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item code {validated_item.item_code} already exists")

            created_item = ItemRepository.create(validated_item)
            if not created_item:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create item")
            
            ItemService._ensure_item_owner_for_staff(created_item, current_user)

            logger.info(f"Item created with ID {created_item['id']}")

            return ItemResponse(**created_item)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create item: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def update_item(item_id: int, item_data: ItemUpdate, current_user: Dict[str, Any]) -> ItemResponse:
        """
        Update an existing item.
        """
        try:
            if not isinstance(item_id, int) or item_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")
            
            # If item id is not found
            existing_item = ItemRepository.get_by_id(item_id)
            if not existing_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found")

            ItemService._ensure_item_owner_for_staff(existing_item, current_user)

            update_payload = item_data.model_dump(exclude_unset=True)
            if ItemService._is_staff(current_user):
                if "owner_user_id" in update_payload and update_payload["owner_user_id"] != current_user["id"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Staff users can only assign ownership to themselves"
                    )
                update_payload["owner_user_id"] = current_user["id"]

            validate_update = ItemUpdate(**update_payload)

            # Check Item Code uniqueness if updating Item Code
            if validate_update.item_code and validate_update.item_code.strip().upper() != existing_item['item_code']:
                if ItemRepository.exists_by_item_code(validate_update.item_code):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item code {validate_update.item_code} already exists")
                
            # Validate category/unit if being updated
            if validate_update.category_id and not CategoryRepository.exists_by_id(validate_update.category_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {validate_update.category_id} does not exist")
            
            if validate_update.unit_id and not UnitsRepository.exists_by_id(validate_update.unit_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit ID {validate_update.unit_id} does not exist")
            
            updated_item = ItemRepository.update(item_id, validate_update)
            if not updated_item:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update item")
            
            logger.info(f"Item with ID {item_id} updated")

            return ItemResponse(**updated_item)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update item ID {item_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def delete_item(item_id: int) -> dict:
        """
        Soft delete an item by setting its active status to False.
        """
        try:
            if not isinstance(item_id, int) or item_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")

            existing_item = ItemRepository.get_by_id(item_id)
            if not existing_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found")

            if existing_item.get("active") in (False, 0):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item {item_id} is already inactive")

            dependencies = ItemRepository.get_dependency_summary(item_id)
            
            success = ItemRepository.delete(item_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete item")
            
            logger.info(
                "Item soft-deleted successfully",
                extra={
                    "item_id": item_id,
                    "item_code": existing_item["item_code"],
                    "dependencies": dependencies,
                }
            )

            total_dependencies = sum(dependencies.values())
            warning = None
            if total_dependencies > 0:
                warning = (
                    f"Related records remain for history (issue items, stock levels, "
                    f"stock transactions, scans): {total_dependencies}."
                )

            message = {
                "message": f"Item {existing_item['name']} (ID: {item_id}, code: {existing_item['item_code']}) has been deactivated.",
                "warning": warning,
                "dependencies": dependencies,
            }

            return message
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete item ID {item_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
        
