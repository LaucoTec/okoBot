from dataclasses import dataclass
from sqlite3 import Error

from discord import HTTPException

from config import ID_LOGS_FICHAS, ID_LOGS_OBRAS, ID_LOGS_RESERVAS, OkoBot
from db.database import BaseDeDatos
from embeds.daily_task_embeds import (
    log_estados_reservas,
    log_integridad_ids,
    log_purga_registros,
    log_sincronizacion_obras,
)
from logs.loggers import audit_logger, bot_logger, db_logger
from models.db_models import SincronizacionReserva
from services.tasks.expired_records import (
    ResultadoLimpiezaRegistros,
    detectar_registros_antiguos,
)
from services.tasks.integrity_task import (
    ResultadoIntegridad,
    detectar_integridad_ids,
)
from services.tasks.reservation_state_task import (
    ResultadoActualizacionEstado,
    actualizar_mensajes_estado_reserva,
    detectar_cambios_estado_reserva,
)
from services.tasks.universes_update_task import (
    ResultadoSincronizacionObras,
    detectar_actualizaciones_obras,
)
from utils.discord_utils import obtener_canal_mensajes


@dataclass
class EjecucionIntegridad(
    ResultadoIntegridad,
):
    """
    Representa el resultado de la ejecución de la tarea de integridad de IDs con los cambios confirmados.
    Atributos:
    - fichas_invalidas: Lista de registros de fichas eliminadas por referencias inválidas.
    - reservas_invalidas: Lista de registros de reservas eliminadas por referencias inválidas.
    """


@dataclass
class EjecucionActualizacionEstado(
    ResultadoActualizacionEstado,
):
    """
    Representa el resultado de la ejecución de la tarea de actualización de estado de reservas con los cambios confirmados.
    Atributos:
    - reservas_actualizadas: Lista de registros de reservas actualizadas.
    """


async def servicio_integridad_ids(bot: OkoBot) -> EjecucionIntegridad:
    """
    Ejecuta la tarea Integridad de IDs, que elimina los registros de fichas y reservas que tienen referencias a mensajes o hilos que ya no existen en Discord.
    Parámetros:
    - bot: Instancia del bot OkoBot
    Retorna:
    - Un objeto EjecucionIntegridad con dos listas: "fichas_invalidas" y "reservas_invalidas"
    """

    bot_logger.info("--Iniciando tarea de integridad de IDs--")

    resultado = await detectar_integridad_ids(bot=bot)

    fichas_eliminadas = []
    reservas_eliminadas = []
    cont = 0

    for registro in resultado.fichas_invalidas:
        try:
            if bot.bd.fichas.eliminar_ficha_definitivo(registro.id_registro):
                fichas_eliminadas.append(registro)
        except Error:
            cont += 1
            db_logger.error(
                f"No se pudo eliminar la ficha {registro.nombre} con ID {registro.id_registro}.",
                exc_info=True,
            )

    for registro in resultado.reservas_invalidas:
        try:
            if bot.bd.reservas.eliminar_reserva_definitiva(registro.id_registro):
                reservas_eliminadas.append(registro)
        except Error:
            cont += 1
            db_logger.error(
                f"No se pudo eliminar la reserva {registro.nombre} con ID {registro.id_registro}.",
                exc_info=True,
            )

    return EjecucionIntegridad(
        fichas_invalidas=fichas_eliminadas, reservas_invalidas=reservas_eliminadas
    )


