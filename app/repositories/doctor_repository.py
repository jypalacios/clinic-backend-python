from sqlalchemy.orm import Session

from app.models.doctor import Doctor


class DoctorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, doctor_id: int) -> Doctor | None:
        return self.db.query(Doctor).filter(Doctor.id_doctors == doctor_id).first()

    def get_by_email(self, email: str) -> Doctor | None:
        return self.db.query(Doctor).filter(Doctor.email == email).first()

    def list_all(self) -> list[Doctor]:
        return self.db.query(Doctor).all()

    def create(self, doctor: Doctor) -> Doctor:
        self.db.add(doctor)
        self.db.commit()
        self.db.refresh(doctor)
        return doctor

    def update(self, doctor: Doctor) -> Doctor:
        self.db.commit()
        self.db.refresh(doctor)
        return doctor

    def delete(self, doctor: Doctor) -> None:
        self.db.delete(doctor)
        self.db.commit()
