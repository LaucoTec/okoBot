from dataclasses import dataclass
from enum import StrEnum

from discord import HTTPException, Thread

from config import OkoBot
from db.repos import RepoReservas
from embeds.reservation_embeds import embed_reserva
from services.reservation_services import obtener_datos_reserva
from utils.discord_utils import obtener_canal_mensajes, obtener_mensaje
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


def _determinar_nuevo_estado(
    fecha_expiracion: str, estado_actual: EstadoReserva
) -> EstadoReserva:
    fecha_exp = str_a_fecha(fecha_expiracion)
    fecha_actual = obtener_fecha_cdmx().date()

    if estado_actual == EstadoReserva.VENCIDA:
        return EstadoReserva.VENCIDA

    if fecha_actual > fecha_exp:
        return EstadoReserva.VENCIDA

    elif fecha_actual == fecha_exp:
        return EstadoReserva.POR_EXPIRAR
    else:
        return EstadoReserva(estado_actual)


def detectar_cambios_estado_reserva(bd: RepoReservas) -> ResultadoActualizacionEstado:
    reservas = bd.obtener_reservas()
    resultado = ResultadoActualizacionEstado(
        reservas_por_expirar=[], reservas_vencidas=[], reservas_no_cambiadas=0
    )

    for reserva in reservas:
        estado_actual = EstadoReserva(reserva["estado"])
        nuevo_estado = _determinar_nuevo_estado(
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
    Actualiza los mensajes de las reservas que cambiaron de estado.
    Retorna la cantidad de reservas cuyo mensaje no pudo actualizarse.
    """
    contador_fallos = 0

    cambios = reservas.reservas_por_expirar + reservas.reservas_vencidas

    for cambio in cambios:
        datos_reserva = await obtener_datos_reserva(
            bot=bot,
            id_reserva=cambio.id_reserva,
        )
        if datos_reserva is None:
            contador_fallos += 1
            continue

        hilo = await obtener_canal_mensajes(bot, datos_reserva.id_hilo)
        if not isinstance(hilo, Thread):
            contador_fallos += 1
            continue

        if datos_reserva.id_mensaje is None:
            contador_fallos += 1
            continue

        mensaje = await obtener_mensaje(hilo, datos_reserva.id_mensaje)
        if mensaje is None:
            contador_fallos += 1
            continue

        try:
            await mensaje.edit(embed=embed_reserva(datos_reserva))
        except HTTPException:
            contador_fallos += 1

    return contador_fallos