async def servicio_log_integridad_ids(
    bot: OkoBot, resultado: EjecucionIntegridad
) -> None:
    """
    Envía logs de la tarea de integridad de IDs a los canales correspondientes.
    Parámetros:
    - bot: Instancia del bot OkoBot
    - resultado: Objeto EjecucionIntegridad con los registros realmente eliminados
    """
    fichas_eliminadas = len(resultado.fichas_invalidas)
    reservas_eliminadas = len(resultado.reservas_invalidas)

    bot_logger.info(f"Fichas eliminadas: {fichas_eliminadas}")
    bot_logger.info(f"Reservas eliminadas: {reservas_eliminadas}")

    embed_fichas, embed_reservas = log_integridad_ids(registros=resultado)
    if resultado.fichas_invalidas:
        for registro in resultado.fichas_invalidas:
            audit_logger.info(
                f"Ficha eliminada: ID {registro.id_registro}, Nombre ficha: {registro.nombre}, Motivo: Referencia inválida."
            )

        try:
            canal_fichas = await obtener_canal_mensajes(bot, ID_LOGS_FICHAS)

            if canal_fichas:
                await canal_fichas.send(
                    content="Tarea Integridad de IDs - Fichas Eliminadas",
                    embed=embed_fichas,
                )
            else:
                bot_logger.warning(
                    f"No se encontró el canal de logs de fichas con ID {ID_LOGS_FICHAS}"
                )
        except HTTPException as e:
            bot_logger.error(
                f"Error al enviar el mensaje de log de fichas eliminadas: {e}",
                exc_info=True,
            )

    if resultado.reservas_invalidas:
        for registro in resultado.reservas_invalidas:
            audit_logger.info(
                f"Reserva eliminada: ID {registro.id_registro}, Nombre: {registro.nombre}, Motivo: Referencia inválida."
            )

        try:
            canal_reservas = await obtener_canal_mensajes(bot, ID_LOGS_RESERVAS)

            if canal_reservas:
                await canal_reservas.send(
                    content="Tarea Integridad de IDs - Reservas Eliminadas",
                    embed=embed_reservas,
                )
            else:
                bot_logger.warning(
                    f"No se encontró el canal de logs de reservas con ID {ID_LOGS_RESERVAS}"
                )
        except HTTPException as e:
            bot_logger.error(
                f"Error al enviar el mensaje de log de reservas eliminadas: {e}",
                exc_info=True,
            )

    bot_logger.info("--Tarea integridad de IDs finalizada--")


async def servicio_actualizar_estados_reservas(
    bot: OkoBot,
) -> EjecucionActualizacionEstado:
    """
    Ejecuta la tarea de actualización de estados de reservas, que verifica las fechas de expiración y actualiza el estado de cada reserva a "Por Expirar" o "Vencida" según corresponda.
    Parámetros:
    - bot: Instancia del bot OkoBot
    Retorna:
    - Un objeto ResultadoActualizacionEstado con listas de reservas por expirar, vencidas y un conteo de reservas sin cambios.
    """
    bot_logger.info("--Iniciando tarea de actualización estados de reserva--")
    resultado = detectar_cambios_estado_reserva(bot.bd.reservas)
    reservas_por_expirar = []
    reservas_vencidas = []

    for reserva in resultado.reservas_por_expirar:
        try:
            if bot.bd.reservas.actualizar_estado_reserva(
                reserva.id_reserva, reserva.estado_nuevo.value
            ):
                reservas_por_expirar.append(reserva)
                try:
                    bot.bd.reservas.actualizar_sincronizacion_reserva(
                        id_reserva=reserva.id_reserva,
                        nuevo_estado=SincronizacionReserva.DESINCRONIZADO,
                    )
                except Error:
                    db_logger.error(
                        f"No se pudo actualizar la sincronización de la reserva {reserva.nombre_reserva} con ID {reserva.id_reserva}.",
                        exc_info=True,
                    )
        except Error:
            db_logger.error(
                f"No se pudo actualizar el estado de la reserva {reserva.nombre_reserva} con ID {reserva.id_reserva}.",
                exc_info=True,
            )
            continue

    for reserva in resultado.reservas_vencidas:
        try:
            if bot.bd.reservas.actualizar_estado_reserva(
                reserva.id_reserva, reserva.estado_nuevo.value
            ):
                reservas_vencidas.append(reserva)
                try:
                    bot.bd.reservas.actualizar_sincronizacion_reserva(
                        id_reserva=reserva.id_reserva,
                        nuevo_estado=SincronizacionReserva.DESINCRONIZADO,
                    )
                except Error:
                    db_logger.error(
                        f"No se pudo actualizar la sincronización de la reserva {reserva.nombre_reserva} con ID {reserva.id_reserva}.",
                        exc_info=True,
                    )
        except Error:
            db_logger.error(
                f"No se pudo actualizar el estado de la reserva {reserva.nombre_reserva} con ID {reserva.id_reserva}.",
                exc_info=True,
            )
            continue

    cambios = EjecucionActualizacionEstado(
        reservas_por_expirar=reservas_por_expirar,
        reservas_vencidas=reservas_vencidas,
    )
    actualizaciones = await actualizar_mensajes_estado_reserva(cambios, bot)

    return EjecucionActualizacionEstado(
        reservas_por_expirar=actualizaciones.reservas_por_expirar,
        reservas_vencidas=actualizaciones.reservas_vencidas,
    )


