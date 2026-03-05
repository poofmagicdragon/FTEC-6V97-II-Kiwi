from pydantic import BaseModel, Field



class ErrorResponse(BaseModel):
    error_message: str = Field(..., description = 'Error message describing the issue')
    request_id: str = Field(..., description = 'The id of the request as a reference for support')




