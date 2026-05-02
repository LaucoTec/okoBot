import discord
from discord.ext import commands


async def obtener_canal(
    bot: commands.Bot, canalID: int
) -> discord.abc.GuildChannel | discord.Thread | None:

    canal = bot.get_channel(canalID)

    if canal is None:
        try:
            canal = await bot.fetch_channel(canalID)

        except discord.NotFound:
            return None

    return canal


async def obtener_mensaje(
    canal: discord.TextChannel | discord.Thread, mensajeID: int
) -> discord.Message | None:
    try:
        return await canal.fetch_message(mensajeID)

    except discord.NotFound:
        return None


def es_imagen(attachment: discord.Attachment) -> bool:
    return bool(
        attachment.content_type and attachment.content_type.startswith("image/")
    )
