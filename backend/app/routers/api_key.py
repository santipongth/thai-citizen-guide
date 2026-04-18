from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.models.user import User, UserAPIKey
from app.utils import generate_uuid

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    created_at: str

class CreateAPIKeyRequest(BaseModel):
    name: str

class UpdateAPIKeyRequest(BaseModel):
    name: str

@router.get("/", summary="List API keys for the current user")
async def list_api_keys(user: User = Depends(get_current_user)) -> list[APIKeyResponse]:
    result = await UserAPIKey.filter(user_id=user.id).order_by("-created_at").all()
    return [APIKeyResponse(id=str(key.id), name=key.name, key=key.key, created_at=str(key.created_at)) for key in result]

@router.post("/", summary="Create a new API key")
async def create_api_key(body: CreateAPIKeyRequest, user: User = Depends(get_current_user)) -> APIKeyResponse:
    new_key = await UserAPIKey.create(user_id=user.id, name=body.name, key=generate_uuid())
    return APIKeyResponse(id=str(new_key.id), name=new_key.name, key=new_key.key, created_at=str(new_key.created_at))

@router.patch("/{key_id}", summary="Rename an API key")
async def update_api_key(key_id: str, body: UpdateAPIKeyRequest, user: User = Depends(get_current_user)) -> APIKeyResponse:
    key = await UserAPIKey.filter(id=key_id, user_id=user.id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    key.name = body.name
    await key.save()
    return APIKeyResponse(id=str(key.id), name=key.name, key=key.key, created_at=str(key.created_at))

@router.delete("/{key_id}", summary="Delete an API key")
async def delete_api_key(key_id: str, user: User = Depends(get_current_user)) -> dict:
    key = await UserAPIKey.filter(id=key_id, user_id=user.id).first()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await key.delete()
    return {"detail": "API key deleted"}