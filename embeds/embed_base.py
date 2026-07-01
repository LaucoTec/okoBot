from enum import StrEnum

from discord import Color, Embed, Member, User

from utils import obtener_fecha_cdmx


class AccionesComandos(StrEnum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CONFIRM = "CONFIRM"
    CANCEL = "CANCEL"


class AccionesLogs(StrEnum):
    CREATE = "CREATE"
    EDIT = "EDIT"
    DELETE = "DELETE"


# Colores de comandos
COMMAND_COLOR = {
    AccionesComandos.SUCCESS: Color.brand_green(),
    AccionesComandos.ERROR: Color.greyple(),
    AccionesComandos.CONFIRM: Color.teal(),
    AccionesComandos.CANCEL: Color.dark_red(),
}
# Color de advertencia
WARNING_COLOR = Color.dark_orange()
# Colores de logs
LOG_COLOR = {
    AccionesLogs.CREATE: Color.yellow(),
    AccionesLogs.EDIT: Color.pink(),
    AccionesLogs.DELETE: Color.brand_red(),
}


# --- Comandos---
def generico_exito(mensaje: str) -> Embed:
    return Embed(
        title="Operación completada",
        description=mensaje,
        color=COMMAND_COLOR[AccionesComandos.SUCCESS],
    )


def generico_error(comando: str, motivo: str) -> Embed:
    return Embed(
        title=f"Error ejecutando {comando}",
        description=motivo,
        color=COMMAND_COLOR[AccionesComandos.ERROR],
    )


def generico_confirmar(peticion: str) -> Embed:
    return Embed(
        title="¿Desea continuar?",
        description=peticion,
        color=COMMAND_COLOR[AccionesComandos.CONFIRM],
    )


def generico_cancelar(comando: str) -> Embed:
    return Embed(
        title=comando,
        description="La operación se ha cancelado.",
        color=COMMAND_COLOR[AccionesComandos.CANCEL],
    )


# ---Advertencia---
def generico_advertencia(mensaje: str) -> Embed:
    return Embed(
        title="Revise atentamente antes de continuar",
        description=mensaje,
        color=WARNING_COLOR,
    )


# ---Logs---
def generico_log(
    accion: AccionesLogs,
    titulo: str,
    descripcion: str,
    autor: User | Member | None,
    id_operacion: int | str,
    miniatura: str | None = None,
) -> Embed:

    embed = Embed(title=titulo, description=descripcion)
    if autor is not None:
        embed.set_author(name=autor.display_name, icon_url=autor.display_avatar.url)
    embed.timestamp = obtener_fecha_cdmx()
    embed.set_footer(text=f"ID: {id_operacion}")

    if miniatura is not None:
        embed.set_thumbnail(url=miniatura)

    embed.color = LOG_COLOR[accion]

    return embed
