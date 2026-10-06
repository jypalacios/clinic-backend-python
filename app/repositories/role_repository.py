from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.id_role).all()

    def get_by_id(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def get_by_name(self, name: str) -> Role | None:
        return self.db.query(Role).filter(func.lower(Role.nom_role) == name.lower()).first()

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update(self, role: Role) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role
