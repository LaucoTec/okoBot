import os
from typing import overload

from dotenv import load_dotenv

load_dotenv()


@overload
def _env(key: str, *, cast: type = str, required: bool = True) -> str: ...


@overload
def _env(key: str, *, cast: type = int, required: bool = True) -> int: ...


def _env(key: str, *, cast: type = str, required: bool = True):
    value = os.getenv(key)
    if value is None:
        if required:
            raise ValueError(f"Missing required environment variable: {key}")
        return None

    if cast is int:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(
                f"Environment variable {key!r} must be an integer, got {value!r}"
            ) from exc

    return value


TOKEN = _env("TOKEN")
# Oko
ID_SERVER = _env("ID_SERVER", cast=int)
# ID de rol Verificador
ID_VERIFICADOR = _env("ID_VERIFICADOR", cast=int)
# ID canal general
ID_GENERAL = _env("ID_GENERAL", cast=int)
# ID canal de verificación
ID_VERIFICACION = _env("ID_VERIFICACION", cast=int)
# ID de canal de advertencias por inactividad
ID_ADVERTENCIAS = _env("ID_ADVERTENCIAS", cast=int)
# ID de canal de repositorio de imágenes
ID_REPOSITORIO = _env("ID_REPOSITORIO", cast=int)
# ID foro de reservas
ID_RESERVAS = _env("ID_RESERVAS", cast=int)
# ID de logs de obras y alias
ID_LOGS_OBRAS = _env("ID_LOGS_OBRAS", cast=int)
# ID de logs de reservas
ID_LOGS_RESERVAS = _env("ID_LOGS_RESERVAS", cast=int)
# Id de logs de fichas
ID_LOGS_FICHAS = _env("ID_LOGS_FICHAS", cast=int)
