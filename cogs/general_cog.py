import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="Repite el mensaje que le des")
    @app_commands.describe(mensaje="Texto a repetir.")
    async def say(self, interaction: discord.Interaction, mensaje: str):
        await interaction.response.send_message(mensaje + " 🔥")


async def setup(bot):
    await bot.add_cog(General(bot))
