from dataclasses import dataclass

from db import BaseDeDatos


@dataclass
class UsuarioInactivo:
    id: int
    nombre: str | None
    fichas: dict[int, str]
    reservas: dict[int, str]


@dataclass
class ResultadoUsuariosInactivos:
    usuarios: list[UsuarioInactivo]


def _obtener_registros_inactivos(
    bd: BaseDeDatos, id: int
) -> tuple[dict[int, str], dict[int, str]]:
    fichas_bd = bd.fichas.obtener_fichas_por_usuario_y_estado(
        id_propietario=id, estado="activa"
    )
    fichas = {ficha["id_ficha"]: ficha["nombre_personaje"] for ficha in fichas_bd}

    reservas_bd = bd.reservas.obtener_reservas_por_usuario_y_estado(
        id_propietario=id, estado="activa"
    )
    reservas = {
        reserva["id_reserva"]: reserva["nombre_personaje"] for reserva in reservas_bd
    }

    return fichas, reservas


def obtener_usuarios_inactivos(bd: BaseDeDatos) -> ResultadoUsuariosInactivos:
    usuarios = bd.usuarios.obtener_usuarios_inactivos(dias=5)
    resultado = []
    for usuario in usuarios:
        fichas, reservas = _obtener_registros_inactivos(bd, usuario["id"])
        resultado.append(
            UsuarioInactivo(
                id=usuario["id"],
                nombre=usuario["nombre"],
                fichas=fichas,
                reservas=reservas,
            )
        )
    return ResultadoUsuariosInactivos(usuarios=resultado)
