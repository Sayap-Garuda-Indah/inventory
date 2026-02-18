from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class Units(BaseModel):
    # id: int = Field(..., description="The unique identifier for the unit")
    name: str = Field(..., description="The name of the unit")
    symbol: str = Field(..., description="The symbol representing the unit")
    multiplier: int = Field(..., description="The multiplier for the unit")

class UnitCreate(Units):
    pass

class UnitUpdate(Units):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, min_length=1, max_length=16)
    multiplier: Optional[int] = Field(None, ge=0)

class UnitResponse(Units):
    id: int
    
    class Config:
        from_attributes = True

class UnitListResponse(BaseModel):
    units: list[UnitResponse]
    total: int
    page: int
    page_size: int


class UnitDeleteResponse(BaseModel):
    message: str
    warning: Optional[str] = None
    reassigned_items: int
    replacement_unit_name: str
