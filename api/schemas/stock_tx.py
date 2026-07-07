import datetime
from pydantic import BaseModel, Field
from typing import Optional
from schemas.items import ItemCondition, ItemStatus

class StockTxCreate(BaseModel):
    item_id: int = Field(..., description="Identifier for the item")
    location_id: int = Field(..., description="Identifier for the location")
    tx_type: str = Field(..., description="Type of transaction (IN, OUT, ADJ, XFER)")
    qty: float = Field(..., description="Quantity of items in the transaction")
    user_id: Optional[int] = Field(None, description="Owner user ID after transaction")
    new_status: Optional[ItemStatus] = Field(None, description="Optional item status after transaction")
    new_condition: Optional[ItemCondition] = Field(None, description="Optional item condition after transaction")
    ref: Optional[str] = Field(None, description="Reference for the transaction")
    note: Optional[str] = Field(None, description="Additional notes about the transaction")

class StockTxUpdate(BaseModel):
    item_id: Optional[int] = Field(None, description="Identifier for the item")
    location_id: Optional[int] = Field(None, description="Identifier for the location")
    tx_type: Optional[str] = Field(None, description="Type of transaction (IN, OUT, ADJ, XFER)")
    qty: Optional[float] = Field(None, description="Quantity of items in the transaction")
    user_id: Optional[int] = Field(None, description="Owner user ID after transaction")
    new_status: Optional[ItemStatus] = Field(None, description="Optional item status after transaction")
    new_condition: Optional[ItemCondition] = Field(None, description="Optional item condition after transaction")
    ref: Optional[str] = Field(None, description="Reference for the transaction")
    note: Optional[str] = Field(None, description="Additional notes about the transaction")

class StockTxResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the transaction")
    item_id: int = Field(..., description="Identifier for the item")
    item_code: Optional[str] = Field(None, description="Item code for display")
    item_name: Optional[str] = Field(None, description="Item name for display")
    location_id: int = Field(..., description="Identifier for the location")
    location_name: Optional[str] = Field(None, description="Location name for display")
    tx_type: str = Field(..., description="Type of transaction (IN, OUT, ADJ, XFER)")
    qty: float = Field(..., description="Quantity of items in the transaction")
    ref: Optional[str] = Field(None, description="Reference for the transaction")
    note: Optional[str] = Field(None, description="Additional notes about the transaction")
    tx_at: datetime.datetime = Field(..., description="Timestamp of the transaction")
    user_id: int = Field(..., description="Identifier for the owner user after transaction")
    owner_name: Optional[str] = Field(None, description="Owner name derived from user_id")
    qty_on_hand: Optional[float] = Field(None, description="Current quantity on hand after transaction")
    item_status_before: Optional[ItemStatus] = Field(None, description="Item status before transaction")
    item_status_after: Optional[ItemStatus] = Field(None, description="Item status after transaction")
    item_condition_before: Optional[ItemCondition] = Field(None, description="Item condition before transaction")
    item_condition_after: Optional[ItemCondition] = Field(None, description="Item condition after transaction")

class StockTxListResponse(BaseModel):
    txs: list[StockTxResponse]
    total: int
    page: int
    page_size: int
