from typing import List, Optional
from fastapi import HTTPException, status
from db.repositories.category_repo import CategoryRepository
from schemas.categories import Category, CategoryCreate, CategoryUpdate
from core.logging import get_logger

logger = get_logger(__name__)

class CategoryService:
    @staticmethod
    def get_all_categories(
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None
    ) -> List[Category]:
        """
        Get paginated list of categories with optional search.
        """
        try:
            if page < 1:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be at least 1")
            if page_size < 1 or page_size > 100:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be between 1 and 100")
            
            offset = (page - 1) * page_size
            categories_data = CategoryRepository.get_all(page_size, offset, search)

            categories = [Category(**category) for category in categories_data]
            return categories
        except HTTPException:
            raise 
        except Exception as e:
            logger.error(f"Error in get_all_categories: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def get_category_by_id(category_id: int) -> Category:
        """
        Get a category by its ID.
        """
        try:
            if not isinstance(category_id, int) or category_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid category ID")
            
            category_data = CategoryRepository.get_by_id(category_id)
            if not category_data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {category_id} not found")
            
            return Category(**category_data)
        except HTTPException:
            raise 
        except Exception as e:
            logger.error(f"Error in get_category_by_id: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def create_category(category_create: CategoryCreate) -> Category:
        """
        Create a new category.
        """
        try:
            if CategoryRepository.exists_by_name(category_create.name):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this name already exists")
            
            category_id = CategoryRepository.create(category_create)
            category_data = CategoryRepository.get_by_id(category_id)
            
            if not category_data:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created category")
            
            data = Category(**category_data)
            return data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in create_category: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def update_category(category_id: int, category_update: CategoryUpdate) -> Category:
        """
        Update an existing category.
        """
        try:
            if not isinstance(category_id, int) or category_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID")
            
            existing_category = CategoryRepository.get_by_id(category_id)
            if not existing_category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {category_id} not found")
            
            existing_category_name = existing_category['name']
            if category_update.name and category_update.name != existing_category_name:
                if CategoryRepository.exists_by_name(category_update.name):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this name already exists")
                
            CategoryRepository.update(category_id, category_update)
            updated_category_data = CategoryRepository.get_by_id(category_id)

            if not updated_category_data:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated category")
            
            data = Category(**updated_category_data)
            return data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_category: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def category_exists(category_id: int) -> bool:
        """
        Check if a category exists by its ID.
        """
        try:
            if not isinstance(category_id, int) or category_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID")
            
            exists = CategoryRepository.get_by_id(category_id) is not None
            return exists
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in category_exists: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    @staticmethod
    def delete_category(category_id: int) -> dict:
        """
        Delete a category by its ID.
        """
        try:
            if not isinstance(category_id, int) or category_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID")
            
            existing_category = CategoryRepository.get_by_id(category_id)
            if not existing_category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category {category_id} not found")

            if existing_category["name"] == CategoryRepository.FALLBACK_CATEGORY_NAME:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fallback category '-' cannot be deleted")

            result = CategoryRepository.soft_delete_and_reassign(category_id)

            logger.info(
                "Category soft-deleted successfully",
                extra={
                    "category_id": category_id,
                    "category_name": result["deleted_category_name"],
                    "reassigned_items": result["reassigned_items"],
                    "replacement_category_id": result["replacement_category_id"],
                },
            )

            warning = None
            if result["reassigned_items"] > 0:
                warning = (
                    f"{result['reassigned_items']} item(s) were linked to this category "
                    f"and reassigned to '{result['replacement_category_name']}'."
                )

            return {
                "message": f"Category '{result['deleted_category_name']}' soft-deleted successfully.",
                "warning": warning,
                "reassigned_items": result["reassigned_items"],
                "replacement_category_name": result["replacement_category_name"],
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in delete_category: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
