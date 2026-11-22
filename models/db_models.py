from enum import IntEnum


class SincronizacionReserva(IntEnum):
    """Enum que representa los posibles estados de sincronización de una reserva de personaje con Discord."""

    SINCRONIZADO = 0
    DESINCRONIZADO = 1
    SIN_ID_MENSAJE = 2
    REFERENCIA_INVALIDA = 3


class SincronizacionFicha(IntEnum):
    """Enum que representa los posibles estados de sincronización de una ficha de personaje con Discord."""

    SINCRONIZADO = 0
    DESINCRONIZADO = 1
    SIN_ID_MENSAJE = 2
    REFERENCIA_INVALIDA = 3