async def servicio_log_actualizar_estados_reservas(
    bot: OkoBot, resultado: EjecucionActualizacionEstado
) -> None:
    reservas_por_expirar = len(resultado.reservas_por_expirar)
    reservas_vencidas = len(resultado.reservas_vencidas)

    bot_logger.info(f"Reservas por expirar: {reservas_por_expirar}")
    bot_logger.info(f"Reservas vencidas: {reservas_vencidas}")

    for cambio in resultado.reservas_por_expirar + resultado.reservas_vencidas:
        audit_logger.info(
            f"Reserva actualizada: ID {cambio.id_reserva}, Nombre '{cambio.nombre_reserva}', Actualizada de estado '{cambio.estado_actual}' a '{cambio.estado_nuevo.value}'"
        )

    embed_por_expirar, embed_vencidas = log_estados_reservas(registros=resultado)

    try:
        canal = await obtener_canal_mensajes(bot=bot, canal_id=ID_LOGS_RESERVAS)
        if not canal:
            bot_logger.warning(
                f"El canal de logs de reservas con ID {ID_LOGS_RESERVAS} no fue encontrado."
            )
            return

        if resultado.reservas_por_expirar:
            await canal.send(
                content="Tarea Actualización Estados Reservas - Fichas por expirar hoy",
                embed=embed_por_expirar,
            )

        if resultado.reservas_vencidas:
            await canal.send(
                content="Tarea Actualización Estados Reservas - Fichas vencidas hoy",
                embed=embed_vencidas,
            )
    except HTTPException as e:
        bot_logger.error(
            f"Error al enviar el mensaje de log de actualización de estados de reservas: {e}",
            exc_info=True,
        )

    bot_logger.info("--Tarea actualización estados reservas finalizada--")


async def servicio_sincronizar_obras(bot: OkoBot) -> ResultadoSincronizacionObras:

    bot_logger.info("--Iniciando tarea de sincronización de obras--")
    resultado = await detectar_actualizaciones_obras(bot=bot)
    creadas = []
    actualizadas = []
    eliminadas = []

    try:
        async with bot.bd.transaccion():
            for creada in resultado.obras_creadas:
                if bot.bd.obras.crear_obra(
                    nombre_obra=creada.nombre, id_hilo=creada.id_hilo
                ):
                    creadas.append(creada)

            for actualizada in resultado.obras_actualizadas:
                if bot.bd.obras.actualizar_obra(
                    id_obra=actualizada.id_obra, nombre_obra=actualizada.nombre_nuevo
                ):
                    actualizadas.append(actualizada)

            for eliminada in resultado.obras_eliminadas:
                if bot.bd.obras.eliminar_obra(id_obra=eliminada.id_obra):
                    eliminadas.append(eliminada)
    except Error:
        db_logger.error(
            "Error al sincronizar obras en la base de datos. Todos los cambios han sido revertidos.",
            exc_info=True,
        )

    return ResultadoSincronizacionObras(
        obras_creadas=creadas,
        obras_actualizadas=actualizadas,
        obras_eliminadas=eliminadas,
    )


async def servicio_log_sincronizar_obras(
    bot: OkoBot, resultado: ResultadoSincronizacionObras
) -> None:

    obras_creadas = len(resultado.obras_creadas)
    obras_actualizadas = len(resultado.obras_actualizadas)
    obras_eliminadas = len(resultado.obras_eliminadas)

    bot_logger.info(f"Obras creadas: {obras_creadas}.")
    bot_logger.info(f"Obras actualizadas: {obras_actualizadas}.")
    bot_logger.info(f"Obras eliminadas: {obras_eliminadas}.")

    for creada in resultado.obras_creadas:
        audit_logger.info(f"Obra creada: Nombre {creada.nombre}")

    for actualizada in resultado.obras_actualizadas:
        audit_logger.info(
            f"Obra actualizada: Nombre anterior '{actualizada.nombre_anterior}', Nombre nuevo '{actualizada.nombre_nuevo}'"
        )

    for eliminada in resultado.obras_eliminadas:
        audit_logger.info(
            f"Obra eliminada: ID {eliminada.id_obra}, Nombre {eliminada.nombre}"
        )

    embed_creadas, embed_actualizadas, embed_eliminadas = log_sincronizacion_obras(
        registros=resultado
    )

    canal = await obtener_canal_mensajes(bot=bot, canal_id=ID_LOGS_OBRAS)

    if canal:
        if resultado.obras_creadas:
            await canal.send(
                content="Tarea Sincronización de Obras - Obras Creadas.",
                embed=embed_creadas,
            )

        if resultado.obras_actualizadas:
            await canal.send(
                content="Tarea Sincronización de Obras - Obras Actualizadas.",
                embed=embed_actualizadas,
            )

        if resultado.obras_eliminadas:
            await canal.send(
                content="Tarea Sincronización de Obras - Obras Eliminadas.",
                embed=embed_eliminadas,
            )

    else:
        bot_logger.warning(
            f"No se encontró el canal de logs de obras con ID {ID_LOGS_OBRAS}"
        )

    bot_logger.info("--Tarea sincronización obras finalizada--")


