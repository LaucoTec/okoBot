from dataclasses import dataclass
from sqlite3 import Error

from discord import HTTPException, Thread

from config import OkoBot
from db.repos import RepoReservas
from embeds.reservation_embeds import embed_reserva
from logs.loggers import bot_logger, db_logger
from models.db_models import SincronizacionReserva
from models.reservation_models import EstadoReserva
from services.reservation_services import obtener_datos_reserva
from utils.discord_utils import obtener_canal_mensajes, obtener_mensaje
from utils.time_utils import obtener_fecha_cdmx, str_a_fecha


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
        reservas_por_expirar=[], reservas_vencidas=[]
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

        if reserva["sincronizado"] == SincronizacionReserva.DESINCRONIZADO:
            cambio = CambioEstadoReserva(
                id_reserva=reserva["id_reserva"],
                estado_actual=estado_actual,
                estado_nuevo=estado_actual,
                nombre_reserva=reserva["nombre_personaje"],
            )
            resultado.reservas_por_expirar.append(cambio)

    return resultado


async def actualizar_mensajes_estado_reserva(
    reservas: ResultadoActualizacionEstado, bot: OkoBot
) -> ResultadoActualizacionEstado:
    """
    Actualiza los mensajes de las reservas que cambiaron de estado.
    Retorna la cantidad de reservas cuyo mensaje no pudo actualizarse.
    """

    cambios = reservas.reservas_por_expirar + reservas.reservas_vencidas
    por_expirar = []
    vencidas = []

    for cambio in cambios:
        datos_reserva = await obtener_datos_reserva(
            bot=bot,
            id_reserva=cambio.id_reserva,
        )

        if datos_reserva is None:
            bot_logger.error(
                f"No se pudo recuperar los datos de la reserva con ID {cambio.id_reserva} para actualizar su mensaje."
            )
            continue
        if not datos_reserva.id_mensaje:
            raise RuntimeError(
                f"La reserva con ID {cambio.id_reserva} no tiene un ID de mensaje asociado."
            )

        try:
            hilo = await obtener_canal_mensajes(bot, datos_reserva.id_hilo)
            if not isinstance(hilo, Thread):
                bot_logger.warning(
                    f"El canal con ID {datos_reserva.id_hilo} no es un hilo o no existe. No se puede actualizar el mensaje de la reserva con ID {cambio.id_reserva}."
                )
                continue

            mensaje = await obtener_mensaje(
                canal=hilo,
                mensaje_id=datos_reserva.id_mensaje,
            )
            if mensaje is None:
                bot_logger.warning(
                    f"No se pudo encontrar el mensaje con ID {datos_reserva.id_mensaje} en el hilo con ID {datos_reserva.id_hilo}. No se puede actualizar el mensaje de la reserva con ID {cambio.id_reserva}."
                )
                continue

            await mensaje.edit(embed=embed_reserva(datos_reserva))
        except HTTPException as e:
            bot_logger.error(
                f"No se pudo actualizar el mensaje de la reserva con ID {cambio.id_reserva}. Error: {e}"
            )
            continue
        else:
            try:
                bot.bd.reservas.actualizar_sincronizacion_reserva(
                    id_reserva=cambio.id_reserva,
                    nuevo_estado=SincronizacionReserva.SINCRONIZADO,
                )
            except Error as e:
                db_logger.error(
                    f"No se pudo actualizar la sincronización de la reserva con ID {cambio.id_reserva}. Error: {e}"
                )

            if cambio.estado_nuevo == EstadoReserva.POR_EXPIRAR:
                por_expirar.append(cambio)
            elif cambio.estado_nuevo == EstadoReserva.VENCIDA:
                vencidas.append(cambio)

    return ResultadoActualizacionEstado(
        reservas_por_expirar=por_expirar, reservas_vencidas=vencidas
    )
