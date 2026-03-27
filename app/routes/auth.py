from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import EmailRequest, MessageResponse, Token, UserCreate, UserLogin, UserResponse
from app.services.auth import create_access_token, get_password_hash, verify_password
from app.services.email import send_verification_email, verify_email_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this email already exists.",
        )

    existing_username = db.query(User).filter(User.username == body.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this username already exists.",
        )

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=get_password_hash(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    send_verification_email(background_tasks, user.email)
    return user


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = None
    if body.email:
        user = db.query(User).filter(User.email == body.email).first()
    elif body.username:
        user = db.query(User).filter(User.username == body.username).first()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    access_token = create_access_token(user.email)
    return Token(access_token=access_token)


@router.get("/verify-email/{token}", response_model=MessageResponse)
def verify_registered_email(token: str, db: Session = Depends(get_db)):
    try:
        email = verify_email_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.verified_email:
        return MessageResponse(message="Email is already verified.")

    user.verified_email = True
    db.commit()
    return MessageResponse(message="Email successfully verified.")


@router.post("/request-email", response_model=MessageResponse)
def request_email_verification(
    body: EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.verified_email:
        return MessageResponse(message="Email is already verified.")

    send_verification_email(background_tasks, user.email)
    return MessageResponse(message="Verification email sent.")
