from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.dependencies import get_current_user
from db.repositories.locations_repo import LocationsRepository
from schemas.locations import Location
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
        data = LocationsRepository.get_by_id(location_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve location", extra={"error": str(e), "location_id": location_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
