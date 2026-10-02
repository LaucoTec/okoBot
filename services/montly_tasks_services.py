from discord import TextChannel

from config import (
    ID_ADVERTENCIAS,
    ID_ANUNCIOS,
    ID_LOGS_FICHAS,
    ID_LOGS_RESERVAS,
    ID_LOGS_USUARIOS,
    OkoBot,
)
from embeds.monthly_task_embeds import (
    advertencia_usuario_inactivo,
    aviso_previo,
    log_desactivar_usuario_inactivo,
    log_purga_usuarios_ausentes,
)
from logs.loggers.audit_logger import logger as audit_logger
from logs.loggers.bot_logger import logger as bot_logger
from services.tasks.afk_users import (
    ResultadoUsuariosInactivos,
    obtener_usuarios_inactivos,
)
from services.tasks.left_users_task import (
    ResultadoUsuariosAusentes,
    obtener_usuarios_ausentes,
)
from utils.discord_utils import crear_hilo, obtener_canal_mensajes


async def servicio_enviar_aviso_pre_mensual(bot: OkoBot):
    """
    Envía un aviso pre-mensual al canal de anuncios del bot.
    """
    canal_anuncios = await obtener_canal_mensajes(bot, ID_ANUNCIOS)
    if canal_anuncios:
        embed_aviso = aviso_previo()
        await canal_anuncios.send(content="", embed=embed_aviso)


async def servicio_purgar_usuarios_ausentes(bot: OkoBot) -> ResultadoUsuariosAusentes:
    bot_logger.info("--Iniciando tarea de purga de usuarios ausentes--")

    resultado = await obtener_usuarios_ausentes(bot)

    for usuario in resultado.usuarios:
        try:
            bot.bd.usuarios.eliminar_usuario(usuario.id)
        except Exception:
            bot_logger.error(
                f"No se pudo eliminar al usuario {usuario.nombre} con ID {usuario.id}.",
                exc_info=True,
            )
            continue

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


async def servicio_desactivar_usuarios_inactivos(
    bot: OkoBot,
) -> ResultadoUsuariosInactivos:
    """
    Desactiva a los usuarios inactivos en el servidor.
    """
    bot_logger.info("--Iniciando tarea de desactivación de usuarios inactivos--")

    resultado = obtener_usuarios_inactivos(bot.bd)

    canal_advertencias = await obtener_canal_mensajes(bot, ID_ADVERTENCIAS)
    if not isinstance(canal_advertencias, TextChannel):
        bot_logger.warning(
            f"No se encontró el canal de advertencias con ID {ID_ADVERTENCIAS}"
        )
        return resultado

    for usuario in resultado.usuarios:
        embed = advertencia_usuario_inactivo(usuario)

        hilo = await crear_hilo(
            nombre=f"Aviso de inactividad - {usuario.nombre}",
            canal=canal_advertencias,
            bot=bot,
            mensaje=None,
        )
        if not hilo:
            bot_logger.warning(
                f"No se pudo crear un hilo para el usuario "
                f"{usuario.nombre} con ID {usuario.id}. "
                "No se modificarán sus registros."
            )
            continue

        try:
            await hilo.send(content="", embed=embed)
        except Exception:
            bot_logger.error(
                f"No se pudo enviar la advertencia al usuario "
                f"{usuario.nombre} con ID {usuario.id}. "
                "No se modificarán sus registros.",
                exc_info=True,
            )
            continue

        try:
            async with bot.bd.transaccion():
                for id_ficha in usuario.fichas:
                    bot.bd.fichas.actualizar_estado_ficha(
                        id_ficha=id_ficha,
                        nuevo_estado="eliminada",
                    )

                for id_reserva in usuario.reservas:
                    bot.bd.reservas.actualizar_estado_reserva(
                        id_reserva=id_reserva,
                        nuevo_estado="vencida",
                    )

        except Exception:
            bot_logger.error(
                f"No se pudieron actualizar los registros del usuario "
                f"{usuario.nombre} con ID {usuario.id} después de enviar "
                "la advertencia. La transacción fue revertida.",
                exc_info=True,
            )

    return resultado


async def servicio_log_desactivar_usuarios_inactivos(
    bot: OkoBot, resultado: ResultadoUsuariosInactivos
):
    """
    Registra en los logs la desactivación de usuarios inactivos.
    """
    usuarios_desactivados = len(resultado.usuarios)
    fichas_desactivadas = sum(len(u.fichas) for u in resultado.usuarios)
    reservas_desactivadas = sum(len(u.reservas) for u in resultado.usuarios)

    bot_logger.info(f"Usuarios inactivos desactivados: {usuarios_desactivados}")
    bot_logger.info(f"Fichas desactivadas: {fichas_desactivadas}")
    bot_logger.info(f"Reservas desactivadas: {reservas_desactivadas}")

    if usuarios_desactivados > 0:
        for usuario in resultado.usuarios:
            if usuario.nombre:
                audit_logger.info(
                    f"Usuario desactivado por inactividad: ID {usuario.id}, Nombre: {usuario.nombre}"
                )
            else:
                audit_logger.info(
                    f"Usuario desactivado por inactividad: ID: {usuario.id}"
                )

            if usuario.fichas:
                for id_ficha, nombre in usuario.fichas.items():
                    audit_logger.info(
                        f"Ficha desactivada por inactividad: ID {id_ficha}, Nombre: {nombre}"
                    )
            if usuario.reservas:
                for id_reserva, nombre in usuario.reservas.items():
                    audit_logger.info(
                        f"Reserva desactivada por inactividad: ID {id_reserva}, Nombre: {nombre}"
                    )
        embed_usuario, embed_fichas, embed_reservas = log_desactivar_usuario_inactivo(
            resultado
        )
        canal_usuarios = await obtener_canal_mensajes(bot, ID_LOGS_USUARIOS)
        if canal_usuarios:
            if usuarios_desactivados > 0:
                await canal_usuarios.send(
                    content="Tarea desactivación de usuarios inactivos - Usuarios desactivados",
                    embed=embed_usuario,
                )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de usuarios con ID {ID_LOGS_USUARIOS}"
            )
        canal_fichas = await obtener_canal_mensajes(bot, ID_LOGS_FICHAS)
        if canal_fichas:
            if fichas_desactivadas > 0:
                await canal_fichas.send(
                    content="Tarea desactivación de usuarios inactivos - Fichas desactivadas",
                    embed=embed_fichas,
                )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de fichas con ID {ID_LOGS_FICHAS}"
            )
        canal_reservas = await obtener_canal_mensajes(bot, ID_LOGS_RESERVAS)
        if canal_reservas:
            if reservas_desactivadas > 0:
                await canal_reservas.send(
                    content="Tarea desactivación de usuarios inactivos - Reservas desactivadas",
                    embed=embed_reservas,
                )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de reservas con ID {ID_LOGS_RESERVAS}"
            )

    bot_logger.info("--Tarea desactivación de usuarios inactivos finalizada--")
