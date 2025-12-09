"""
Email service for sending emails using Resend API.
"""

import logging

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using Resend API."""
    
    def __init__(self):
        if not settings.resend_api_key:
            logger.warning("RESEND_API_KEY not configured - emails will not be sent")
        else:
            resend.api_key = settings.resend_api_key
            logger.info("Email service initialized with Resend API")
    
    async def _send_email(self, to: str, subject: str, html_content: str) -> bool:
        """Send email using Resend API."""
        if not settings.resend_api_key:
            logger.error("Cannot send email: RESEND_API_KEY not configured")
            return False
        
        try:
            params = {
                "from": settings.resend_from_email,
                "to": [to],
                "subject": subject,
                "html": html_content,
            }
            resend.Emails.send(params)
            return True
        except Exception as e:
            logger.error(f"Resend API error: {e}")
            return False
    
    async def send_verification_email(self, email: str, username: str, token: str) -> bool:
        """
        Send email verification link to user.
        
        Args:
            email: User's email address
            username: User's username
            token: Verification token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        verification_link = f"{settings.frontend_url}/verify-email?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1DA1F2; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #1DA1F2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to X Clone!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username}!</h2>
                    <p>Thank you for signing up. Please verify your email address to activate your account.</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email</a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #1DA1F2;">{verification_link}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 X Clone. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = await self._send_email(email, "Verify your X Clone account", html_content)
                                                
        if success:
            logger.info(f"Verification email sent to {email}")
        else:
            logger.error(f"Failed to send verification email to {email}")
        
        return success
    
    async def send_password_reset_email(self, email: str, username: str, token: str) -> bool:
        """
        Send password reset link to user.
        
        Args:
            email: User's email address
            username: User's username
            token: Reset token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_link = f"{settings.frontend_url}/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1DA1F2; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: #1DA1F2; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {username}!</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #1DA1F2;">{reset_link}</p>
                    <div class="warning">
                        <strong>⚠️ This link will expire in 1 hour.</strong>
                    </div>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 X Clone. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = await self._send_email(email, "Reset your X Clone password", html_content)
        
        if success:
            logger.info(f"Password reset email sent to {email}")
        else:
            logger.error(f"Failed to send password reset email to {email}")
        
        return success


# Singleton instance
email_service = EmailService()
