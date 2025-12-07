"""
Authentication endpoints for user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new user account. A verification email will be sent to the provided email address.",
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters, alphanumeric and underscores)
    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **display_name**: Optional display name
    
    After registration, a verification email is sent. User must verify email before logging in.
    """
    auth_service = AuthService(db)
    return await auth_service.register(user_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access and refresh tokens.",
)
async def login(
    login_data: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """
    Login with email and password.
    
    Returns JWT access token and refresh token.
    Email must be verified before login is allowed.
    """
    auth_service = AuthService(db)
    return await auth_service.login(login_data.email, login_data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: DbSession,
) -> TokenResponse:
    """
    Get new access and refresh tokens using a valid refresh token.
    
    The old refresh token will be revoked.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(token_data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Revoke the refresh token to logout user.",
)
async def logout(
    token_data: RefreshTokenRequest,
    db: DbSession,
) -> MessageResponse:
    """
    Logout by revoking the refresh token.
    
    The access token will remain valid until it expires.
    """
    auth_service = AuthService(db)
    await auth_service.logout(token_data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post(
    "/verify-email",
    response_model=UserResponse,
    summary="Verify email address",
    description="Verify user's email address using the token sent via email.",
)
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: DbSession,
) -> UserResponse:
    """
    Verify email address using the verification token.
    
    The token is sent to the user's email during registration.
    Token expires after 24 hours.
    """
    auth_service = AuthService(db)
    return await auth_service.verify_email(verify_data.token)


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
    description="Resend the email verification link.",
)
async def resend_verification(
    resend_data: ResendVerificationRequest,
    db: DbSession,
) -> MessageResponse:
    """
    Resend the verification email.
    
    Use this if the original verification link expired or was lost.
    """
    auth_service = AuthService(db)
    await auth_service.resend_verification_email(resend_data.email)
    return MessageResponse(message="Verification email sent. Please check your inbox.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Send a password reset link to the user's email.",
)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    """
    Request a password reset email.
    
    If the email exists, a reset link will be sent.
    For security, this endpoint always returns success even if email doesn't exist.
    Reset link expires after 1 hour.
    """
    auth_service = AuthService(db)
    await auth_service.forgot_password(forgot_data.email)
    return MessageResponse(
        message="If the email exists, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset user's password using the token from the reset email.",
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: DbSession,
) -> MessageResponse:
    """
    Reset password using the reset token.
    
    All existing sessions will be invalidated after password reset.
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(reset_data.token, reset_data.new_password)
    return MessageResponse(message="Password reset successfully. Please login with your new password.")
