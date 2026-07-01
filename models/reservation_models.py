from dataclasses import dataclass
from datetime import date, datetime

from services.tasks.reservation_state_task import EstadoReserva


@dataclass
class SolicitudReserva:
    id_usuario: int

    nombre_personaje: str
    id_obra: int
    nombre_obra: str
    nombre_obra_original: str | None = None

    id_canal_esperado: int | None = None
    id_mensaje_esperado: int | None = None

    # control del flujo
    expira_en: datetime | None = None
    puede_cancelarse: bool = True

    # se llenan cuando manda la imagen
    url_imagen: str | None = None
    autor_nombre: str | None = None
    autor_icono_url: str | None = None

    # se llenan al calcular duración
    fecha_reserva: date | None = None
    fecha_expiracion: date | None = None


@dataclass
class ReservaNueva:
    id_propietario: int
    nombre_personaje: str
    id_obra: int

    fecha_reserva: date
    fecha_expiracion: date
    estado: EstadoReserva

    enlace_imagen: str
    id_hilo: int


@dataclass
class DatosReserva:
    id_reserva: int
    id_propietario: int

    nombre_personaje: str
    id_obra: int
    nombre_obra: str

    fecha_reserva: date
    fecha_expiracion: date
    estado: EstadoReserva

    enlace_imagen: str
    id_hilo: int
    id_mensaje: int | None

    autor_nombre: str
    autor_icono_url: str | None
