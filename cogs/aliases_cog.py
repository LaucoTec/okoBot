import discord
from discord import app_commands
from discord.ext import commands

from config import ID_VERIFICADOR
from embeds.alias_embeds import (
    embed_alias_crear,
    embed_alias_listar_inicial,
    embed_alias_log,
)
from services.alias_services import (
    servicio_alias_autocompletar_alias,
    servicio_alias_autocompletar_obra,
    servicio_alias_crear,
    servicio_alias_listar_obras,
    servicio_alias_log,
)
from views import AliasVista


async def autocompletar_obra(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    bot = interaction.client
    return servicio_alias_autocompletar_obra(bd=bot.bd, current=current)


async def autocompletar_alias(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    bot = interaction.client
    return servicio_alias_autocompletar_alias(bd=bot.bd, current=current)


class AliasCog(commands.Cog):
    """
    Cog para gestionar alias de las obras. Permite a los verificadores crear alias personalizados
    para obras existentes, facilitando su identificación y búsqueda.
    """

    def __init__(self, bot):
        self.bot = bot

    aliasGroup = app_commands.Group(
        name="alias", description="Comandos para gestionar alias de obras"
    )

    @aliasGroup.command(
        name="crear", description="Crear un alias para una obra existente"
    )
    @app_commands.describe(alias="El alias a crear", obra="El nombre de la obra")
    @app_commands.autocomplete(obra=autocompletar_obra)
    @app_commands.checks.has_role(ID_VERIFICADOR)
    async def crear_alias(
        self, interaction: discord.Interaction, obra: str, alias: str
    ):
        estado, idAlias = servicio_alias_crear(bd=self.bot.bd, obra=obra, alias=alias)
        embed = embed_alias_crear(estado=estado, obra=obra, alias=alias)

        await interaction.response.send_message(
            content="Creando un alias...", embed=embed, delete_after=60
        )

        if estado == "SUCCESS":
            embedLog = embed_alias_log(
                accion="CREATE",
                obra=obra,
                alias=alias,
                autor=interaction.user,
                id_operacion=idAlias,
            )
            await servicio_alias_log(bot=self.bot, embed_log=embedLog, accion="CREATE")

    @aliasGroup.command(name="eliminar", description="Eliminar un alias existente")
    @app_commands.describe(alias="El alias a eliminar")
    @app_commands.autocomplete(alias=autocompletar_alias)
    @app_commands.checks.has_role(ID_VERIFICADOR)
    async def eliminar_alias(self, interaction: discord.Interaction, alias: str):
        aliasData = self.bot.bd.aliasObras.obtenerObraPorAlias(alias)
        if aliasData is None:
            await interaction.response.send_message(
                f"No se encontró el alias '{alias}'.", ephemeral=True
            )
            return

        idAlias = aliasData["id_alias"]
        self.bot.bd.aliasObras.eliminarAliasObra(idAlias)
        await interaction.response.send_message(
            f"Alias '{alias}' eliminado.", ephemeral=True
        )

    @aliasGroup.command(
        name="listar", description="Listar todos los alias registrados por obra"
    )
    async def listar_aliases(self, interaction: discord.Interaction):
        estado, obras = servicio_alias_listar_obras(bd=self.bot.bd)

        embed = embed_alias_listar_inicial(estado=estado)

        view = AliasVista(bd=self.bot.bd, obras=obras)
        await interaction.response.send_message(
            "Mostrando alias...\n-# Pulsa los botones para ver otras opciones en el menú desplegable.",
            embed=embed,
            view=(view if estado == "SUCCESS" else None),
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(AliasCog(bot))
