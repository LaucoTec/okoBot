from dataclasses import dataclass
from enum import Enum
from sqlite3 import SQLITE_CONSTRAINT_UNIQUE, IntegrityError, Row

from discord import Embed, HTTPException, app_commands
from discord.abc import Messageable
from discord.ext.commands import Bot

from config import ID_LOGS_OBRAS
from db import BaseDeDatos
from logs.loggers import bot_logger
from utils import obtener_canal_mensajes


class EstadoServicioAliasCrear(Enum):
    SUCCESS = "SUCCESS"
    ERROR_TOO_SHORT = "ERROR_TOO_SHORT"
    ERROR_REPEATED = "ERROR_REPEATED"
    ERROR_NOT_FOUND = "ERROR_NOT_FOUND"


class EstadoServicioAliasEliminar(Enum):
    SUCCESS = "SUCCESS"
    ERROR_NOT_FOUND = "ERROR_NOT_FOUND"
    ERROR_DELETION = "ERROR_DELETION"
    ERROR_UNKNOWN = "ERROR_UNKNOWN"


@dataclass
class ResultadoServicioCrearAlias:
    estado: EstadoServicioAliasCrear
    id_alias: int | None

    def __post_init__(self):
        if self.estado is EstadoServicioAliasCrear.SUCCESS and self.id_alias is None:
            raise ValueError("Un resultado exitoso debe contener un id_alias.")

        if (
            self.estado is not EstadoServicioAliasCrear.SUCCESS
            and self.id_alias is not None
        ):
            raise ValueError("Un resultado con error no puede contener un id_alias.")


@dataclass
class ResultadoServicioEliminarAlias:
    estado: EstadoServicioAliasEliminar
    alias_eliminado: str
    id_eliminado: int | None
    obra_asociada: str | None

    def __post_init__(self):
        if self.estado is EstadoServicioAliasEliminar.SUCCESS and (
            self.id_eliminado is None or self.obra_asociada is None
        ):
            raise ValueError(
                "Un resultado exitoso debe contener el id del alias_eliminado y obra_asociada."
            )

        if self.estado is not EstadoServicioAliasEliminar.SUCCESS and (
            self.id_eliminado is not None or self.obra_asociada is not None
        ):
            raise ValueError(
                "Un resultado con error no puede contener el id_eliminado ni obra_asociada."
            )


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
        todasObras = bd.obras.obtener_obras()
    else:
        resultado = bd.buscar_obra_por_nombre_o_alias(current)
        if resultado:
            todasObras = [resultado]
        else:
            todasObras = bd.obras.buscar_obras_por_nombre_normalizado(current)

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
        todosAliases = bd.aliasObras.obtener_aliases_obras()
    else:
        todosAliases = bd.aliasObras.obtener_aliases_por_nombre(current)

    if not todosAliases:
        return []

    return [
        app_commands.Choice(name=alias["alias"], value=alias["alias"])
        for alias in todosAliases[:25]
    ]


def servicio_alias_crear(
    bd: BaseDeDatos, obra: str, alias: str
) -> ResultadoServicioCrearAlias:
    """Inserta un alias en la base de datos.

    Args:
        bd (BaseDeDatos): Objeto de acceso a los métodos de la base
        obra (str): Nombre de la obra asociada
        alias (str): Alias a crear

    Returns:
        ResultadoServicioCrearAlias: Objeto con el estado y el ID del alias creado
    """
    alias = alias.strip()

    if len(alias) < 2:
        return ResultadoServicioCrearAlias(
            estado=EstadoServicioAliasCrear.ERROR_TOO_SHORT, id_alias=None
        )

    aliases = bd.aliasObras.obtener_alias_por_nombre_exacto(nombre_alias=alias)

    if aliases:
        return ResultadoServicioCrearAlias(
            estado=EstadoServicioAliasCrear.ERROR_REPEATED, id_alias=None
        )

    obraData = bd.obras.obtener_obra_por_nombre_normalizado(nombre_obra=obra)

    if obraData is None:
        return ResultadoServicioCrearAlias(
            estado=EstadoServicioAliasCrear.ERROR_NOT_FOUND, id_alias=None
        )
    try:
        idAlias = bd.aliasObras.crear_alias_obra(
            alias=alias, id_obra=obraData["id_obra"]
        )
    except IntegrityError as e:
        if e.sqlite_errorcode == SQLITE_CONSTRAINT_UNIQUE:
            return ResultadoServicioCrearAlias(
                estado=EstadoServicioAliasCrear.ERROR_REPEATED, id_alias=None
            )
        else:
            raise
    return ResultadoServicioCrearAlias(
        estado=EstadoServicioAliasCrear.SUCCESS, id_alias=idAlias
    )


def servicio_alias_eliminar(
    bd: BaseDeDatos, alias: str
) -> ResultadoServicioEliminarAlias:
    """Elimina un alias de la base de datos.

    Args:
        bd (BaseDeDatos): Objeto de acceso a los métodos de la base
        alias (str): Alias a eliminar

    Returns:
        ResultadoServicioEliminarAlias: Objeto con el estado y la información del alias eliminado
    """
    aliasData = bd.aliasObras.obtener_alias_por_nombre_exacto(nombre_alias=alias)

    if not aliasData:
        return ResultadoServicioEliminarAlias(
            estado=EstadoServicioAliasEliminar.ERROR_NOT_FOUND,
            alias_eliminado=alias,
            id_eliminado=None,
            obra_asociada=None,
        )

    obraData = bd.obras.obtener_obra_por_id(id_obra=aliasData["id_obra"])

    if not obraData:
        return ResultadoServicioEliminarAlias(
            estado=EstadoServicioAliasEliminar.ERROR_UNKNOWN,
            alias_eliminado=alias,
            id_eliminado=None,
            obra_asociada=None,
        )

    if not bd.aliasObras.eliminar_alias_obra(aliasData["id_alias"]):
        return ResultadoServicioEliminarAlias(
            estado=EstadoServicioAliasEliminar.ERROR_DELETION,
            alias_eliminado=alias,
            id_eliminado=None,
            obra_asociada=None,
        )

    return ResultadoServicioEliminarAlias(
        estado=EstadoServicioAliasEliminar.SUCCESS,
        alias_eliminado=alias,
        id_eliminado=aliasData["id_alias"],
        obra_asociada=obraData["nombre_obra"],
    )


def servicio_alias_listar_obras(bd: BaseDeDatos) -> list[Row]:
    return bd.obras.obtener_obras()


def servicio_alias_listar_aliases(bd: BaseDeDatos, id_obra: int) -> list[Row]:
    return bd.aliasObras.obtener_aliases_por_id_obra(id_obra=id_obra)


async def servicio_alias_log(bot: Bot, embed_log: Embed, accion: str):

    try:
        canalLog = await obtener_canal_mensajes(bot=bot, canal_id=ID_LOGS_OBRAS)
        if isinstance(canalLog, Messageable):
            if accion == "CREATE":
                mensaje = "Alias creado."
            elif accion == "DELETE":
                mensaje = "Alias eliminado."
            else:
                raise ValueError(f"Acción no válida {accion}")
            await canalLog.send(content=mensaje, embed=embed_log)
    except HTTPException as e:
        bot_logger.error(f"Error al enviar el log de alias: {e}", exc_info=True)
