from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import rate_limit_me
from app.models import User
from app.schemas import UserResponse
from app.services.auth import get_current_user
from app.services.cloudinary_service import upload_avatar


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(rate_limit_me)):
    return current_user


@router.patch("/avatar", response_model=UserResponse, status_code=201)
def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    avatar_url = upload_avatar(file, current_user.id)
    current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user
