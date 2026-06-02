from config import ID_LOGS_FICHAS, ID_LOGS_RESERVAS, OkoBot
from embeds.task_embeds import log_integridad_ids
from logs.loggers.audit_logger import logger as audit_logger
from logs.loggers.bot_logger import logger as bot_logger
from services.tasks.integrity_task import (
    ResultadoIntegridad,
    integridad_ids_fichas,
    integridad_ids_reservas,
)
from utils.discord_utils import obtener_canal_mensajes


async def servicio_integridad_ids(bot: OkoBot) -> ResultadoIntegridad:
    """
    Ejecuta la tarea Integridad de IDs, que elimina los registros de fichas y reservas que tienen referencias a mensajes o hilos que ya no existen en Discord.
    Parámetros:
    - bot: Instancia del bot OkoBot
    Retorna:
    - Un diccionario con dos listas: "fichas_invalidas" y "reservas_invalidas"
    """

    bot_logger.info("Iniciando tarea de integridad de IDs")
    resultado = ResultadoIntegridad(fichas_invalidas=[], reservas_invalidas=[])

    # Validar fichas
    fichas_invalidas = await integridad_ids_fichas(bot)
    resultado.fichas_invalidas = fichas_invalidas
    bot_logger.info(f"Fichas eliminadas: {len(fichas_invalidas)}")

    # Validar reservas
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
