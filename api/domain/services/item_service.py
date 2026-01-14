from typing import Optional
from fastapi import HTTPException, status
from db.repositories.item_repo import ItemRepository
from db.repositories.category_repo import CategoryRepository
from db.repositories.units_repo import UnitsRepository
from schemas.items import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from core.logging import get_logger

logger = get_logger(__name__)

class ItemService:
    @staticmethod
    def get_all_items(
        active_only: bool = True,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None
    ) -> ItemListResponse:
        """ 
        Get paginated list of items with optional filters.
        """
        try:
            if page < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
            if page_size < 1 or page_size > 100:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")
            
            offset = (page - 1) * page_size
            items_data = ItemRepository.get_all(active_only, page_size, offset, search)
            total = ItemRepository.count(active_only, search)

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
    def get_item_by_id(item_id: int) -> ItemResponse:
        """
        Get an item by its ID.
        """
        try:
            if not isinstance(item_id, int) or item_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid item ID")
            
            item_data = ItemRepository.get_by_id(item_id)
            if not item_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found")
            
            return ItemResponse(**item_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve item by ID {item_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def create_item(item_data: ItemCreate) -> ItemResponse:
        """
        Create a new item.
        """
        try:
            # # Validate foreign keys
            # if not CategoryRepository.exists_by_sku(item_data.category_id):
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {item_data.category_id} does not exist")
            
            # validate category exists
            if not CategoryRepository.exists_by_id(item_data.category_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {item_data.category_id} does not exist")
            
            # Validate unit exists
            if not UnitsRepository.exists_by_id(item_data.unit_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit ID {item_data.unit_id} does not exist")
            
            # Check by Item Code uniqueness
            if ItemRepository.exists_by_item_code(item_data.item_code):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item code {item_data.item_code} already exists")

            created_item = ItemRepository.create(item_data)
            if not created_item:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create item")
            
            logger.info(f"Item created with ID {created_item['id']}")

            return ItemResponse(**created_item)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create item: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
    @staticmethod
    def update_item(item_id: int, item_data: ItemUpdate) -> ItemResponse:
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

            # Check Item Code uniqueness if updating Item Code
            if item_data.item_code and item_data.item_code.strip().upper() != existing_item['item_code']:
                if ItemRepository.exists_by_item_code(item_data.item_code):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item code {item_data.item_code} already exists")
                
            # Validate category/unit if being updated
            if item_data.category_id and not CategoryRepository.exists_by_id(item_data.category_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category ID {item_data.category_id} does not exist")
            
            if item_data.unit_id and not UnitsRepository.exists_by_id(item_data.unit_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unit ID {item_data.unit_id} does not exist")
            
            updated_item = ItemRepository.update(item_id, item_data)
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
            existing_item = ItemRepository.get_by_id(item_id)
            if not existing_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found")
            
            success = ItemRepository.delete(item_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete item")
            
            logger.info(f"Item with ID {existing_item['sku']} deleted (soft delete)")

            message = {"message": f"Item {existing_item['name']} (ID: {item_id}) with SKU {existing_item['sku']} has been deleted."}

            return message
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete item ID {item_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        
        