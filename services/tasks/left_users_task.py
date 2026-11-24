from dataclasses import dataclass

from discord import HTTPException, Message, Thread

from config import ID_SERVER, OkoBot
from logs.loggers import bot_logger
from utils.discord_utils import (
    obtener_canal_mensajes,
    obtener_mensaje,
    obtener_miembro,
    obtener_usuario,
)


@dataclass
class UsuariosAusentes:
    id: int
    nombre: str | None
    mensajes_reservas: dict[int, int]
    hilos_fichas: list[int]


@dataclass
class ResultadoUsuariosAusentes:
    usuarios: list[UsuariosAusentes]


async def obtener_usuarios_ausentes(bot: OkoBot) -> ResultadoUsuariosAusentes:

    usuarios = bot.bd.usuarios.obtener_usuarios()
    usuarios_ausentes = []

    for usuario in usuarios:
        if not await obtener_miembro(
            bot=bot, servidor_id=ID_SERVER, usuario_id=usuario["id_usuario"]
        ):
            reservas = {
                reserva["id_hilo"]: reserva["id_mensaje"]
                for reserva in bot.bd.reservas.obtener_reservas_por_usuario(
                    usuario["id_usuario"]
                )
            }
            fichas = [
                ficha["id_hilo"]
                for ficha in bot.bd.fichas.obtener_fichas_por_usuario(
                    id_propietario=usuario["id_usuario"]
                )
            ]
            ausente = await obtener_usuario(bot, usuario["id_usuario"])
            if ausente:
                usuarios_ausentes.append(
                    UsuariosAusentes(
                        id=ausente.id,
                        nombre=ausente.name,
                        mensajes_reservas=reservas,
                        hilos_fichas=fichas,
                    )
                )
            else:
                usuarios_ausentes.append(
                    UsuariosAusentes(
                        id=usuario["id_usuario"],
                        nombre=None,
                        mensajes_reservas={},
                        hilos_fichas=[],
                    )
                )

    resultado = ResultadoUsuariosAusentes(usuarios=usuarios_ausentes)

    return resultado


async def _eliminar_mensajes(bot: OkoBot, mensajes: dict[int, int]):
    for hilo, mensaje in mensajes.items():
        try:
            canal = await obtener_canal_mensajes(bot=bot, canal_id=hilo)
            if isinstance(canal, Thread):
                mensaje = await obtener_mensaje(canal=canal, mensaje_id=mensaje)
                if isinstance(mensaje, Message):
                    await mensaje.delete()
        except HTTPException as e:
            bot_logger.error(
                f"Error al eliminar el mensaje con ID {mensaje} en el canal {hilo}: {e}",
                exc_info=True,
            )


async def _eliminar_hilos(bot: OkoBot, hilos: list[int]):
    for hilo in hilos:
        try:
            canal = await obtener_canal_mensajes(bot=bot, canal_id=hilo)
            if isinstance(canal, Thread):
                await canal.delete()
        except HTTPException as e:
            bot_logger.error(
                f"Error al eliminar el hilo {hilo}: {e}",
                exc_info=True,
            )


async def eliminar_usuario_discord(
    bot: OkoBot, registros: ResultadoUsuariosAusentes
): ...
