from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime

class IssueItem(BaseModel):
    issue_id: int = Field(..., description="ID of the related issue")
    item_id: int = Field(..., description="ID of the item related to the issue")
    qty: Decimal = Field(..., description="Quantity of the item related to the issue")
    
class IssueItemCreate(BaseModel):
    issue_id: int = Field(..., description="ID of the related issue")
    item_id: int = Field(..., description="ID of the item related to the issue")
    qty: Decimal = Field(..., description="Quantity of the item related to the issue")

class IssueItemUpdate(BaseModel):
    qty: Optional[Decimal] = Field(None, description="Updated quantity of the item related to the issue")

class IssueItemResponse(BaseModel):
    id: int
    issue_id: int
    item_id: int
    qty: Decimal

    item_code: Optional[str] = None
    item_name: Optional[str] = None

    class Config:
        from_attributes = True

class IssueItemListResponse(BaseModel):
    issue_item: list[IssueItemResponse]
    total: int
    page: int
    page_size: int

class IssueItemBulkCreate(BaseModel):
    issue_id: int = Field(..., gt=0, description="ID of the related issue")
    items: list[dict] = Field(..., description="List of items with item_id and qty", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": 1,
                "items": [
                    {"item_id": 101, "qty": "5.0"},
                    {"item_id": 102, "qty": "10.0"}
                ]
            }
        }
