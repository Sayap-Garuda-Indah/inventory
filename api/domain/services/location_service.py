from fastapi import HTTPException, status
from core.logging import get_logger
from db.repositories.locations_repo import LocationsRepository
from schemas.locations import Location, LocationCreate, LocationUpdate

logger = get_logger(__name__)


class LocationService:
    @staticmethod
    def get_location_by_id(location_id: int) -> Location:
        try:
            if not isinstance(location_id, int) or location_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid location ID")

            data = LocationsRepository.get_by_id(location_id)
            if not data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

            return Location(**data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to retrieve location", extra={"error": str(e), "location_id": location_id})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def create_location(location_data: LocationCreate) -> Location:
        try:
            if LocationsRepository.exists_by_name(location_data.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Location with name '{location_data.name}' already exists"
                )

            if LocationsRepository.exists_by_code(location_data.code):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Location with code '{location_data.code}' already exists"
                )

            created = LocationsRepository.create(location_data)
            return Location(**created)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create location", extra={"error": str(e)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def update_location(location_id: int, location_data: LocationUpdate) -> Location:
        try:
            if not isinstance(location_id, int) or location_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid location ID")

            existing = LocationsRepository.get_by_id(location_id)
            if not existing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

            if location_data.name and location_data.name != existing["name"]:
                if LocationsRepository.exists_by_name(location_data.name, exclude_id=location_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Location with name '{location_data.name}' already exists"
                    )

            if location_data.code and location_data.code != existing["code"]:
                if LocationsRepository.exists_by_code(location_data.code, exclude_id=location_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Location with code '{location_data.code}' already exists"
                    )

            updated = LocationsRepository.update(location_id, location_data)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update location"
                )

            return Location(**updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update location", extra={"error": str(e), "location_id": location_id})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    @staticmethod
    def delete_location(location_id: int) -> None:
        try:
            if not isinstance(location_id, int) or location_id <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid location ID")

            existing = LocationsRepository.get_by_id(location_id)
            if not existing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

            success = LocationsRepository.delete(location_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete location"
                )
        except HTTPException:
            raise
        except Exception as e:
            if "foreign key" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Location is in use and cannot be deleted"
                )
            logger.error("Failed to delete location", extra={"error": str(e), "location_id": location_id})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
