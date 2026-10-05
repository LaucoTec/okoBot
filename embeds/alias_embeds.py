from discord import Color, Embed, Member, User

from embeds.embed_base import (
    AccionesLogs,
    generico_advertencia,
    generico_error,
    generico_exito,
    generico_log,
)
from services.alias_services import (
    EstadoServicioAliasCrear,
    EstadoServicioAliasEliminar,
)


def embed_alias_crear(estado: EstadoServicioAliasCrear, obra: str, alias: str) -> Embed:

    if estado == EstadoServicioAliasCrear.SUCCESS:
        motivo = f"El alias '{alias}' se ha asociado a {obra} exitosamente."
        embed = generico_exito(mensaje=motivo)

    else:
        if estado == EstadoServicioAliasCrear.ERROR_TOO_SHORT:
            motivo = (
                "El alias provisto es demasiado corto.\nIngrese al menos 2 caracteres."
            )

        elif estado == EstadoServicioAliasCrear.ERROR_REPEATED:
            motivo = f"Este alias ya existe para la obra '{obra}'."

        elif estado == EstadoServicioAliasCrear.ERROR_NOT_FOUND:
            motivo = f"No se ha encontrado la obra '{obra}'.\nVerifique la información proporcionada."

        embed = generico_error(comando="/alias crear", motivo=motivo)

    return embed


def embed_alias_eliminar(estado: EstadoServicioAliasEliminar, alias: str) -> Embed:

    if estado == EstadoServicioAliasEliminar.SUCCESS:
        motivo = f"El alias '{alias}' se ha eliminado exitosamente."
        embed = generico_exito(mensaje=motivo)

    else:
        if estado == EstadoServicioAliasEliminar.ERROR_NOT_FOUND:
            motivo = f"No se ha encontrado el alias '{alias}'.\nVerifique la información proporcionada."

        elif estado == EstadoServicioAliasEliminar.ERROR_DELETION:
            motivo = f"No se pudo eliminar el alias '{alias}'.\nIntente nuevamente más tarde."
        elif estado == EstadoServicioAliasEliminar.ERROR_UNKNOWN:
            motivo = f"Se produjo un error desconocido al intentar eliminar el alias '{alias}'.\nIntente nuevamente más tarde."

        embed = generico_error(comando="/alias eliminar", motivo=motivo)

    return embed


def embed_alias_listar_inicial(estado: EstadoServicioAliasCrear) -> Embed:

    if estado == EstadoServicioAliasCrear.SUCCESS:
        embed = generico_exito(mensaje="Selecciona una obra para ver sus alias:")
    else:
        embed = generico_error(
            comando="/alias listar", motivo="No hay obras disponibles para mostrar."
        )

    return embed


def embed_alias_listar(estado: EstadoServicioAliasCrear, obra: str) -> Embed:

    if estado == EstadoServicioAliasCrear.SUCCESS:
        embed = Embed(title=f"Mostrando aliases para {obra}", color=Color.blue())
    else:
        embed = generico_advertencia(
            mensaje="No hay ningún alias asociado a esta obra."
        )

    return embed


def embed_alias_log(
    accion: AccionesLogs, obra: str, alias: str, autor: User | Member, id_operacion: int
) -> Embed:
    if accion == AccionesLogs.CREATE:
        titulo = f"Nuevo alias para obra {obra}"
    elif accion == AccionesLogs.DELETE:
        titulo = f"Alias eliminado para obra {obra}"
    else:
        raise ValueError(f"Estado no válido {accion} para aliases")

    descripcion = f"- **Alias:** {alias}"
    embed = generico_log(
        accion=accion,
        titulo=titulo,
        descripcion=descripcion,
        autor=autor,
        id_operacion=id_operacion,
    )

    return embed
