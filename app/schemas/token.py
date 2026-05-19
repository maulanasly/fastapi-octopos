# pyrefly: ignore [missing-import]
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str | None = None
