import datetime
from pydantic import BaseModel, Field
from typing import Optional

class StockTxCreate(BaseModel):
    item_id: int = Field(..., description="Identifier for the item")
    location_id: int = Field(..., description="Identifier for the location")
    tx_type: str = Field(..., description="Type of transaction (IN, OUT, ADJ, XFER)")
    qty: float = Field(..., description="Quantity of items in the transaction")
    ref: Optional[str] = Field(None, description="Reference for the transaction")
    note: Optional[str] = Field(None, description="Additional notes about the transaction")

class StockTxUpdate(BaseModel):
    item_id: Optional[int] = Field(None, description="Identifier for the item")
    location_id: Optional[int] = Field(None, description="Identifier for the location")
    tx_type: Optional[str] = Field(None, description="Type of transaction (IN, OUT, ADJ, XFER)")
    qty: Optional[float] = Field(None, description="Quantity of items in the transaction")
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
    user_id: int = Field(..., description="Identifier for the user who made the transaction")
    qty_on_hand: Optional[float] = Field(None, description="Current quantity on hand after transaction")

class StockTxListResponse(BaseModel):
    txs: list[StockTxResponse]
    total: int
    page: int
    page_size: int
