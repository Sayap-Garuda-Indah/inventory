import datetime
from pydantic import BaseModel, Field
from typing import Optional

class StockLevelResponse(BaseModel):
    id: int = Field(..., description="The unique identifier for the stock level")
    item_id: int = Field(..., description="The ID of the item")
    item_code: Optional[str] = Field(None, description="The item code for display")
    item_name: Optional[str] = Field(None, description="The item name for display")
    location_id: int = Field(..., description="The ID of the location")
    location_name: Optional[str] = Field(None, description="The location name for display")
    qty_on_hand: float = Field(0, description="The quantity on hand for the item at the location")
    updated_at: datetime.datetime = Field(..., description="The timestamp when the stock level was last updated")

class StockLevelListResponse(BaseModel):
    levels: list[StockLevelResponse]
    total: int
    page: int
    page_size: int
