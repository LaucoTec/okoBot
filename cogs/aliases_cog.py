import discord
from discord import app_commands
from discord.ext import commands

from config import ID_VERIFICADOR
from services.alias_services import autocompletar_alias, autocompletar_obra
from views.alias_views import AliasVista


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

    async def autocompletar_obra(
        self,
        _: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:

        return autocompletar_obra(bd=self.bot.bd, current=current)

    async def autocompletar_alias(
        self,
        _: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:

        return autocompletar_alias(bd=self.bot.bd, current=current)

    @aliasGroup.command(
        name="crear", description="Crear un alias para una obra existente"
    )
    @app_commands.describe(alias="El alias a crear", obra="El nombre de la obra")
    @app_commands.autocomplete(obra=autocompletar_obra)
    @app_commands.checks.has_role(ID_VERIFICADOR)
    async def crear_alias(
        self, interaction: discord.Interaction, alias: str, obra: str
    ):
        obraData = self.bot.bd.obras.obtenerObraPorNombre(obra)
        if obraData is None:
            await interaction.response.send_message(
                f"No se encontró la obra '{obra}'.", ephemeral=True
            )
            return

        idObra = obraData["id_obra"]
        idAlias = self.bot.bd.aliasObras.crearAliasObra(alias, idObra)

        if idAlias is not None:
            await interaction.response.send_message(
                f"Alias '{alias}' creado para la obra '{obra}'.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Error al crear el alias.", ephemeral=True
            )

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
        obras = self.bot.bd.obras.obtenerObras()
        view = AliasVista(bd=self.bot.bd, obras=obras)
        await interaction.response.send_message(
            "Selecciona una obra para ver sus alias:", view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AliasCog(bot))
