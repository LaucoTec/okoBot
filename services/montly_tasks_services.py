from config import ID_ANUNCIOS, ID_LOGS_USUARIOS, OkoBot
from embeds.monthly_task_embeds import aviso_previo, log_purga_usuarios_ausentes
from logs.loggers.audit_logger import logger as audit_logger
from logs.loggers.bot_logger import logger as bot_logger
from services.tasks.left_users_task import (
    ResultadoUsuariosAusentes,
    obtener_usuarios_ausentes,
)
from utils.discord_utils import obtener_canal_mensajes


async def servicio_enviar_aviso_pre_mensual(bot: OkoBot):
    """
    Envía un aviso pre-mensual al canal de anuncios del bot.
    """
    canal_anuncios = await obtener_canal_mensajes(bot, ID_ANUNCIOS)
    if canal_anuncios:
        embed_aviso = aviso_previo()
        await canal_anuncios.send(content="", embed=embed_aviso)


async def servicio_purgar_usuarios_ausentes(bot: OkoBot) -> ResultadoUsuariosAusentes:
    bot_logger.info("--Iniciando tarea de integridad de IDs--")

    resultado = await obtener_usuarios_ausentes(bot)

    for usuario in resultado.usuarios:
        bot.bd.usuarios.eliminar_usuario(usuario.id)

    return resultado


async def servicio_log_purgar_usuarios_ausentes(
    bot: OkoBot, resultado: ResultadoUsuariosAusentes
):

    usuarios_eliminados = len(resultado.usuarios)

    bot_logger.info(f"Usuarios ausentes purgados: {usuarios_eliminados}")

    if usuarios_eliminados > 0:
        embed = log_purga_usuarios_ausentes(resultado)

        for usuario in resultado.usuarios:
            if usuario.nombre:
                audit_logger.info(
                    f"Usuario eliminado por ausencia: ID {usuario.id}, Nombre: {usuario.nombre}"
                )

            else:
                audit_logger.info(f"Usuario eliminado por ausencia: ID: {usuario.id}")

        canal_usuarios = await obtener_canal_mensajes(bot, ID_LOGS_USUARIOS)
        if canal_usuarios:
            await canal_usuarios.send(
                content="Tarea purga usuarios ausentes - Usuarios eliminados",
                embed=embed,
            )

        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de usuarios con ID {ID_LOGS_USUARIOS}"
            )

    bot_logger.info("--Tarea purga de usuarios ausentes finalizada--")
