"""
Authentication Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for token response after login."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""
    
    token: str


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""
    
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset request."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class MessageResponse(BaseModel):
    """Schema for generic message response."""
    
    message: str
    success: bool = True
