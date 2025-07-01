from fastapi import APIRouter, HTTPException
from typing import List
from services.model_management import model_manager

router = APIRouter()

@router.get("/list", response_model=List)
async def list_models():
    """
    Returns a list of all available models discovered by the ModelManager.
    """
    try:
        models = model_manager.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/load/{model_name}")
async def load_model(model_name: str):
    """
    Triggers the loading of a specific model by the inference service.
    """
    try:
        success = await model_manager.load_model(model_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found or failed to load.")
        return {"message": f"Model '{model_name}' is being loaded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
