import discord
from discord import app_commands
from discord.app_commands import CommandOnCooldown, MissingRole
from discord.ext import commands

from config import ID_VERIFICADOR, OkoBot
from embeds.alias_embeds import (
    embed_alias_crear,
    embed_alias_eliminar,
    embed_alias_listar_inicial,
    embed_alias_log,
)
from embeds.embed_base import AccionesLogs, generico_error_comando
from logs.loggers.bot_logger import logger as bot_logger
from services.alias_services import (
    EstadoServicioAliasCrear,
    EstadoServicioAliasEliminar,
    servicio_alias_autocompletar_alias,
    servicio_alias_autocompletar_obra,
    servicio_alias_crear,
    servicio_alias_eliminar,
    servicio_alias_listar_obras,
    servicio_alias_log,
)
from views import AliasVista


async def autocompletar_obra(
    interaction: discord.Interaction[OkoBot],
    current: str,
) -> list[app_commands.Choice[str]]:
    bot = interaction.client
    return servicio_alias_autocompletar_obra(bd=bot.bd, current=current)


async def autocompletar_alias(
    interaction: discord.Interaction[OkoBot],
    current: str,
) -> list[app_commands.Choice[str]]:
    bot = interaction.client
    return servicio_alias_autocompletar_alias(bd=bot.bd, current=current)


class AliasCog(commands.Cog):
    """
    Cog para gestionar alias de las obras. Permite a los verificadores crear alias personalizados
    para obras existentes, facilitando su identificación y búsqueda.
    """

    def __init__(self, bot: OkoBot):
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
        resultado = servicio_alias_crear(bd=self.bot.bd, obra=obra, alias=alias)
        embed = embed_alias_crear(estado=resultado.estado, obra=obra, alias=alias)

        await interaction.response.send_message(
            content="Creando un alias...", embed=embed, delete_after=60
        )

        if (
            resultado.estado == EstadoServicioAliasCrear.SUCCESS
            and resultado.id_alias is not None
        ):
            embedLog = embed_alias_log(
                accion=AccionesLogs.CREATE,
                obra=obra,
                alias=alias,
                autor=interaction.user,
                id_operacion=resultado.id_alias,
            )
            await servicio_alias_log(
                bot=self.bot, embed_log=embedLog, accion=AccionesLogs.CREATE
            )

    @aliasGroup.command(name="eliminar", description="Eliminar un alias existente")
    @app_commands.describe(alias="El alias a eliminar")
    @app_commands.autocomplete(alias=autocompletar_alias)
    @app_commands.checks.has_role(ID_VERIFICADOR)
    async def eliminar_alias(self, interaction: discord.Interaction, alias: str):

        resultado = servicio_alias_eliminar(bd=self.bot.bd, alias=alias)

        embed = embed_alias_eliminar(estado=resultado.estado, alias=alias)

        await interaction.response.send_message(
            content="Eliminando un alias...", embed=embed, delete_after=60
        )

        if resultado.estado == EstadoServicioAliasEliminar.SUCCESS:
            if resultado.id_eliminado is None or resultado.obra_asociada is None:
                raise RuntimeError(
                    "Un resultado exitoso de eliminación debe incluir el ID y la obra."
                )

            embedLog = embed_alias_log(
                accion=AccionesLogs.DELETE,
                obra=resultado.obra_asociada,
                alias=alias,
                autor=interaction.user,
                id_operacion=resultado.id_eliminado,
            )
            await servicio_alias_log(
                bot=self.bot, embed_log=embedLog, accion=AccionesLogs.DELETE
            )

    @aliasGroup.command(
        name="listar", description="Listar todos los alias registrados por obra"
    )
    async def listar_aliases(self, interaction: discord.Interaction):
        obras = servicio_alias_listar_obras(bd=self.bot.bd)

        if obras:
            embed = embed_alias_listar_inicial(estado=EstadoServicioAliasCrear.SUCCESS)
        else:
            embed = embed_alias_listar_inicial(
                estado=EstadoServicioAliasCrear.ERROR_NOT_FOUND
            )

        if obras:
            view = AliasVista(bd=self.bot.bd, obras=obras)
            await interaction.response.send_message(
                "Mostrando alias...\n-# Pulsa los botones para ver otras opciones en el menú desplegable.",
                embed=embed,
                view=view,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "No hay alias disponibles para mostrar.",
                embed=embed,
                ephemeral=True,
            )

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):

        if isinstance(error, CommandOnCooldown):
            tiempo = int(error.retry_after)
            minutos = tiempo // 60
            segundos = tiempo % 60
            embed = generico_error_comando(
                descripcion=f"Espere ⏱️ {minutos} minutos con {segundos} segundos antes de usar este comando nuevamente."
            )
        elif isinstance(error, MissingRole):
            embed = generico_error_comando(
                descripcion="Esta acción esta reservada para nuestros Archivistas. 🔎"
            )
        elif isinstance(error, app_commands.CommandInvokeError):
            embed = generico_error_comando(
                descripcion="Ha surgido un error de nuestro lado, lo intentaremos resolver pronto."
            )
            bot_logger.error(
                f"Error no manejado: {error.original}",
                exc_info=(
                    type(error.original),
                    error.original,
                    error.original.__traceback__,
                ),
            )
        else:
            embed = generico_error_comando(
                descripcion="Error desconocido, favor de informar a un administrador."
            )
            bot_logger.error(
                f"Error no manejado: {error}",
                exc_info=(type(error), error, error.__traceback__),
            )
        if not interaction.response.is_done():
            await interaction.response.send_message(
                embed=embed, ephemeral=True, delete_after=20
            )
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AliasCog(bot))
