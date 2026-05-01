from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from config import ID_VERIFICADOR


class ObraSelec(discord.ui.Select):
    def __init__(self, obras):
        self.obras = {str(o["id_obra"]): o for o in obras}
        options = [
            discord.SelectOption(label=o["nombre_obra"], value=str(o["id_obra"]))
            for o in obras[:25]
        ]

        super().__init__(placeholder="Selecciona una obra", options=options)

    async def callback(self, interaction: discord.Interaction):
        idObra = self.values[0]
        obraData = self.obras[idObra]
        aliases = self.view.bot.bd.aliasObras.obtenerAliasesObra(idObra)

        if not aliases:
            await interaction.response.send_message(
                f"No hay alias registrados para la obra '{obraData['nombre_obra']}'.",
                ephemeral=True,
            )
            return

        mensaje = f"\n".join([f"- {alias['alias']}" for alias in aliases])
        mensaje = discord.Embed(
            title=f"Alias de {obraData['nombre_obra']}",
            description=mensaje,
            color=discord.Color.blue(),
        )
        await interaction.response.edit_message(
            content=f"Mostrando {len(aliases)} alias.", embed=mensaje
        )


class AliasVista(discord.ui.View):
    def __init__(self, bot, obras):
        super().__init__()
        self.bot = bot
        self.add_item(ObraSelec(obras))


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

    async def autocompletarObra(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Sugiere obras existentes conforme escribe."""
        if len(current) < 3:
            todasObras = self.bot.bd.obras.obtenerObras()
        else:
            resultado = self.bot.bd.buscarObraPorNombreOAlias(current)
            if resultado:
                todasObras = [resultado]
            else:
                todasObras = self.bot.bd.obras.buscarObrasPorNombre(current)

        if not todasObras:
            return []

        return [
            app_commands.Choice(name=obra["nombre_obra"], value=obra["nombre_obra"])
            for obra in todasObras[:25]
        ]

    async def autocompletarAlias(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Sugiere alias existentes conforme escribe."""
        if len(current) < 3:
            todosAliases = self.bot.bd.aliasObras.obtenerAliasesObras()
        else:
            todosAliases = self.bot.bd.aliasObras.buscarAliasesPorNombre(current)

        if not todosAliases:
            return []

        return [
            app_commands.Choice(name=alias["alias"], value=alias["alias"])
            for alias in todosAliases[:25]
        ]

    @aliasGroup.command(
        name="crear", description="Crear un alias para una obra existente"
    )
    @app_commands.describe(alias="El alias a crear", obra="El nombre de la obra")
    @app_commands.autocomplete(obra=autocompletarObra)
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
    @app_commands.autocomplete(alias=autocompletarAlias)
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
    @app_commands.describe()
    async def listar_aliases(self, interaction: discord.Interaction):
        obras = self.bot.bd.obras.obtenerObras()
        view = AliasVista(self.bot, obras)
        await interaction.response.send_message(
            "Selecciona una obra para ver sus alias:", view=view, ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(AliasCog(bot))
