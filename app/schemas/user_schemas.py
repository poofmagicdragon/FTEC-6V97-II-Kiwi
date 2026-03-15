from pydantic import BaseModel, Field


class CreateUserSchema(BaseModel):
    username: str = Field(..., description = "User's name")
    firstname: str = Field(..., description = "User's first name")
    lastname: str = Field(..., description = "User's last name")
    balance: float = Field(..., description = "User's money")