from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    user_id: int
    username: str
    role: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
