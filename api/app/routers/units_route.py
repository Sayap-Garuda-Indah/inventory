from typing import Optional
from core.logging import get_logger
from schemas.users import UserRole
from domain.services.unit_service import UnitService
from app.dependencies import require_role
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from app.dependencies import require_role
from domain.services.unit_service import UnitService
from schemas.units import UnitCreate, UnitUpdate, UnitResponse, UnitListResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/units", tags=["units"])

@router.get("", response_model=UnitListResponse)
@router.get("/", response_model=UnitListResponse, include_in_schema=False)
def list_units(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, ge=1, le=100, description="Number of units per page"),
    search: Optional[str] = Query(None, description="Search term to filter units by name or symbol"),
) -> UnitListResponse:
    try:
        logger.info(
            "Unit list requested",
            extra={
                "page": page,
                "page_size": page_size,
                "search": search
            }
        )

        response = UnitService.get_all_units(
            page=page,
            page_size=page_size,
            search=search
        )

        logger.info(
            "Unit list retrieved",
            extra={
                "unit_count": len(response.units)
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in list_units.",
            extra={
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    

@router.get("/{unit_id}", response_model=UnitResponse)
def get_unit(
    unit_id: int = Path(..., description="The ID of the unit to retrieve"),
) -> UnitResponse:
    """
    Retrieve a single unit by its ID.
    """
    try:
        logger.info(
            "Unit detail requested",
            extra={
                "unit_id": unit_id
            }
        )

        response = UnitService.get_unit_by_id(unit_id)

        logger.info(
            "Unit detail retrieved",
            extra={
                "unit_id": unit_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error in get_unit.",
            extra={
                "error": str(e),
                "unit_id": unit_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.post("", response_model=UnitResponse)
@router.post("/", response_model=UnitResponse, include_in_schema=False)
def create_unit(
    unit_data: UnitCreate,
    current_user=Depends(require_role(UserRole.ADMIN))
) -> UnitResponse:
    """
    Create a new unit.
    """
    try:
        logger.info(
            "Unit creation requested",
            extra={
                "created_by": current_user['id'],
                "unit_name": unit_data.name,
                "unit_symbol": unit_data.symbol
            }
        )
        response = UnitService.create_unit(unit_data)
        logger.info(
            "Unit created successfully",
            extra={
                "created_by": current_user['id'],
                "unit_id": response.id,
                "unit_name": response.name
            }
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unit creation failed",
            extra={
                "created_by": current_user['id'],
                "unit_name": unit_data.name,
                "unit_symbol": unit_data.symbol
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_data: UnitUpdate,
    current_user=Depends(require_role(UserRole.ADMIN)),
    unit_id: int = Path(..., description="The ID of the unit to update"),
) -> UnitResponse:
    """
    Update an existing unit.
    """
    try:
        logger.info(
            "Unit update requested",
            extra={
                "updated_by": current_user['id'],
                "unit_id": unit_id,
                "unit_data": unit_data.model_dump()
            }
        )
        response = UnitService.update_unit(unit_id, unit_data)
        logger.info(
            "Unit updated successfully",
            extra={
                "updated_by": current_user['id'],
                "unit_id": unit_id
            }
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unit update failed",
            extra={
                "updated_by": current_user['id'],
                "unit_id": unit_id,
                "unit_data": unit_data.model_dump()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_unit(
    unit_id: int = Path(..., description="The ID of the unit to delete"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> None:
    """
    Delete an existing unit.
    """
    try:
        logger.info(
            "Unit deletion requested",
            extra={
                "deleted_by": current_user['id'],
                "unit_id": unit_id
            }
        )

        UnitService.delete_unit(unit_id)
        
        logger.info(
            "Unit deleted successfully",
            extra={
                "deleted_by": current_user['id'],
                "unit_id": unit_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unit deletion failed",
            extra={
                "deleted_by": current_user['id'],
                "unit_id": unit_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return None
