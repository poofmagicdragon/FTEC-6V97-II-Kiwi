from pydantic import BaseModel, Field

class CreatePortfolioSchema(BaseModel):
    name: str = Field(..., description = "Portfolio name")
    description: str = Field(..., description = "Portfolio Description")
#    username: str = Field(..., min_length = 5, max_length = 30, description = "Username")

