from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)
from src.backend.services.auth_services import (
    authenticate_merchant,
    create_merchant,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    authenticated = authenticate_merchant(
        db,
        request.email,
        request.password,
    )

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return LoginResponse(
        message="Login successful",
    )


@router.post(
    "/signup",
    response_model=SignupResponse,
)
def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    merchant = create_merchant(
        db,
        request.business_name,
        request.email,
        request.password,
    )

    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    return SignupResponse(
        message="Account created successfully",
    )