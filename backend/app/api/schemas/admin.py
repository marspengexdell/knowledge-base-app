from pydantic import BaseModel

class ModelSwitchRequest(BaseModel):
    """Request body for switching the generation model."""

    model_name: str
