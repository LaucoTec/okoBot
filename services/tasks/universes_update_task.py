from dataclasses import dataclass

from discord import ForumChannel

from config import ID_REPOSITORIO, OkoBot
from utils.discord_utils import obtener_canal_server


@dataclass
class ObraCreada:
    id_hilo: int
    nombre: str


@dataclass
class ObraActualizada:
    id_obra: int
    nombre_anterior: str
    nombre_nuevo: str


@dataclass
class ObraEliminada:
    id_obra: int
    nombre: str


@dataclass
class ResultadoSincronizacionObras:
    obras_creadas: list[ObraCreada]
    obras_actualizadas: list[ObraActualizada]
    obras_eliminadas: list[ObraEliminada]


def determinar_cambios_obras(
    obras: dict[int, str], hilos: dict[int, str]
) -> tuple[set[int], set[int], set[int]]:

    creadas = hilos.keys() - obras.keys()

    eliminadas = obras.keys() - hilos.keys()

    temp = obras.keys() & hilos.keys()
    actualizadas = {id_hilo for id_hilo in temp if obras[id_hilo] != hilos[id_hilo]}

    return (creadas, eliminadas, actualizadas)


async def detectar_actualizaciones_obras(bot: OkoBot) -> ResultadoSincronizacionObras:

    resultado = ResultadoSincronizacionObras(
        obras_creadas=[], obras_eliminadas=[], obras_actualizadas=[]
    )

    canal = await obtener_canal_server(bot=bot, canal_id=ID_REPOSITORIO)
    if not canal or not isinstance(canal, ForumChannel):
        raise ValueError("No se encontró el canal de foro indicado.")

    hilos_actuales = {hilo.id: hilo.name for hilo in canal.threads}

    obras = bot.bd.obras.obtener_obras()
    obras_actuales = {obra["id_hilo"]: obra["nombre_obra"] for obra in obras}
    obras_ids = {obra["id_hilo"]: obra["id_obra"] for obra in obras}

    creadas, eliminadas, actualizadas = determinar_cambios_obras(
        obras=obras_actuales, hilos=hilos_actuales
    )

    for id_hilo in creadas:
        resultado.obras_creadas.append(
            (
                ObraCreada(
                    nombre=hilos_actuales[id_hilo],
                    id_hilo=id_hilo,
                )
            )
        )

    for id_hilo in actualizadas:
        resultado.obras_actualizadas.append(
            ObraActualizada(
                id_obra=obras_ids[id_hilo],
                nombre_anterior=obras_actuales[id_hilo],
                nombre_nuevo=hilos_actuales[id_hilo],
            )
        )

    for id_hilo in eliminadas:
        resultado.obras_eliminadas.append(
            ObraEliminada(id_obra=obras_ids[id_hilo], nombre=obras_actuales[id_hilo])
        )

    return resultado
