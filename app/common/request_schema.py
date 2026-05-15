from pydantic import BaseModel, Field

class PortfolioSecurityRequestData(BaseModel):
    username: str = Field(..., description = "Unique identifier for user")
    role: str = Field(..., description = "assigned role of user")