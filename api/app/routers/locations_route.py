from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Path
from app.dependencies import get_current_user, require_role
from domain.services.location_service import LocationService
from db.repositories.locations_repo import LocationsRepository
from schemas.locations import Location, LocationCreate, LocationUpdate
from schemas.users import UserRole
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/", response_model=list[Location])
def list_locations(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(100, ge=1, le=200, description="Number of locations per page"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    active_only: int = Query(1, description="Filter to only active locations if set to 1"),
    current_user=Depends(get_current_user)
) -> list[Location]:
    try:
        offset = (page - 1) * page_size
        data = LocationsRepository.get_all(
            active_only=active_only == 1,
            limit=page_size,
            offset=offset,
            search=search
        )
        return data
    except Exception as e:
        logger.error("Failed to list locations", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{location_id}", response_model=Location)
def get_location(
    location_id: int,
    current_user=Depends(get_current_user)
) -> Location:
    try:
        return LocationService.get_location_by_id(location_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve location", extra={"error": str(e), "location_id": location_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/", response_model=Location, status_code=status.HTTP_201_CREATED)
def create_location(
    location_data: LocationCreate,
    current_user=Depends(require_role(UserRole.ADMIN))
) -> Location:
    try:
        logger.info(
            "Location creation requested",
            extra={
                "created_by": current_user.get("id"),
                "location_code": location_data.code
            }
        )
        return LocationService.create_location(location_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create location", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: int = Path(..., gt=0, description="The ID of the location to update"),
    location_data: LocationUpdate = ...,
    current_user=Depends(require_role(UserRole.ADMIN))
) -> Location:
    try:
        logger.info(
            "Location update requested",
            extra={
                "updated_by": current_user.get("id"),
                "location_id": location_id
            }
        )
        return LocationService.update_location(location_id, location_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update location", extra={"error": str(e), "location_id": location_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int = Path(..., gt=0, description="The ID of the location to delete"),
    current_user=Depends(require_role(UserRole.ADMIN))
) -> None:
    try:
        logger.info(
            "Location deletion requested",
            extra={
                "deleted_by": current_user.get("id"),
                "location_id": location_id
            }
        )
        LocationService.delete_location(location_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete location", extra={"error": str(e), "location_id": location_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
