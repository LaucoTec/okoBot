from sqlite3 import Row

import discord

from db import BaseDeDatos
from embeds.alias_embeds import embed_alias_listar
from services.alias_services import servicio_alias_listar_aliases


class PaginaBoton(discord.ui.Button):
    def __init__(self, pagina_actual: int, max_pagina: int):
        super().__init__(
            label=f"{pagina_actual + 1}/{max_pagina + 1}",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=1,
        )


class AnteriorBoton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(
            label="◀", style=discord.ButtonStyle.secondary, disabled=disabled, row=1
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        view.paginaActual -= 1
        view.actualizar_vista()

        await interaction.response.edit_message(view=view)


class SiguienteBoton(discord.ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(
            label="▶", style=discord.ButtonStyle.secondary, disabled=disabled, row=1
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        view.paginaActual += 1
        view.actualizar_vista()

        await interaction.response.edit_message(view=view)


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
        estado, aliases = servicio_alias_listar_aliases(bd=self.bd, id_obra=int(idObra))

        embed = embed_alias_listar(estado=estado, obra=obraData["nombre_obra"])

        if estado == "SUCCESS":
            embed.description = f"\n".join([f"- {alias['alias']}" for alias in aliases])

        await interaction.response.edit_message(embed=embed)


class AliasVista(discord.ui.View):
    def __init__(self, bd: BaseDeDatos, obras: list[Row]):
        super().__init__()
        self.bd = bd
        self.obras = obras
        self.paginaActual = 0
        self.obrasPorPagina = 25
        self.actualizar_vista()

    def actualizar_vista(self):
        self.clear_items()

        opciones = self.obtener_obras_actuales()
        seleccionar = ObraSeleccionar(bd=self.bd, obras=opciones)
        seleccionar.row = 0

        self.add_item(seleccionar)

        maxPagina = (len(self.obras) - 1) // self.obrasPorPagina

        anterior = AnteriorBoton(disabled=(self.paginaActual <= 0))
        pagina = PaginaBoton(pagina_actual=self.paginaActual, max_pagina=maxPagina)
        siguiente = SiguienteBoton(disabled=self.paginaActual >= maxPagina)

        self.add_item(anterior)
        self.add_item(pagina)
        self.add_item(siguiente)

    def obtener_obras_actuales(self):
        inicio = self.paginaActual * self.obrasPorPagina
        fin = inicio + self.obrasPorPagina

        return self.obras[inicio:fin]
