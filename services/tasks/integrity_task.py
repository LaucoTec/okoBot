from dataclasses import dataclass
from sqlite3 import Row

from config import OkoBot
from utils.discord_utils import es_huerfano


@dataclass
class RegistroInvalido:
    id_registro: int
    tipo: str  # "ficha" o "reserva"
    nombre: str  # Nombre de la ficha o reserva para facilitar identificación


@dataclass
class ResultadoIntegridad:
    fichas_invalidas: list[RegistroInvalido]
    reservas_invalidas: list[RegistroInvalido]


async def obtener_ids_invalidos(
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
                    tipo=campo_id.replace("id_", ""),
                    nombre=registro["nombre_personaje"],
                )
            )

    return registros_invalidos


async def integridad_ids_fichas(bot: OkoBot) -> list[RegistroInvalido]:
    """Reúne los IDs de las fichas con IDs de mensaje e hilo inválidos."""

    fichas = bot.bd.fichas.obtener_fichas()
    fichas_invalidas = await obtener_ids_invalidos(
        bot=bot, campo_id="id_ficha", registros=fichas
    )

    return fichas_invalidas


async def integridad_ids_reservas(bot: OkoBot) -> list[RegistroInvalido]:
    """Reúne los IDs de las reservas con IDs de mensaje e hilo inválidos."""

    reservas = bot.bd.reservas.obtener_reservas()
    reservas_invalidas = await obtener_ids_invalidos(
        bot=bot, campo_id="id_reserva", registros=reservas
    )

    return reservas_invalidas
