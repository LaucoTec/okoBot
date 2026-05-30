import discord
from discord.ext import commands


async def obtener_canal(
    bot: commands.Bot, canal_id: int
) -> discord.abc.GuildChannel | None:

    canal = bot.get_channel(canal_id)

    if canal is None:
        try:
            canal = await bot.fetch_channel(canal_id)

        except discord.NotFound:
            return None

    if not isinstance(canal, discord.abc.GuildChannel):
        return None

    return canal


async def obtener_hilo(bot: commands.Bot, hilo_id: int) -> discord.Thread | None:
    hilo = bot.get_channel(hilo_id)

    if hilo is None:
        try:
            hilo = await bot.fetch_channel(hilo_id)

        except discord.NotFound:
            return None

    if not isinstance(hilo, discord.Thread):
        return None

    return hilo


async def obtener_mensaje(
    canal: discord.TextChannel | discord.Thread, mensaje_id: int
) -> discord.Message | None:
    try:
        return await canal.fetch_message(mensaje_id)

    except discord.NotFound:
        return None


def es_imagen(attachment: discord.Attachment) -> bool:
    return bool(
        attachment.content_type and attachment.content_type.startswith("image/")
    )
