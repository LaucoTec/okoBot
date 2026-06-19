from config import ID_LOGS_FICHAS, ID_LOGS_OBRAS, ID_LOGS_RESERVAS, OkoBot
from embeds.task_embeds import log_integridad_ids, log_sincronizacion_obras
from logs.loggers.audit_logger import logger as audit_logger
from logs.loggers.bot_logger import logger as bot_logger
from services.tasks.integrity_task import (
    ResultadoIntegridad,
    integridad_ids_fichas,
    integridad_ids_reservas,
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


async def servicio_integridad_ids(bot: OkoBot) -> ResultadoIntegridad:
    """
    Ejecuta la tarea Integridad de IDs, que elimina los registros de fichas y reservas que tienen referencias a mensajes o hilos que ya no existen en Discord.
    Parámetros:
    - bot: Instancia del bot OkoBot
    Retorna:
    - Un objeto ResultadoIntegridad con dos listas: "fichas_invalidas" y "reservas_invalidas"
    """

    bot_logger.info("Iniciando tarea de integridad de IDs")
    resultado = ResultadoIntegridad(fichas_invalidas=[], reservas_invalidas=[])

    fichas_invalidas = await integridad_ids_fichas(bot)
    resultado.fichas_invalidas = fichas_invalidas
    bot_logger.info(f"Fichas eliminadas: {len(fichas_invalidas)}")

    reservas_invalidas = await integridad_ids_reservas(bot)
    resultado.reservas_invalidas = reservas_invalidas
    bot_logger.info(f"Reservas eliminadas: {len(reservas_invalidas)}")

    for registro in resultado.fichas_invalidas:
        bot.bd.fichas.eliminar_ficha_definitivo(registro.id_registro)
        audit_logger.info(
            f"Ficha eliminada: ID {registro.id_registro}, Nombre ficha: {registro.nombre}, Motivo: Referencia inválida."
        )

    for registro in resultado.reservas_invalidas:
        bot.bd.reservas.eliminar_reserva_definitiva(registro.id_registro)
        audit_logger.info(
            f"Reserva eliminada: ID {registro.id_registro}, Nombre reserva: {registro.nombre}, Motivo: Referencia inválida."
        )
    return resultado


async def servicio_log_integridad_ids(
    bot: OkoBot, resultado: ResultadoIntegridad
) -> None:
    """
    Envía logs de la tarea de integridad de IDs a los canales correspondientes.
    Parámetros:
    - bot: Instancia del bot OkoBot
    - resultado: Objeto ResultadoIntegridad con los registros eliminados
    """
    embed_fichas, embed_reservas = log_integridad_ids(registros=resultado)

    canal_fichas = await obtener_canal_mensajes(bot, ID_LOGS_FICHAS)
    canal_reservas = await obtener_canal_mensajes(bot, ID_LOGS_RESERVAS)

    if canal_fichas:
        await canal_fichas.send(
            content="Tarea Integridad de IDs - Fichas Eliminadas", embed=embed_fichas
        )
    else:
        bot_logger.warning(
            f"No se encontró el canal de logs de fichas con ID {ID_LOGS_FICHAS}"
        )
    if canal_reservas:
        await canal_reservas.send(
            content="Tarea Integridad de IDs - Reservas Eliminadas",
            embed=embed_reservas,
        )
    else:
        bot_logger.warning(
            f"No se encontró el canal de logs de reservas con ID {ID_LOGS_RESERVAS}"
        )


async def servicio_actualizar_estados_reservas(
    bot: OkoBot,
) -> ResultadoActualizacionEstado:
    """
    Ejecuta la tarea de actualización de estados de reservas, que verifica las fechas de expiración y actualiza el estado de cada reserva a "Por Expirar" o "Vencida" según corresponda.
    Parámetros:
    - bot: Instancia del bot OkoBot
    Retorna:
    - Un objeto ResultadoActualizacionEstado con listas de reservas por expirar, vencidas y un conteo de reservas sin cambios.
    """
    bot_logger.info("Iniciando tarea de actualización estados de reserva")
    resultado = detectar_cambios_estado_reserva(bot.bd)

    # Actualizar estados en la base de datos
    for cambio in resultado.reservas_por_expirar + resultado.reservas_vencidas:
        bot.bd.reservas.actualizar_estado_reserva(
            cambio.id_reserva, cambio.estado_nuevo.value
        )
        audit_logger.info(
            f"Reserva ID {cambio.id_reserva} - '{cambio.nombre_reserva}' actualizada de estado '{cambio.estado_actual}' a '{cambio.estado_nuevo.value}'"
        )

    # Actualizar mensajes en Discord
    contador_fallos = await actualizar_mensajes_estado_reserva(resultado, bot)
    if contador_fallos > 0:
        bot_logger.warning(
            f"Hubo {contador_fallos} fallos al actualizar mensajes de reservas por expirar/vencidas."
        )

    return resultado


async def servicio_log_actualizar_estados_reservas(
    bot: OkoBot, resultado: ResultadoActualizacionEstado
) -> None:
    pass


async def servicio_sincronizar_obras(bot: OkoBot) -> ResultadoSincronizacionObras:

    bot_logger.info("Iniciando tarea de sincronización de obras")
    resultado = await detectar_actualizaciones_obras(bot=bot)

    for creada in resultado.obras_creadas:
        bot.bd.obras.crear_obra(nombre_obra=creada.nombre, id_hilo=creada.id_hilo)
        audit_logger.info(f"Obra {creada.nombre} creada")

    for actualizada in resultado.obras_actualizadas:
        bot.bd.obras.actualizar_obra(
            id_obra=actualizada.id_obra, nombre_obra=actualizada.nombre_nuevo
        )
        audit_logger.info(
            f"Obra {actualizada.nombre_anterior} actualizada con el nombre {actualizada.nombre_nuevo}"
        )

    for eliminada in resultado.obras_eliminadas:
        bot.bd.obras.eliminar_obra(id_obra=eliminada.id_obra)
        audit_logger.info(
            f"Obra {eliminada.nombre} con id {eliminada.id_obra} eliminada"
        )

    return resultado


async def servicio_log_sincronizar_obras(
    bot: OkoBot, resultado: ResultadoSincronizacionObras
) -> None:

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
