"""
Common Pydantic schemas for pagination and shared responses.
"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Pagination metadata in responses."""
    
    current_page: int
    total_pages: int
    page_size: int
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    
    @classmethod
    def create(cls, total_count: int, page: int, limit: int) -> "PaginationMeta":
        """Create pagination metadata from query results."""
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        return cls(
            current_page=page,
            total_pages=total_pages,
            page_size=limit,
            total_count=total_count,
            has_next_page=page < total_pages,
            has_previous_page=page > 1,
        )


class PaginatedResponse(BaseModel):
    """Base paginated response wrapper."""
    
    pagination: PaginationMeta


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str
    success: bool = True
