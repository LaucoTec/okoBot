from discord import (
    Attachment,
    Guild,
    Member,
    Message,
    NotFound,
    TextChannel,
    Thread,
    User,
)
from discord.abc import GuildChannel
from discord.ext import commands

from config import ID_SERVER


async def _obtener_servidor(bot: commands.Bot, server_id: int) -> Guild | None:
    servidor = bot.get_guild(server_id)

    if servidor is None:
        try:
            servidor = await bot.fetch_guild(server_id)

        except NotFound:
            return None

    return servidor


async def obtener_usuario(bot: commands.Bot, usuario_id: int) -> User | None:
    usuario = bot.get_user(usuario_id)

    if usuario is None:
        try:
            usuario = await bot.fetch_user(usuario_id)

        except NotFound:
            return None


async def obtener_miembro(bot: commands.Bot, usuario_id: int) -> Member | None:
    servidor = await _obtener_servidor(bot=bot, server_id=ID_SERVER)

    if servidor is None:
        return None

    miembro = servidor.get_member(usuario_id)

    if miembro is None:
        try:
            miembro = await servidor.fetch_member(usuario_id)

        except NotFound:
            return None

    return miembro


async def obtener_canal_server(bot: commands.Bot, canal_id: int) -> GuildChannel | None:
    canal = bot.get_channel(canal_id)

    if canal is None:
        try:
            canal = await bot.fetch_channel(canal_id)

        except NotFound:
            return None

    if not isinstance(canal, GuildChannel):
        return None

    return canal


async def obtener_canal_mensajes(
    bot: commands.Bot, canal_id: int
) -> TextChannel | Thread | None:

    canal = bot.get_channel(canal_id)

    if canal is None:
        try:
            canal = await bot.fetch_channel(canal_id)

        except NotFound:
            return None

    if not isinstance(canal, (TextChannel, Thread)):
        return None

    return canal


async def obtener_mensaje(
    canal: TextChannel | Thread, mensaje_id: int
) -> Message | None:
    try:
        return await canal.fetch_message(mensaje_id)

    except NotFound:
        return None


async def es_huerfano(id_mensaje: int, id_origen: int, bot: commands.Bot) -> bool:

    origen = await obtener_canal_mensajes(bot, id_origen)
    if origen is None:
        return True

    return await obtener_mensaje(origen, id_mensaje) is None


def es_imagen(attachment: Attachment) -> bool:
    return bool(
        attachment.content_type and attachment.content_type.startswith("image/")
    )


async def crear_hilo(
    nombre: str,
    canal: int | TextChannel,
    bot: commands.Bot,
    mensaje: Message | None = None,
) -> Thread | None:

    if mensaje and isinstance(mensaje.channel, TextChannel):
        creacion_hilo = await mensaje.channel.create_thread(
            name=nombre, message=mensaje, auto_archive_duration=1440
        )
        return creacion_hilo

    elif isinstance(canal, TextChannel):
        creacion_hilo = await canal.create_thread(
            name=nombre, auto_archive_duration=1440, invitable=False
        )
        return creacion_hilo

    else:
        canal_obtenido = await obtener_canal_mensajes(bot, canal)
        if isinstance(canal_obtenido, TextChannel):
            creacion_hilo = await canal_obtenido.create_thread(
                name=nombre, auto_archive_duration=1440, invitable=False
            )
            return creacion_hilo

    return None
