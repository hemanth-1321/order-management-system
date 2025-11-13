from pydantic import BaseModel,EmailStr,ConfigDict


class UserBase(BaseModel):
    name:str
    email:EmailStr
    password:str
    model_config = ConfigDict(extra="forbid")

class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    id:int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")

class RefreshRequest(BaseModel):
    refresh_token:str