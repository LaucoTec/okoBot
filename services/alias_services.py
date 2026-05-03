from sqlite3 import Row

from discord import Embed, app_commands
from discord.ext.commands import Bot

from config import ID_LOGS_OBRAS
from db import BaseDeDatos
from utils import obtener_canal


def servicio_alias_autocompletar_obra(
    bd: BaseDeDatos,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Obtiene las opciones de obra según el texto ingresado.

    Args:
        bd (BaseDeDatos): Objeto de acceso a los métodos de la base
        current (str): Texto actual en el comando

    Returns:
        list[app_commands.Choice[str]]: Lista de opciones encontradas
    """
    if len(current) < 2:
        todasObras = bd.obras.obtenerObras()
    else:
        resultado = bd.buscarObraPorNombreOAlias(current)
        if resultado:
            todasObras = [resultado]
        else:
            todasObras = bd.obras.buscarObrasPorNombre(current)

    if not todasObras:
        return []

    return [
        app_commands.Choice(name=obra["nombre_obra"], value=obra["nombre_obra"])
        for obra in todasObras[:25]
    ]


def servicio_alias_autocompletar_alias(
    bd: BaseDeDatos,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Obtiene las opciones de alias según el texto ingresado.

    Args:
        bd (BaseDeDatos): Objeto de acceso a los métodos de la base
        current (str): Texto actual en el comando

    Returns:
        list[app_commands.Choice[str]]: Lista de opciones encontradas
    """
    if len(current) < 2:
        todosAliases = bd.aliasObras.obtenerAliasesObras()
    else:
        todosAliases = bd.aliasObras.buscarAliasesPorNombre(current)

    if not todosAliases:
        return []

    return [
        app_commands.Choice(name=alias["alias"], value=alias["alias"])
        for alias in todosAliases[:25]
    ]


def servicio_alias_crear(
    bd: BaseDeDatos, obra: str, alias: str
) -> tuple[str, int | None]:
    """Inserta un alias en la base de datos.

    Args:
        bd (BaseDeDatos): Objeto de acceso a los métodos de la base
        obra (str): Nombre de la obra asociada
        alias (str): Alias a crear

    Returns:
        estado (str): Estado de éxito o fracaso en la ejecución
    """
    estado = "SUCCESS"

    aliases = bd.aliasObras.buscarAliasesPorNombre(nombre_alias=alias)

    if aliases:
        estado = "ERROR_REPEATED"
        return estado, None

    obraData = bd.obras.obtenerObraPorNombre(nombre_obra=obra)

    if obraData is None:
        estado = "ERROR_NOT_FOUND"
        return estado, None

    idAlias = bd.aliasObras.crearAliasObra(alias=alias, id_obra=obraData["id_obra"])

    if idAlias is None:
        estado = "ERROR_NOT_CREATED"

    return estado, idAlias


def servicio_alias_listar_obras(bd: BaseDeDatos) -> tuple[str, list[Row]]:
    estado = "SUCCESS"
    obras = bd.obras.obtenerObras()

    if not obras:
        estado = "ERROR_NOT_FOUND"

    return estado, obras


def servicio_alias_listar_aliases(
    bd: BaseDeDatos, id_obra: int
) -> tuple[str, list[Row]]:
    estado = "SUCCESS"
    aliases = bd.aliasObras.obtenerAliasesObra(id_obra=id_obra)

    if not aliases:
        estado = "ERROR_NOT_FOUND"

    return estado, aliases


async def servicio_alias_log(bot: Bot, embed_log: Embed, accion: str) -> bool:

    canalLog = await obtener_canal(bot=bot, canal_id=ID_LOGS_OBRAS)
    if canalLog is not None:
        if accion == "CREATE":
            mensaje = "Alias creado."
        elif accion == "DELETE":
            mensaje = "Alias eliminado."
        else:
            raise ValueError(f"Acción no válida {accion}")

        await canalLog.send(content=mensaje, embed=embed_log)

        return True
    return False
