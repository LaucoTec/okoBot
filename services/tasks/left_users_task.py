from dataclasses import dataclass

from config import OkoBot
from utils.discord_utils import obtener_miembro, obtener_usuario


@dataclass
class UsuariosAusentes:
    id: int
    nombre: str | None


@dataclass
class ResultadoUsuariosAusentes:
    usuarios: list[UsuariosAusentes]


async def obtener_usuarios_ausentes(bot: OkoBot) -> ResultadoUsuariosAusentes:

    usuarios = bot.bd.usuarios.obtener_usuarios()
    usuarios_ausentes = []

    for usuario in usuarios:
        if not await obtener_miembro(bot, usuario["id_usuario"]):
            ausente = await obtener_usuario(bot, usuario["id_usuario"])
            if ausente:
                usuarios_ausentes.append(
                    UsuariosAusentes(id=ausente.id, nombre=ausente.name)
                )
            else:
                usuarios_ausentes.append(
                    UsuariosAusentes(id=usuario["id_usuario"], nombre=None)
                )

    resultado = ResultadoUsuariosAusentes(usuarios=usuarios_ausentes)

    return resultado