def servicio_purgar_registros_antiguos(
    bd: BaseDeDatos, dias_tolerancia: int
) -> ResultadoLimpiezaRegistros:
    """
    Ejecuta la tarea de purga de registros antiguos, eliminando fichas y reservas que han sido eliminadas o vencidas por más de 'dias_tolerancia' días.
    Parámetros:
    - bd: Instancia de la base de datos
    - dias_tolerancia: Número de días para considerar un registro como antiguo
    Retorna:
    - Un objeto ResultadoLimpiezaRegistros con listas de fichas y reservas antiguas y un conteo total de registros purgados.
    """
    bot_logger.info("--Iniciando tarea de purga de registros antiguos--")
    resultado = detectar_registros_antiguos(bd=bd, dias_tolerancia=dias_tolerancia)
    fichas = []
    reservas = []

    for ficha in resultado.fichas_antiguas:
        try:
            if bd.fichas.eliminar_ficha_definitivo(ficha.id_registro):
                fichas.append(ficha)
        except Error:
            db_logger.error(
                f"Ocurrió un error al eliminar la ficha con ID {ficha.id_registro}.",
                exc_info=True,
            )

    for reserva in resultado.reservas_antiguas:
        try:
            if bd.reservas.eliminar_reserva_definitiva(reserva.id_registro):
                reservas.append(reserva)
        except Error:
            db_logger.error(
                f"Ocurrió un error al eliminar la reserva con ID {reserva.id_registro}.",
                exc_info=True,
            )

    return ResultadoLimpiezaRegistros(
        fichas_antiguas=fichas,
        reservas_antiguas=reservas,
    )


async def servicio_log_purgar_registros_antiguos(
    bot: OkoBot, resultado: ResultadoLimpiezaRegistros
) -> None:
    """
    Envía logs de la tarea de purga de registros antiguos a los canales correspondientes.
    Parámetros:
    - bot: Instancia del bot OkoBot
    - resultado: Objeto ResultadoLimpiezaRegistros con los registros purgados
    """
    fichas_eliminadas = len(resultado.fichas_antiguas)
    reservas_eliminadas = len(resultado.reservas_antiguas)

    bot_logger.info(f"Fichas eliminadas: {fichas_eliminadas}")
    bot_logger.info(f"Reservas eliminadas: {reservas_eliminadas}")

    for ficha in resultado.fichas_antiguas:
        audit_logger.info(
            f"Ficha purgada: ID {ficha.id_registro}, Nombre '{ficha.nombre}', Fecha estado '{ficha.fecha_estado}'"
        )

    for reserva in resultado.reservas_antiguas:
        audit_logger.info(
            f"Reserva purgada: ID {reserva.id_registro}, Nombre '{reserva.nombre}', Fecha estado '{reserva.fecha_estado}'"
        )

    embed_fichas, embed_reservas = log_purga_registros(registros=resultado)
    try:
        canal_fichas = await obtener_canal_mensajes(bot=bot, canal_id=ID_LOGS_FICHAS)
        canal_reservas = await obtener_canal_mensajes(
            bot=bot, canal_id=ID_LOGS_RESERVAS
        )

        if canal_fichas:
            if resultado.fichas_antiguas:
                await canal_fichas.send(
                    content="Tarea Purga de Registros Antiguos - Fichas Eliminadas.",
                    embed=embed_fichas,
                )

        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de fichas con ID {ID_LOGS_FICHAS}"
            )

        if canal_reservas:
            if resultado.reservas_antiguas:
                await canal_reservas.send(
                    content="Tarea Purga de Registros Antiguos - Reservas Eliminadas.",
                    embed=embed_reservas,
                )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de reservas con ID {ID_LOGS_RESERVAS}"
            )
    except HTTPException as e:
        bot_logger.error(
            f"Error al enviar el mensaje de log de purga de registros antiguos: {e}",
            exc_info=True,
        )

    bot_logger.info("--Tarea purga de registros antiguos finalizada--")
