from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, data: UserCreate) -> User:
        if self.repo.get_by_email(data.email):
            raise ValueError("El email ya está registrado")

        if self.repo.get_by_usuario(data.usuario):
            raise ValueError("El nombre de usuario ya existe")

        if self.repo.get_by_cedula(data.cedula):
            raise ValueError("La cédula ya está registrada")

        user = User(
            cedula=data.cedula,
            nombre=data.nombre,
            apellido=data.apellido,
            usuario=data.usuario,
            email=data.email,
            password=get_password_hash(data.password),
            id_role=data.id_role,
            id_estado=data.id_estado,
            usu_creacion=data.usuario,
        )

        return self.repo.create(user)

    def list_users(self) -> list[User]:
        return self.repo.list_all()

    def get_user(self, user_id: int) -> User | None:
        return self.repo.get_by_id(user_id)

    def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        if data.email and data.email != user.email and self.repo.get_by_email(str(data.email)):
            raise ValueError("El email ya está registrado")

        if data.usuario and data.usuario != user.usuario and self.repo.get_by_usuario(data.usuario):
            raise ValueError("El nombre de usuario ya existe")

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)

        return self.repo.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        self.repo.delete(user)
