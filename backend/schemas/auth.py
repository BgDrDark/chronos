from pydantic import EmailStr

from backend.schemas.base import CustomBaseModel


class Token(CustomBaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class LoginResponse(Token):
    password_force_change: bool = False


class TokenData(CustomBaseModel):
    email: EmailStr | None = None
