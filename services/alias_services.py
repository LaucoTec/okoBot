from sqlite3 import Row

from discord import app_commands

from db import BaseDeDatos


def autocompletar_obra(
    bd: BaseDeDatos,
    current: str,
) -> list[app_commands.Choice[str]]:
    """
    Sugiere obras existentes conforme escribe.
    - Retorna:
      - app_commands.Choice con hasta 25 opciones.
    """
    if len(current) < 3:
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


def autocompletar_alias(
    bd: BaseDeDatos,
    current: str,
) -> list[app_commands.Choice[str]]:
    """
    Sugiere aliases existentes conforme escribe.
    - Retorna:
      - app_commands.Choice con hasta 25 opciones.
    """
    if len(current) < 3:
        todosAliases = bd.aliasObras.obtenerAliasesObras()
    else:
        todosAliases = bd.aliasObras.buscarAliasesPorNombre(current)

    if not todosAliases:
        return []

    return [
        app_commands.Choice(name=alias["alias"], value=alias["alias"])
        for alias in todosAliases[:25]
    ]


def obtener_aliases(bd: BaseDeDatos, id_obra: str) -> list[Row]:
    return bd.aliasObras.obtenerAliasesObra(int(id_obra))
