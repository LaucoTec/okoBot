from discord import Color, Embed, Member, User

from utils import obtener_fecha_cdmx

# Colores de comandos
COMMAND_COLOR = {
    "SUCCESS": Color.brand_green(),
    "ERROR": Color.greyple(),
    "CONFIRM": Color.teal(),
    "CANCEL": Color.dark_red(),
}
# Color de advertencia
WARNING_COLOR = Color.dark_orange()
# Colores de logs
LOG_COLOR = {
    "CREATE": Color.yellow(),
    "EDIT": Color.pink(),
    "DELETE": Color.brand_red(),
}


# --- Comandos---
def generico_exito(mensaje: str) -> Embed:
    return Embed(
        title="Operación completada",
        description=mensaje,
        color=COMMAND_COLOR["SUCCESS"],
    )


def generico_error(comando: str, motivo: str) -> Embed:
    return Embed(
        title=f"Error ejecutando {comando}",
        description=motivo,
        color=COMMAND_COLOR["ERROR"],
    )


def generico_confirmar(peticion: str) -> Embed:
    return Embed(
        title="¿Desea continuar?", description=peticion, color=COMMAND_COLOR["CONFIRM"]
    )


def generico_cancelar(comando: str) -> Embed:
    return Embed(
        title=comando,
        description="La operación se ha cancelado.",
        color=COMMAND_COLOR["CANCEL"],
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
    accion: str,
    titulo: str,
    descripcion: str,
    autor: User | Member,
    id_operacion: int,
    miniatura: str | None = None,
) -> Embed:
    embed = Embed(title=titulo, description=descripcion)
    embed.set_author(name=autor.display_name, icon_url=autor.display_avatar.url)
    embed.timestamp = obtener_fecha_cdmx()
    embed.set_footer(text=f"ID: {id_operacion}")

    if miniatura is not None:
        embed.set_thumbnail(url=miniatura)

    try:
        embed.color = LOG_COLOR[accion]
    except KeyError:
        raise ValueError(f"Acción no válida {accion}")

    return embed
