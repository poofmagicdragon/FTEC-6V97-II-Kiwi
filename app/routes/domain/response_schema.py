from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
    request_id: Optional[str] = None




