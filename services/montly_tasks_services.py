from sqlite3 import Error

from discord import HTTPException, TextChannel

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
from logs.loggers import audit_logger, bot_logger, db_logger
from services.tasks.afk_users import (
    ResultadoUsuariosInactivos,
    obtener_usuarios_inactivos,
)
from services.tasks.left_users_task import (
    ResultadoUsuariosAusentes,
    eliminar_usuario_discord,
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
        try:
            await canal_anuncios.send(content="", embed=embed_aviso)
        except HTTPException:
            bot_logger.error(
                f"No se pudo enviar el aviso pre-mensual al canal de anuncios con ID {ID_ANUNCIOS}.",
                exc_info=True,
            )
    else:
        bot_logger.warning(f"No se encontró el canal de anuncios con ID {ID_ANUNCIOS}")
        raise TypeError(f"No se encontró el canal de anuncios con ID {ID_ANUNCIOS}")


async def servicio_purgar_usuarios_ausentes(bot: OkoBot) -> ResultadoUsuariosAusentes:
    bot_logger.info("--Iniciando tarea de purga de usuarios ausentes--")

    resultado = await obtener_usuarios_ausentes(bot)
    exitos = []

    for usuario in resultado.usuarios:
        try:
            eliminado = bot.bd.usuarios.eliminar_usuario(usuario.id)
        except Error:
            db_logger.error(
                f"No se pudo eliminar al usuario {usuario.nombre} con ID {usuario.id}.",
                exc_info=True,
            )
            continue
        else:
            if eliminado:
                exitos.append(usuario)

    await eliminar_usuario_discord(bot=bot, registros=ResultadoUsuariosAusentes(exitos))

    return ResultadoUsuariosAusentes(usuarios=exitos)


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
            try:
                await canal_usuarios.send(
                    content="Tarea purga usuarios ausentes - Usuarios eliminados",
                    embed=embed,
                )
            except HTTPException:
                bot_logger.error(
                    f"No se pudo enviar el log de purga de usuarios ausentes al canal de logs de usuarios con ID {ID_LOGS_USUARIOS}.",
                    exc_info=True,
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

    resultado = await obtener_usuarios_inactivos(bot)
    exitos = []

    canal_advertencias = await obtener_canal_mensajes(bot, ID_ADVERTENCIAS)
    if not isinstance(canal_advertencias, TextChannel):
        bot_logger.warning(
            f"No se encontró el canal de advertencias con ID {ID_ADVERTENCIAS}"
        )
        raise TypeError(
            f"No se encontró el canal de advertencias con ID {ID_ADVERTENCIAS}"
        )

    for usuario in resultado.usuarios:
        embed = advertencia_usuario_inactivo(usuario)

        try:
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

            await hilo.send(content="", embed=embed)
        except HTTPException:
            bot_logger.error(
                f"No se pudo crear o enviar la advertencia al usuario "
                f"{usuario.nombre} con ID {usuario.id}. "
                "No se modificarán sus registros.",
                exc_info=True,
            )
            continue

        try:
            async with bot.bd.transaccion():
                for id_ficha in usuario.fichas:
                    ficha = bot.bd.fichas.actualizar_estado_ficha(
                        id_ficha=id_ficha,
                        nuevo_estado="eliminada",
                    )
                    if not ficha:
                        raise Error(
                            f"No se pudo actualizar el estado de la ficha con ID {id_ficha}."
                        )

                for id_reserva in usuario.reservas:
                    reserva = bot.bd.reservas.actualizar_estado_reserva(
                        id_reserva=id_reserva,
                        nuevo_estado="vencida",
                    )
                    if not reserva:
                        raise Error(
                            f"No se pudo actualizar el estado de la reserva con ID {id_reserva}."
                        )
        except Error as error:
            db_logger.error(
                f"No se pudieron actualizar los registros del usuario "
                f"{usuario.nombre} con ID {usuario.id} después de enviar "
                "la advertencia. La transacción fue revertida.",
                exc_info=(type(error), error, error.__traceback__),
            )
            try:
                await hilo.delete()
            except HTTPException:
                bot_logger.error(
                    f"No se pudo eliminar el hilo de advertencia del usuario "
                    f"{usuario.nombre} con ID {usuario.id} tras revertir "
                    "la transacción.",
                    exc_info=True,
                )
        else:
            exitos.append(usuario)

    return ResultadoUsuariosInactivos(usuarios=exitos)


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
                try:
                    await canal_usuarios.send(
                        content="Tarea desactivación de usuarios inactivos - Usuarios desactivados",
                        embed=embed_usuario,
                    )
                except HTTPException:
                    bot_logger.error(
                        f"No se pudo enviar el log de desactivación de usuarios inactivos al canal de logs de usuarios con ID {ID_LOGS_USUARIOS}.",
                        exc_info=True,
                    )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de usuarios con ID {ID_LOGS_USUARIOS}"
            )
        canal_fichas = await obtener_canal_mensajes(bot, ID_LOGS_FICHAS)
        if canal_fichas:
            if fichas_desactivadas > 0:
                try:
                    await canal_fichas.send(
                        content="Tarea desactivación de usuarios inactivos - Fichas desactivadas",
                        embed=embed_fichas,
                    )
                except HTTPException:
                    bot_logger.error(
                        f"No se pudo enviar el log de desactivación de usuarios inactivos al canal de logs de fichas con ID {ID_LOGS_FICHAS}.",
                        exc_info=True,
                    )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de fichas con ID {ID_LOGS_FICHAS}"
            )
        canal_reservas = await obtener_canal_mensajes(bot, ID_LOGS_RESERVAS)
        if canal_reservas:
            if reservas_desactivadas > 0:
                try:
                    await canal_reservas.send(
                        content="Tarea desactivación de usuarios inactivos - Reservas desactivadas",
                        embed=embed_reservas,
                    )
                except HTTPException:
                    bot_logger.error(
                        f"No se pudo enviar el log de desactivación de usuarios inactivos al canal de logs de reservas con ID {ID_LOGS_RESERVAS}.",
                        exc_info=True,
                    )
        else:
            bot_logger.warning(
                f"No se encontró el canal de logs de reservas con ID {ID_LOGS_RESERVAS}"
            )

    bot_logger.info("--Tarea desactivación de usuarios inactivos finalizada--")
