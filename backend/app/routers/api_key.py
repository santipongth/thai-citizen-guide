from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.models.user import User, UserAPIKey

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

class APIKeyResponse(BaseModel):
    id: str
    key: str
    created_at: str

@router.get("/", summary="List API keys for the current user")
async def list_api_keys(user: User = Depends(get_current_user)) -> list[APIKeyResponse]:
    result = await UserAPIKey.filter(user_id=user.id).order_by("-created_at").all()
    return [APIKeyResponse(id=key.id, key=key.key, created_at=key.created_at) for key in result]

@router.post("/", summary="Create a new API key")
async def create_api_key(user: User = Depends(get_current_user)) -> APIKeyResponse:
    new_key = await UserAPIKey.create(user_id=user.id)
    return APIKeyResponse(id=new_key.id, key=new_key.key, created_at=new_key.created_at)

@router.delete("/{key_id}", summary="Delete an API key")
async def delete_api_key(key_id: str, user: User = Depends(get_current_user)) -> dict:
    key = await UserAPIKey.filter(id=key_id, user_id=user.id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await key.delete()
    return {"detail": "API key deleted"}