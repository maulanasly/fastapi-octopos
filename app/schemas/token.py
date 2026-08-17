# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int  # access token lifetime in seconds (proactive refresh)


class TokenPayload(BaseModel):
    sub: str | None = None
    ten: int | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
