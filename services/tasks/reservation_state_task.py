from dataclasses import dataclass
from enum import StrEnum

from config import OkoBot
from db import BaseDeDatos
from utils.discord_utils import obtener_hilo, obtener_mensaje
from utils.time_utils import obtener_fecha_cdmx, str_a_fecha


class EstadoReserva(StrEnum):
    ACTIVA = "activa"
    POR_EXPIRAR = "por expirar"
    VENCIDA = "vencida"


@dataclass
class CambioEstadoReserva:
    id_reserva: int
    estado_actual: EstadoReserva
    estado_nuevo: EstadoReserva
    nombre_reserva: str


@dataclass
class ResultadoActualizacionEstado:
    reservas_por_expirar: list[CambioEstadoReserva]
    reservas_vencidas: list[CambioEstadoReserva]
    reservas_no_cambiadas: int


def determinar_nuevo_estado(
    fecha_expiracion: str, estado_actual: EstadoReserva
) -> EstadoReserva:
    fecha_exp = str_a_fecha(fecha_expiracion)
    fecha_actual = obtener_fecha_cdmx().date()

    if fecha_actual > fecha_exp:
        return EstadoReserva.VENCIDA

    elif fecha_actual == fecha_exp:
        return EstadoReserva.POR_EXPIRAR
    else:
        return EstadoReserva(estado_actual)


def detectar_cambios_estado_reserva(bd: BaseDeDatos) -> ResultadoActualizacionEstado:
    reservas = bd.reservas.obtener_reservas()
    resultado = ResultadoActualizacionEstado(
        reservas_por_expirar=[], reservas_vencidas=[], reservas_no_cambiadas=0
    )

    for reserva in reservas:
        estado_actual = EstadoReserva(reserva["estado"])
        nuevo_estado = determinar_nuevo_estado(
            fecha_expiracion=reserva["fecha_expiracion"], estado_actual=estado_actual
        )

        if nuevo_estado != estado_actual:
            cambio = CambioEstadoReserva(
                id_reserva=reserva["id_reserva"],
                estado_actual=estado_actual,
                estado_nuevo=nuevo_estado,
                nombre_reserva=reserva["nombre_personaje"],
            )
            if nuevo_estado == EstadoReserva.POR_EXPIRAR:
                resultado.reservas_por_expirar.append(cambio)
            elif nuevo_estado == EstadoReserva.VENCIDA:
                resultado.reservas_vencidas.append(cambio)

        else:
            resultado.reservas_no_cambiadas += 1

    return resultado


async def actualizar_mensajes_estado_reserva(
    reservas: ResultadoActualizacionEstado, bot: OkoBot
) -> int:
    """
    Actualiza los mensajes de las reservas que han cambiado de estado a "Por Expirar" o "Vencida".
    Parámetros:
    - reservas: Un objeto ResultadoActualizacionEstado con las reservas por expirar y vencidas.
    - bot: Instancia del bot OkoBot
    """
    contador_fallos = 0

    for cambio in reservas.reservas_por_expirar + reservas.reservas_vencidas:
        reserva = bot.bd.reservas.obtener_reserva_por_id(cambio.id_reserva)
        if not reserva:
            contador_fallos += 1
            continue
        hilo = await obtener_hilo(bot, reserva["id_hilo"])
        if not hilo:
            contador_fallos += 1
            continue

        mensaje = await obtener_mensaje(hilo, reserva["id_mensaje"])
        if not mensaje or not mensaje.embeds:
            contador_fallos += 1
            continue

        embed = mensaje.embeds[0]
        # TODO: Aquí se debería modificar el embed para reflejar el nuevo estado de la reserva (por expirar o vencida)
        # Aún no hago la plantilla para embed de reserva

    return contador_fallos
