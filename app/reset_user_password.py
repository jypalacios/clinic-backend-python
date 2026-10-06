import getpass
import sys

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User


def main() -> int:
    email = input("Correo del usuario: ").strip()
    if not email:
        print("El correo es obligatorio.", file=sys.stderr)
        return 1

    password = getpass.getpass("Nueva contraseña: ")
    confirmation = getpass.getpass("Confirme la nueva contraseña: ")
    if not password:
        print("La contraseña no puede estar vacía.", file=sys.stderr)
        return 1
    if password != confirmation:
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return 1

    password_hash = get_password_hash(password)
    try:
        with SessionLocal.begin() as db:
            user_id = db.scalar(select(User.id).where(User.email == email))
            if user_id is None:
                print("No existe un usuario con ese correo.", file=sys.stderr)
                return 1

            db.execute(
                text(
                    """
                    CALL sp_cambiar_password_user(
                        CAST(:user_id AS INTEGER),
                        CAST(:password_hash AS VARCHAR),
                        NULL,
                        NULL
                    )
                    """
                ),
                {"user_id": user_id, "password_hash": password_hash},
            )
    except OperationalError as exc:
        message = str(exc.orig).lower()
        if "could not translate host name" in message or "getaddrinfo failed" in message:
            print(
                "La base de datos no es accesible desde este entorno. "
                "Ejecute dentro del contenedor: "
                "docker exec -it clinica_backend python -m app.reset_user_password",
                file=sys.stderr,
            )
        else:
            print("No se pudo conectar con la base de datos.", file=sys.stderr)
        return 1
    except SQLAlchemyError as exc:
        original = getattr(exc, "orig", None)
        sqlstate = getattr(original, "sqlstate", None)
        suffix = f" (SQLSTATE {sqlstate})" if sqlstate else ""
        print(f"Falló la actualización en la base de datos{suffix}.", file=sys.stderr)
        return 1

    print("Contraseña actualizada correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())