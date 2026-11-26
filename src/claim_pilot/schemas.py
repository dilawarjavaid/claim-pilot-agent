from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LossType(str, Enum):
    AUTO_COLLISION = "auto_collision"
    AUTO_THEFT = "auto_theft"
    WEATHER = "weather_damage"
    WATER = "water_damage"
    FIRE = "fire"
    HOME_THEFT = "home_theft"
    LIABILITY = "liability"
    OTHER = "other"


class ClaimSubmission(BaseModel):
    """Raw claim as the customer submits it."""
    claim_id: str
    policy_number: str
    submitted_on: date
    description: str
    photo_path: Optional[str] = None


class ExtractedClaim(BaseModel):
    """Structured output produced by the intake agent."""
    incident_date: Optional[date] = Field(None, description="Date of loss; null if not stated")
    loss_type: LossType
    location: Optional[str] = Field(None, description="Where it happened; null if not stated")
    damaged_items: list[str] = Field(default_factory=list)
    estimated_amount: Optional[float] = Field(None, description="Amount in CAD if the customer gave one")
    injuries: bool = False
    police_report: bool = False
    summary: str = Field(description="One neutral sentence describing the loss")
    missing_info: list[str] = Field(
        default_factory=list,
        description="Facts an adjuster needs that the customer did not provide",
    )