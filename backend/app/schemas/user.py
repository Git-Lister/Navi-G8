from pydantic import BaseModel, ConfigDict, Field, validator
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_byte_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password exceeds 72 bytes when encoded. Use a shorter password or avoid non-ASCII characters.')
        return v

class UserResponse(BaseModel):
    id: UUID
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str