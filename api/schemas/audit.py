from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AuditSessionCreate(BaseModel):
    location_id: int = Field(..., description="ID of the location where the session is created")
    note: Optional[str] = Field(None, max_length=255, description="Optional note for the session")

class AuditSessionResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the audit session")
    location_id: int = Field(..., description="ID of the location associated with the session")
    location_name: Optional[str] = Field(None, description="Name of the location associated with the session")
    location_code: Optional[str] = Field(None, description="Code of the location associated with the session")
    status: str = Field(..., description="Status of the audit session")
    started_at: datetime = Field(..., description="Timestamp when the session was started")
    started_by: int = Field(..., description="User ID of the person who started the session")
    started_by_name: Optional[str] = Field(None, description="Name of the user who started the session")
    closed_at: Optional[datetime] = Field(None, description="Timestamp when the session was closed")
    closed_by: Optional[int] = Field(None, description="User ID of the person who closed the session")
    closed_by_name: Optional[str] = Field(None, description="Name of the user who closed the session")
    note: Optional[str] = Field(None, description="Optional note for the session")
    scanned_count: int = Field(..., description="Number of items scanned in the session")
    expected_count: int = Field(..., description="Expected number of items for the session")
    missing_count: int = Field(..., description="Number of missing items in the session")
    unexpected_count: int = Field(..., description="Number of unexpected items in the session")
    unknown_count: int = Field(..., description="Number of unknown items in the session")

class AuditSessionListResponse(BaseModel):
    sessions: List[AuditSessionResponse]
    total: int
    page: int
    page_size: int

class AuditScanCreate(BaseModel):
    scanned_code: str = Field(..., max_length=100, description="The code of the item being scanned")
    note: Optional[str] = Field(None, max_length=255, description="Optional note for the scan")

class AuditScanResponse(BaseModel):
    id: int = Field(..., description="Unique identifier of the audit scan")
    session_id: int = Field(..., description="ID of the audit session")
    scanned_code: Optional[str] = Field(None, description="The code of the item that was scanned")
    scanned_at: datetime = Field(..., description="Timestamp when the item was scanned")
    scanned_by: int = Field(..., description="User ID of the person who performed the scan")
    item_id: Optional[int] = Field(None, description="ID of the item if it exists in inventory")
    location_id: int = Field(..., description="ID of the location where the scan took place")
    result: str = Field(..., description="Result of the scan (e.g., 'FOUND', 'MISSING', 'UNEXPECTED', 'UNKNOWN')")
    note: Optional[str] = Field(None, description="Optional note for the scan")

class AuditScanListResponse(BaseModel):
    scans: List[AuditScanResponse]
    total: int
    page: int
    page_size: int

class AuditItemSummary(BaseModel):
    item_id: int
    item_code: str
    name: str
    active: bool
    qty_on_hand: Optional[float] = None
    note: Optional[str] = None

class AuditItemNote(BaseModel):
    item_id: int
    note: Optional[str] = None

class AuditScanNote(BaseModel):
    scan_id: int
    note: Optional[str] = None

class AuditSessionNotesUpdate(BaseModel):
    missing_notes: List[AuditItemNote] = []
    unexpected_notes: List[AuditItemNote] = []
    unknown_notes: List[AuditScanNote] = []

class AuditReconciliationResponse(BaseModel):
    session_id: int = Field(..., description="ID of the audit session")
    expected_count: int = Field(..., description="Expected number of items for the session")
    scanned_count: int = Field(..., description="Number of items scanned in the session")
    found_count: int = Field(..., description="Number of items found during the audit")
    missing_count: int = Field(..., description="Number of missing items in the session")
    unexpected_count: int = Field(..., description="Number of unexpected items in the session")
    unknown_count: int = Field(..., description="Number of unknown items in the session")
    found: List[AuditItemSummary] = Field(..., description="List of found items")
    missing: List[AuditItemSummary] = Field(..., description="List of missing items")
    unexpected: List[AuditItemSummary] = Field(..., description="List of unexpected items")
    # unknown: List[AuditItemSummary] = Field(..., description="List of unknown items")
    
