from typing import Optional
from core.logging import get_logger
from domain.services.category_service import CategoryService
from app.dependencies import get_current_user, require_role
from schemas.users import UserRole
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from schemas.categories import Category, CategoryCreate, CategoryUpdate

logger = get_logger(__name__)
router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=list[Category])
def list_categories(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(50, ge=1, le=100, description="Number of categories per page"),
    search: Optional[str] = Query(None, description="Search term for category name"),
    current_user: UserRole = Depends(get_current_user)
) -> list[Category]:
    try:
        logger.info(
            "Category list requested",
            extra={
                "requested_by": current_user,
                "search": search,
                "page": page,
                "page_size": page_size
            }
        )

        categories_data = CategoryService.get_all_categories(
            page=page,
            page_size=page_size,
            search=search
        )

        logger.info(
            "Category list retrieved",
            extra={
                "requested_by": current_user,
                "category_count": len(categories_data)
            }
        )

        return categories_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in list_categories. ", 
            extra={"error": str(e), 
                   "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{category_id}", response_model=Category)
def get_category(
    category_id: int = Path(..., gt=0, description="The ID of the category to retrieve"),
    current_user: UserRole = Depends(get_current_user)
) -> Category:
    try:
        logger.info(
            "Category detail requested",
            extra={
                "requested_by": current_user,
                "category_id": category_id
            }
        )
        
        category_data = CategoryService.get_category_by_id(category_id)

        logger.info(
            "Category detail retrieved",
            extra={
                "requested_by": current_user,
                "category_id": category_id
            }
        )
    
        return category_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_category. ",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "category_id": category_id
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> Category:
    try:
        logger.info(
            "Category creation requested",
            extra={
                "requested_by": current_user,
                "category_name": category_data.name
            }
        )
        response = CategoryService.create_category(category_data)
       
        logger.info(
            "Category created successfully",
            extra={
                "requested_by": current_user,
                "category_id": response.id,
                "category_name": response.name
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating category.",
            extra={
                "error": str(e),
                "requested_by": current_user
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_data: CategoryUpdate,
    category_id: int = Path(..., gt=0, description="The ID of the category to update"),
    current_user: UserRole = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
) -> Category:
    try:
        logger.info(
            "Category update requested",
            extra={
                "requested_by": current_user,
                "category_id": category_id
            }
        )

        response = CategoryService.update_category(category_id, category_data)
        
        logger.info(
            "Category updated successfully",
            extra={
                "requested_by": current_user,
                "category_id": category_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating category.",
            extra={
                "error": str(e),
                "requested_by": current_user,
                "category_id": category_id
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
    
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int = Path(..., gt=0, description="The ID of the category to delete"),
    current_user: dict = Depends(require_role(UserRole.ADMIN))
) -> None:
    try:
        logger.info(
            "Category deletion requested",
            extra={
                "requested_by": current_user.get('id'),
                "category_id": category_id
            }
        )

        CategoryService.delete_category(category_id)

        logger.info(
            "Category deleted successfully",
            extra={
                "requested_by": current_user.get('id'),
                "category_id": category_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting category",
            extra={
                "error": str(e),
                "requested_by": current_user.get('id'),
                "category_id": category_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
