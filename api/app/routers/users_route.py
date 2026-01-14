from typing import Optional
from core.logging import get_logger
from domain.services.user_service import UserService
from app.dependencies import get_current_user, require_role
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from schemas.users import UserCreate, UserUpdate, UserResponse, UserListResponse, UserRole

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=UserListResponse)
def list_users(
    active_only: int = Query(1, description="Filter to only active users if set to 1"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=100, description="Number of users per page"),
    search: Optional[str] = Query(None, description="Search term to filter users by name or email"),
    current_user=Depends(get_current_user)
) -> UserListResponse:
    """
    Retrieve a paginated list of users with optional filtering by active status and search term.
    """
    try:
        # Log the action with user context
        logger.info(
            "User list requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "search_term": search,
                "page": page,
                "page_size": page_size
            }
        )

        response = UserService.get_all_users(
            active_only=active_only == 1,
            page=page,
            page_size=page_size,
            search=search
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int = Path(..., description="The ID of the user to retrieve"),
    current_user = Depends(get_current_user)
) -> UserResponse:
    """
    Retrieve a single user by their ID.
    """
    try:
        logger.info(
            "User details requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "target_user_id": user_id
            }
        )
        response = UserService.get_user_by_id(user_id)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.post("/register", response_model=UserResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
def create_user(
    user_data: UserCreate,
    current_user=Depends(require_role(UserRole.ADMIN))
) -> UserResponse:
    """
    Create a new user.
    """
    try:
        logger.info(
            "User details requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "new_user_email": user_data.email,
                "new_user_role": user_data.role
            }
        )
        response = UserService.create_user(user_data)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-register", response_model=list[UserResponse], dependencies=[Depends(require_role(UserRole.ADMIN))])
def bulk_create_users(
    users_data: list[UserCreate],
    current_user=Depends(require_role(UserRole.ADMIN))
) -> list[UserResponse]:
    """
    Create multiple users in bulk.
    """
    try:
        logger.info(
            "Bulk user creation requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "number_of_users": len(users_data)
            }
        )
        response = UserService.create_bulk_users(users_data)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
def update_user(
    user_data: UserUpdate,
    user_id: int = Path(..., description="The ID of the user to update"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> UserResponse:
    """
    Update an existing user.
    """
    try:
        logger.info(
            "User details requested",
            extra={
                "requested_by": current_user['id'],
                "requestor_email": current_user['email'],
                "target_fields": list(user_data.model_dump(exclude_unset=True).keys()),
            }
        )
        response = UserService.update_user(user_id, user_data)

        logger.info(
            "User update successfully",
            extra={
                "updated_by": current_user['id'],
                "target_user_id": user_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{user_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
def delete_user(
    user_id: int = Path(..., description="The ID of the user to delete"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> None:
    """
    Delete a user.
    """
    try:
        logger.info(
            "User deletion requested",
            extra={
                "deleted_by": current_user['id'],
                "target_user_id": user_id
            }
        )

        # Prevent self-deletion
        if user_id == current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users cannot delete their own account."
            )
        
        UserService.delete_user(user_id)

        logger.info(
            "User deleted successfully",
            extra={
                "deleted_by": current_user['id'],
                "target_user_id": user_id
            }
        )

        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# @router.patch("/{user_id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
def activate_user(
    user_id: int = Path(..., description="The ID of the user to activate"),
    activate: int = Query(1, description="Set to 1 to activate, 0 to deactivate"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> bool:
    """
    Activate or deactivate a user.
    """
    try:
        logger.info(
            "Activating user",
            extra={
                "activated_by": current_user['id'],
                "target_user_id": user_id
            }
        )
        
        response = UserService.activate_user(user_id=user_id, activate=activate)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.patch("/{user_id}/activate", response_model=UserResponse, dependencies=[Depends(require_role(UserRole.ADMIN))])
def deactivate_user(
    user_id: int = Path(..., description="The ID of the user to activate"),
    deactivate: int = Query(0, description="Set to 0 to deactivate, 1 to activate"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> bool:
    """
    Deactivate a user.
    """
    try:
        logger.info(
            "Deactivating user",
            extra={
                "activated_by": current_user['id'],
                "target_user_id": user_id
            }
        )

        response = UserService.deactivate_user(user_id=user_id, deactivate=deactivate)

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    
# @router