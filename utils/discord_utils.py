from discord import Attachment, Message, NotFound, TextChannel, Thread, User
from discord.abc import GuildChannel
from discord.ext import commands


async def obtener_usuario(bot: commands.Bot, usuario_id: int) -> User | None:
    usuario = bot.get_user(usuario_id)

    if usuario is None:
        try:
            usuario = await bot.fetch_user(usuario_id)

        except NotFound:
            return None


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
