from pydantic import BaseModel, Field
from typing import Literal

class ModelSwitchRequest(BaseModel):
    """Request body for switching the model."""
    model_name: str
    model_type: Literal['GENERATION', 'EMBEDDING'] = Field(..., description="Type of the model to switch")
