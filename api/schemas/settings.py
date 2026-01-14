from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SettingsUpdate(BaseModel):
    app_name: Optional[str] = Field(None, title="Application Name", max_length=100)
    items_per_page: Optional[int] = Field(None, title="Items Per Page", ge=1, le=100)
    allow_negative_stock: Optional[bool] = Field(None, title="Allow Negative Stock")
    auto_backup_enabled: Optional[bool] = Field(None, title="Auto Backup Enabled")
    backup_retention_days: Optional[int] = Field(None, title="Backup Retention Days", ge=1, le=365)
    low_stock_threshold: Optional[int] = Field(None, title="Low Stock Threshold", ge=0)
    enable_notifications: Optional[bool] = Field(None, title="Enable Notifications")

class SettingsResponse(BaseModel):
    id: int
    app_name: str
    items_per_page: int
    allow_negative_stock: bool
    auto_backup_enabled: bool
    backup_retention_days: int
    low_stock_threshold: int
    enable_notifications: bool
    updated_at: datetime
    updated_by: Optional[str]

    class Config:
        from_attributes = True