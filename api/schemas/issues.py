import datetime
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Issue(BaseModel):
    id: int = Field(..., description="Unique identifier for the issue")
    code: str = Field(..., description="Code representing the issue type")
    status: str = Field(..., description="Current status of the issue")
    requested_by: Optional[int] = Field(None, description="ID of the user who requested the issue")
    approved_by: Optional[int] = Field(None, description="ID of the user who approved the issue")
    issued_at: Optional[datetime] = Field(None, description="Timestamp when the issue was issued")
    note: Optional[str] = Field(None, description="Additional notes regarding the issue")

class IssueCreate(BaseModel):
    code: str = Field(..., description="Code representing the issue type")
    status: str = Field(..., description="Current status of the issue")
    requested_by: Optional[int] = Field(None, description="ID of the user who requested the issue")
    approved_by: Optional[int] = Field(None, description="ID of the user who approved the issue")
    note: Optional[str] = Field(None, description="Additional notes regarding the issue")

class IssueUpdate(BaseModel):
    code: Optional[str] = Field(None, description="Code representing the issue type")
    status: Optional[str] = Field(None, description="Current status of the issue")
    requested_by: Optional[int] = Field(None, description="ID of the user who requested the issue")
    approved_by: Optional[int] = Field(None, description="ID of the user who approved the issue")
    issued_at: Optional[datetime] = Field(None, description="Timestamp when the issue was issued")
    note: Optional[str] = Field(None, description="Additional notes regarding the issue")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the issue was last updated")

class IssueResponse(BaseModel):
    id: int
    code: str
    status: str
    requested_by: Optional[int] = None
    approved_by: Optional[int] = None
    issued_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class IssueListResponse(BaseModel):
    total: int = Field(..., description="Total number of issues")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of issues per page")
    issues: list[IssueResponse] = Field(..., description="List of issues on the current page")