from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str


class SignupRequest(BaseModel):
    business_name: str
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    message: str