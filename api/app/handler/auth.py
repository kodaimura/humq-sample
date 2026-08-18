from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.config import config
from app.core.database import get_db
from app.core.jwt import verify_refresh_token
from app.core.response import ApiResponse
from app.handler.dto.auth import (
    AccountResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
)
from app.usecase.auth.forgot_password import ForgotPasswordInput, ForgotPasswordUsecase
from app.usecase.auth.login import LoginInput, LoginUsecase
from app.usecase.auth.refresh import RefreshInput, RefreshUsecase
from app.usecase.auth.reset_password import ResetPasswordInput, ResetPasswordUsecase
from app.usecase.auth.signup import SignupInput, SignupUsecase
from app.usecase.auth.verify_reset_password_token import (
    VerifyResetPasswordTokenInput,
    VerifyResetPasswordTokenUsecase,
)

router = APIRouter()


@router.post("/auth/signup", response_model=SignupResponse)
def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)):
    usecase = SignupUsecase(db)
    account = usecase.execute(
        SignupInput(
            login_id=request.login_id,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )
    )
    data = SignupResponse(account=AccountResponse.model_validate(account))
    return ApiResponse.created(data=data, response=response)


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    usecase = LoginUsecase(db)
    result = usecase.execute(
        LoginInput(
            login_id=request.login_id,
            password=request.password,
            remember_me=request.remember_me,
        )
    )

    refresh_token_max_age = (
        config.REFRESH_TOKEN_REMEMBER_ME_EXPIRES_SECONDS
        if request.remember_me
        else config.REFRESH_TOKEN_EXPIRES_SECONDS
    )

    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        secure=(config.APP_ENV == "production"),
        samesite="lax",
        path="/",
        max_age=refresh_token_max_age,
    )

    data = LoginResponse(
        account=AccountResponse.model_validate(result.account),
        access_token=result.access_token,
    )
    return ApiResponse.ok(data=data, response=response)


@router.post("/auth/refresh", response_model=RefreshResponse)
def refresh_token(
    response: Response,
    payload: dict = Depends(verify_refresh_token),
    db: Session = Depends(get_db),
):
    usecase = RefreshUsecase(db)
    result = usecase.execute(
        RefreshInput(
            sub=payload.get("sub"),
            token_version=payload.get("token_version"),
        )
    )
    data = RefreshResponse(access_token=result.access_token)
    return ApiResponse.ok(data=data, response=response)


@router.post("/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=(config.APP_ENV == "production"),
        samesite="lax",
        path="/",
    )

    return ApiResponse.no_content(response=response)


@router.post("/auth/forgot-password", status_code=204)
def forgot_password(
    request: ForgotPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    usecase = ForgotPasswordUsecase(db)
    usecase.execute(ForgotPasswordInput(email=request.email))
    return ApiResponse.no_content(response=response)


@router.get("/auth/reset-password/verify", status_code=204)
def verify_reset_password_token(
    response: Response,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    usecase = VerifyResetPasswordTokenUsecase(db)
    usecase.execute(VerifyResetPasswordTokenInput(token=token))
    return ApiResponse.no_content(response=response)


@router.post("/auth/reset-password", status_code=204)
def reset_password(
    request: ResetPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    usecase = ResetPasswordUsecase(db)
    usecase.execute(
        ResetPasswordInput(
            token=request.token,
            new_password=request.new_password,
        )
    )
    return ApiResponse.no_content(response=response)
