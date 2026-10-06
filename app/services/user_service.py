from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import PasswordUpdate, UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(
        self,
        data: UserCreate,
        created_by: int,
        creator_permissions: list[str],
    ) -> User:
        target_role = self.repo.db.get(Role, data.id_role)
        if not target_role:
            raise ValueError("El rol seleccionado no existe")
        privileged_permissions = {"users.manage", "roles.manage"}
        if (
            not set(creator_permissions).intersection(privileged_permissions)
            and set(target_role.permisos).intersection(privileged_permissions)
        ):
            raise ValueError("No tiene permiso para asignar un rol de administración")

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
            usu_creacion=created_by,
        )

        return self.repo.create(user)

    def list_users(self) -> list[User]:
        return self.repo.list_all()

    def get_user(self, user_id: int) -> User | None:
        return self.repo.get_by_id(user_id)

    def update_user(self, user_id: int, data: UserUpdate, updated_by: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")

        if data.email and data.email.lower() != user.email.lower() and self.repo.get_by_email(str(data.email)):
            raise ValueError("El email ya está registrado")

        if data.usuario and data.usuario.lower() != user.usuario.lower() and self.repo.get_by_usuario(data.usuario):
            raise ValueError("El nombre de usuario ya existe")

        if data.cedula and data.cedula != user.cedula and self.repo.get_by_cedula(data.cedula):
            raise ValueError("La cédula ya está registrada")
        if data.id_role is not None and not self.repo.db.get(Role, data.id_role):
            raise ValueError("El rol seleccionado no existe")

        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(user, field, value)

        user.usu_actualizacion = updated_by
        user.fec_actualizacion = datetime.now(timezone.utc)
        return self.repo.update(user)

    def update_password(self, user_id: int, data: PasswordUpdate, updated_by: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        user.password = get_password_hash(data.password)
        user.usu_actualizacion = updated_by
        user.fec_actualizacion = datetime.now(timezone.utc)
        self.repo.update(user)

    def delete_user(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        self.repo.delete(user)
