from discord import Color, Embed, User

from .embed_base import (
    generico_advertencia,
    generico_error,
    generico_exito,
    generico_log,
)


def embed_alias_crear(estado: str, obra: str, alias: str) -> Embed:
    if estado.startswith("ERROR"):
        if estado == "ERROR_TOO_SHORT":
            motivo = (
                "El alias provisto es demasiado corto.\nIngrese al menos 2 caracteres."
            )

        elif estado == "ERROR_REPEATED":
            motivo = f"Este alias ya existe para la obra '{obra}'."

        elif estado == "ERROR_NOT_FOUND":
            motivo = f"No se ha encontrado la obra '{obra}'.\nVerifique la información proporcionada."

        elif estado == "ERROR_NOT_CREATED":
            motivo = (
                f"No se ha podido crear el alias '{alias}'.\nIntente de nuevo más tarde"
            )

        else:
            raise ValueError(f"Estado no válido {estado}")

        embed = generico_error(comando="/alias crear", motivo=motivo)

    elif estado == "SUCCESS":
        motivo = f"El alias '{alias}' se ha asociado a {obra} exitosamente."
        embed = generico_exito(mensaje=motivo)
    else:
        raise ValueError(f"Estado no válido {estado}")

    return embed


def embed_alias_listar_inicial(estado: str) -> Embed:
    if estado == "ERROR_NOT_FOUND":
        embed = generico_error(
            comando="/alias listar", motivo="No hay obras disponibles para mostrar."
        )
    elif estado == "SUCCESS":
        embed = generico_exito(mensaje="Selecciona una obra para ver sus alias:")
    else:
        raise ValueError(f"Estado inválido {estado}")

    return embed


def embed_alias_listar(estado: str, obra: str) -> Embed:
    if estado == "ERROR_NOT_FOUND":
        embed = generico_advertencia(
            mensaje="No hay ningún alias asociado a esta obra."
        )
    elif estado == "SUCCESS":
        embed = Embed(title=f"Mostrando aliases para {obra}", color=Color.blue())
    else:
        raise ValueError(f"Estado no válido {estado}")

    return embed


def embed_alias_log(
    accion: str, obra: str, alias: str, autor: User, id_operacion: int
) -> Embed:
    if accion == "CREATE":
        titulo = f"Nuevo alias para obra {obra}"
    elif accion == "DELETE":
        titulo = f"Alias eliminado para obra {obra}"
    else:
        raise ValueError(f"Estado no válido {accion}")

    descripcion = f"- **Alias:** {alias}"
    embed = generico_log(
        accion=accion,
        titulo=titulo,
        descripcion=descripcion,
        autor=autor,
        id_operacion=id_operacion,
    )

    return embed
