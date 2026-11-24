from dataclasses import dataclass
from sqlite3 import Row

from config import OkoBot
from models.db_models import SincronizacionFicha, SincronizacionReserva
from utils.discord_utils import es_huerfano


@dataclass
class RegistroInvalido:
    id_registro: int
    nombre: str


@dataclass
class ResultadoIntegridad:
    fichas_invalidas: list[RegistroInvalido]
    reservas_invalidas: list[RegistroInvalido]


async def _obtener_ids_invalidos(
    bot: OkoBot, campo_id: str, registros: list[Row]
) -> list[RegistroInvalido]:
    """Valida los IDs de mensaje e hilo en los registros dados, y devuelve una lista de IDs de registros que tienen referencias inválidas."""

    if campo_id not in ("id_ficha", "id_reserva"):
        raise ValueError("El campo_id debe ser 'id_ficha' o 'id_reserva'.")

    registros_invalidos = []

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

        if registro["sincronizado"] in [
            SincronizacionFicha.SIN_ID_MENSAJE,
            SincronizacionFicha.REFERENCIA_INVALIDA,
            SincronizacionReserva.SIN_ID_MENSAJE,
            SincronizacionReserva.REFERENCIA_INVALIDA,
        ]:
            registros_invalidos.append(
                RegistroInvalido(
                    id_registro=id_registro,
                    nombre=registro["nombre_personaje"],
                )
            )

    return registros_invalidos


async def _integridad_ids_fichas(bot: OkoBot) -> list[RegistroInvalido]:
    """Reúne los IDs de las fichas con IDs de mensaje e hilo inválidos."""

    fichas = bot.bd.fichas.obtener_fichas()
    fichas_invalidas = await _obtener_ids_invalidos(
        bot=bot, campo_id="id_ficha", registros=fichas
    )

    return fichas_invalidas


async def _integridad_ids_reservas(bot: OkoBot) -> list[RegistroInvalido]:
    """Reúne los IDs de las reservas con IDs de mensaje e hilo inválidos."""

    reservas = bot.bd.reservas.obtener_reservas()
    reservas_invalidas = await _obtener_ids_invalidos(
        bot=bot, campo_id="id_reserva", registros=reservas
    )

    return reservas_invalidas


async def detectar_integridad_ids(bot: OkoBot) -> ResultadoIntegridad:
    """
    Detecta si hay registros de fichas o reservas con IDs de mensaje e hilo inválidos.
    Retorna True si se detectan registros inválidos, False en caso contrario.
    """

    reservas = await _integridad_ids_reservas(bot)
    fichas = await _integridad_ids_fichas(bot)

    resultado = ResultadoIntegridad(
        fichas_invalidas=fichas, reservas_invalidas=reservas
    )

    return resultado
