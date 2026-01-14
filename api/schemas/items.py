from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

class Item(BaseModel):
    id: int = Field(..., description="The unique identifier for the item in the database")
    item_code: str = Field(..., description="The unique indentifier for the item as an company assets or opex")
    serial_number: str = Field(..., description="The unique indentifier of the item physically")
    name: str = Field(..., description="The name of the item")
    category_id: int = Field(..., description="The category ID the item belongs to")
    unit_id: int = Field(..., description="The unit ID for the item")
    owner_user_id: int = Field(..., description="The user ID of the item's owner")
    min_stock: float = Field(0.0, description="The minimum stock level for the item")
    description: str = Field(..., description="Description of the item")
    image_url: Optional[str] = Field(None, description="The URL of the item's image")
    active: bool = Field(True, description="Indicates if the item is active")

class ItemCreate(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=20, description="The stock keeping unit for the item")
    serial_number: Optional[str] = Field(None, min_length=1, max_length=40, description="The unique indentifier of the item physically")
    name: str = Field(..., min_length=1, max_length=255, description="The name of the item")
    category_id: int = Field(..., description="The category ID the item belongs to")
    unit_id: int = Field(..., description="The unit ID for the item")
    owner_user_id: Optional[int] = Field(..., description="The user ID of the item's owner")
    min_stock: Optional[float] = Field(0.0, ge=0.0, description="The minimum stock level for the item")
    description: Optional[str] = Field(None, description="Description of the item")
    image_url: Optional[str] = Field(None, description="The URL of the item's image")
    active: Optional[bool] = Field(True, description="Indicates if the item is active")

    @field_validator('item_code')
    @classmethod
    def validate_item_code(cls, v):
        if not v.strip():
            raise ValueError('Item code must not be empty')
        return v.strip().upper()
    
class ItemUpdate(BaseModel):
    item_code: Optional[str] = Field(None, min_length=1, max_length=20, description="The stock keeping unit for the item")
    serial_number: Optional[str] = Field(None, min_length=1, max_length=40, description="The unique indentifier of the item physically")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="The name of the item")
    category_id: Optional[int] = None
    unit_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    min_stock: Optional[float] = Field(None, ge=0.0, description="The minimum stock level for the item")
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, description="The URL of the item's image")
    active: Optional[bool] = None

    @field_validator('item_code')
    @classmethod
    def validate_item_code(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Item code must not be empty if provided')
        if v is not None:
            return v.strip().upper()
        return v
    
class ItemResponse(BaseModel):
    id: int
    item_code: str
    serial_number: Optional[str] = None
    name: str
    category_id: Optional[int] = None
    unit_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    min_stock: float = 0.0
    description: Optional[str] = None
    image_url: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    page_size: int
