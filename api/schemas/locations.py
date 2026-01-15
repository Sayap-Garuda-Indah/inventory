from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    id: int = Field(..., description="The unique identifier for the location")
    name: str = Field(..., description="The name of the location")
    code: str = Field(..., description="The code representing the location")
    active: int = Field(True, description="Indicates if the location is active")

class LocationCreate(BaseModel):
    name: str = Field(..., description="The name of the location")
    code: str = Field(..., description="The code representing the location")
    active: Optional[int] = Field(1, description="Indicates if the location is active")

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The updated name of the location")
    code: Optional[str] = Field(None, description="The updated code of the location")
    active: Optional[int] = Field(None, description="Indicates if the location is active")
