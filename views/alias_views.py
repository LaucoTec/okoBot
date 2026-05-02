from sqlite3 import Row

import discord

from db import BaseDeDatos
from services import obtener_aliases


class ObraSeleccionar(discord.ui.Select):
    def __init__(self, bd: BaseDeDatos, obras: list[Row]):
        self.bd = bd
        self.obras = {str(o["id_obra"]): o for o in obras}
        options = [
            discord.SelectOption(label=o["nombre_obra"], value=str(o["id_obra"]))
            for o in obras[:25]
        ]

        super().__init__(placeholder="Selecciona una obra", options=options)

    async def callback(self, interaction: discord.Interaction):
        idObra = self.values[0]
        obraData = self.obras[idObra]
        aliases = obtener_aliases(bd=self.bd, id_obra=idObra)

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
    def __init__(self, bd: BaseDeDatos, obras: list[Row]):
        super().__init__()
        self.add_item(ObraSeleccionar(bd=bd, obras=obras))
