from pydantic import BaseModel, Field

class ExecuteBuySchema(BaseModel):
    ticker: str = Field(..., description = "Name of the ticker involved in the trade")
    portfolio_id: int = Field(..., description = "The portfolio ID this trade corresponds to")
    quantity: int = Field(..., description = "The amount of shares in the trade")


class ExecuteSellSchema(BaseModel):
    ticker: str = Field(..., description = "Name of the ticker involved in the trade")
    portfolio_id: int = Field(..., description = "The portfolio ID this trade corresponds to")
    quantity: int = Field(..., description = "The amount of shares in the trade")
    sale_price: float = Field(..., description = "The price at which the security was sold at")

