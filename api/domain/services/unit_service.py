from typing import Optional, List
from fastapi import HTTPException, status
from db.repositories.units_repo import UnitsRepository
from schemas.units import UnitCreate, UnitUpdate, UnitResponse, UnitListResponse, UnitDeleteResponse
from core.logging import get_logger

logger = get_logger(__name__)

class UnitService:

    @staticmethod
    def get_all_units(
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None) -> UnitListResponse:
        """Retrieve a paginated list of units, optionally filtered by a search term."""
        try:
            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="page must be a positive integer"
                )
            
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="page_size must be between 1 and 100"
                )
            
            offset = (page - 1) * page_size

            units_data = UnitsRepository.get_all(
                limit=page_size,
                offset=offset,
                search=search
            )

            total = UnitsRepository.count(search=search)

            units = [UnitResponse(**unit) for unit in units_data]

            response = UnitListResponse(
                units=units,
                total=total,
                page=page,
                page_size=page_size
            )

            return response
        except Exception as e:
            logger.error(
                "Failed to retrieve units",
                extra={"error": str(e), "search": search}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve units: {str(e)}"
            )
        
    @staticmethod
    def get_unit_by_id(unit_id: int) -> UnitResponse:
        """Get unit by ID."""
        try:
            if not isinstance(unit_id, int) or unit_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="unit_id must be a positive integer"
                )
            
            unit_data = UnitsRepository.get_by_id(unit_id)
            if not unit_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with id {unit_id} not found"
                )
            
            return UnitResponse(**unit_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve unit by id",
                extra={"error": str(e), "unit_id": unit_id}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve unit by id {unit_id}: {str(e)}"
            )
        
    @staticmethod
    def create_unit(unit_data: UnitCreate) -> UnitResponse:
        """Create a new unit with validation"""
        try:
            if UnitsRepository.exists_by_name(unit_data.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Unit with name '{unit_data.name}' already exists."
                )
            
            # check if unit with same symbol already exists
            if UnitsRepository.exists_by_symbol(unit_data.symbol):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Unit with symbol '{unit_data.symbol}' already exists."
                )
            
            # Validate multiplier
            if unit_data.multiplier < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multiplier must be a non-negative integer."
                )
            
            created_unit = UnitsRepository.create(unit_data)
            logger.info(
                "Unit created successfully",
                extra={"unit_id": created_unit["id"], "unit_name": created_unit["name"]}
            )
            return UnitResponse(**created_unit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to create unit",
                extra={
                    "error": str(e),
                    "unit_name": unit_data.name,
                    "unit_symbol": unit_data.symbol
                }
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create unit: {str(e)}"
            )
        
    @staticmethod
    def update_unit(unit_id: int, unit_data: UnitUpdate) -> UnitResponse:
        """Update an existing unit with validation"""
        try:
            if not isinstance(unit_id, int) or unit_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="unit_id must be a positive integer"
                )
            
            existing_unit = UnitsRepository.get_by_id(unit_id)
            if not existing_unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with id {unit_id} not found"
                )
            
            # Check for name conflict
            if unit_data.name and unit_data.name != existing_unit['name']:
                if UnitsRepository.exists_by_name(unit_data.name, exclude_id=unit_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Unit with name '{unit_data.name}' already exists."
                    )
                
            # Check for symbol conflict
            if unit_data.symbol and unit_data.symbol != existing_unit['symbol']:
                if UnitsRepository.exists_by_symbol(unit_data.symbol, exclude_id=unit_id):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Unit with symbol '{unit_data.symbol}' already exists."    
                )

            # Validate multiplier if being updated
            if unit_data.multiplier is not None and unit_data.multiplier < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multiplier must be a non-negative integer."
                )
            
            updated_unit = UnitsRepository.update(unit_id, unit_data)
            if not updated_unit:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update unit."
                )
            
            logger.info(
                "Unit updated successfully",
                extra={
                    "unit_id": unit_id,
                    "updated_fields": {
                        k: v for k, v in unit_data.dict(exclude_unset=True).items() if v is not None
                    }
                }
            )

            return UnitResponse(**updated_unit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to update unit",
                extra={"error": str(e), "unit_id": unit_id}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update unit with id {unit_id}: {str(e)}"
            )

    
    @staticmethod
    def delete_unit(unit_id: int) -> UnitDeleteResponse:
        """Soft delete unit and reassign related items to fallback unit."""
        try:
            if not isinstance(unit_id, int) or unit_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="unit_id must be a positive integer"
                )
            
            existing_unit = UnitsRepository.get_by_id(unit_id)
            if not existing_unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with id {unit_id} not found"
                )

            if existing_unit["name"] == UnitsRepository.FALLBACK_UNIT_NAME:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Fallback unit '-' cannot be deleted."
                )

            result = UnitsRepository.soft_delete_and_reassign(unit_id)

            warning = None
            if result["reassigned_items"] > 0:
                warning = (
                    f"{result['reassigned_items']} item(s) were linked to this unit "
                    f"and have been reassigned to '{result['replacement_unit_name']}'."
                )

            logger.info(
                "Unit soft-deleted successfully",
                extra={
                    "unit_id": unit_id,
                    "unit_name": result["deleted_unit_name"],
                    "unit_symbol": result["deleted_unit_symbol"],
                    "reassigned_items": result["reassigned_items"],
                    "replacement_unit_id": result["replacement_unit_id"],
                }
            )

            return UnitDeleteResponse(
                message=(
                    f"Unit '{result['deleted_unit_name']}' ({result['deleted_unit_symbol']}) "
                    "soft-deleted successfully."
                ),
                warning=warning,
                reassigned_items=result["reassigned_items"],
                replacement_unit_name=result["replacement_unit_name"],
            )
        except HTTPException: 
            raise
        except Exception as e:
            logger.error(
                "Failed to delete unit",
                extra={"error": str(e), "unit_id": unit_id}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete unit with id {unit_id}: {str(e)}"
            )
        
    @staticmethod
    def get_unit_by_name(name: str) -> UnitResponse:
        """Get unit by name."""
        try:
            if not name or not name.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="name must be a non-empty string"
                )
            
            unit_data = UnitsRepository.get_by_name(name.strip())
            if not unit_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with name '{name}' not found"
                )
            
            return UnitResponse(**unit_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve unit by name",
                extra={"error": str(e), "unit_name": name}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve unit by name '{name}': {str(e)}"
            )
        
    @staticmethod
    def get_unit_by_symbol(symbol: str) -> UnitResponse:
        """Get unit by symbol."""
        try:
            if not symbol or not symbol.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="symbol must be a non-empty string"
                )
            
            unit_data = UnitsRepository.get_by_symbol(symbol.strip())
            if not unit_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unit with symbol '{symbol}' not found"
                )
            
            return UnitResponse(**unit_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve unit by symbol",
                extra={"error": str(e), "unit_symbol": symbol}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve unit by symbol '{symbol}': {str(e)}"
            )
        
    @staticmethod
    def validate_unit_exists(unit_id: int) -> bool:
        try:
            unit_data = UnitsRepository.get_by_id(unit_id)

            if unit_data:
                return True
        except Exception as e:
            logger.error(
                "Failed to validate unit existence",
                extra={"error": str(e), "unit_id": unit_id}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate unit existence for id {unit_id}: {str(e)}"
            )
        
        return False
    
    @staticmethod
    def get_units_for_dropdown() -> List[dict]:
        """Get simplified unit list for dropdown/select component"""
        try:
            units_data = UnitsRepository.get_all(limit=100, offset=0)
            data = []
            for unit in units_data:
                data.append({
                    "id": unit["id"],
                    "name": unit["name"],
                    "symbol": unit["symbol"],
                    "display": f"{unit['name']} ({unit['symbol']})"
                })
            return data
        except Exception as e:
            logger.error(
                "Failed to retrieve units for dropdown",
                extra={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve units for dropdown: {str(e)}"
            )
