"""
API v1 router aggregating all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    comments,
    engagements,
    feed,
    search,
    tweets,
    upload,
    users,
)

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tweets.router)
api_router.include_router(comments.router)
api_router.include_router(engagements.router)
api_router.include_router(feed.router)
api_router.include_router(search.router)
api_router.include_router(upload.router)
