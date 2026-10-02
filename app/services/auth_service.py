from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.repo.get_by_email(data.email)
        if not user:
            raise ValueError("Credenciales inválidas")

        if not verify_password(data.password, user.password):
            raise ValueError("Credenciales inválidas")

        token = create_access_token(subject=user.id)
        return TokenResponse(access_token=token)
