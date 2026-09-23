"""Skema Pydantic CTW."""
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field


class RegionRead(BaseModel):
    code: str
    name: str
    level: str
    parent_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    project_id: int
    feedback_type: Literal["audit", "inspeksi", "publik"]
    reporter_name: str = "Anonim"
    reporter_contact: str = ""
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10)
