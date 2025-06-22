from pydantic import BaseModel

class ModelSwitchRequest(BaseModel):
    """Request body for switching models via the admin API."""

    model_name: str
    model_type: str
