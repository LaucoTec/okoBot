from dataclasses import dataclass
from sqlite3 import Row

from config import OkoBot
from utils.discord_utils import es_huerfano


@dataclass
class RegistroInvalido:
    id_registro: int
    nombre: str


@dataclass
class ResultadoIntegridad:
    fichas_invalidas: list[RegistroInvalido]
    reservas_invalidas: list[RegistroInvalido]
    registros_sin_cambio: int = 0


async def _obtener_ids_invalidos(
    bot: OkoBot, campo_id: str, registros: list[Row]
) -> tuple[list[RegistroInvalido], int]:
    """Valida los IDs de mensaje e hilo en los registros dados, y devuelve una lista de IDs de registros que tienen referencias inválidas."""

    if campo_id not in ("id_ficha", "id_reserva"):
        raise ValueError("El campo_id debe ser 'id_ficha' o 'id_reserva'.")

    registros_invalidos = []
    cont = 0

    for registro in registros:
        id_registro = registro[campo_id]
        id_mensaje = registro["id_mensaje"]
        id_hilo = registro["id_hilo"]

        if await es_huerfano(id_mensaje=id_mensaje, id_origen=id_hilo, bot=bot):
            registros_invalidos.append(
                RegistroInvalido(
                    id_registro=id_registro,
                    nombre=registro["nombre_personaje"],
                )
            )
        else:
            cont += 1

    return registros_invalidos, cont


async def _integridad_ids_fichas(bot: OkoBot) -> tuple[list[RegistroInvalido], int]:
    """Reúne los IDs de las fichas con IDs de mensaje e hilo inválidos."""

    fichas = bot.bd.fichas.obtener_fichas()
    fichas_invalidas, cont = await _obtener_ids_invalidos(
        bot=bot, campo_id="id_ficha", registros=fichas
    )

    return fichas_invalidas, cont


async def _integridad_ids_reservas(bot: OkoBot) -> tuple[list[RegistroInvalido], int]:
    """Reúne los IDs de las reservas con IDs de mensaje e hilo inválidos."""

    reservas = bot.bd.reservas.obtener_reservas()
    reservas_invalidas, cont = await _obtener_ids_invalidos(
        bot=bot, campo_id="id_reserva", registros=reservas
    )

    return reservas_invalidas, cont


async def detectar_integridad_ids(bot: OkoBot) -> ResultadoIntegridad:
    """
    Detecta si hay registros de fichas o reservas con IDs de mensaje e hilo inválidos.
    Retorna True si se detectan registros inválidos, False en caso contrario.
    """

    reservas, cont1 = await _integridad_ids_reservas(bot)
    fichas, cont2 = await _integridad_ids_fichas(bot)

    resultado = ResultadoIntegridad(
        fichas_invalidas=fichas,
        reservas_invalidas=reservas,
        registros_sin_cambio=cont1 + cont2,
    )

    return resultado
