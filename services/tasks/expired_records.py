from dataclasses import dataclass
from datetime import date

from db import BaseDeDatos
from db.repos import RepoFichas, RepoReservas
from utils.time_utils import str_a_fecha


@dataclass
class RegistroAntiguo:
    id_registro: int
    nombre: str
    fecha_estado: date


@dataclass
class ResultadoLimpiezaRegistros:
    fichas_antiguas: list[RegistroAntiguo]
    reservas_antiguas: list[RegistroAntiguo]
    registros_purgados: int


def _antiguedad_fichas(repo_fichas: RepoFichas, dias: int) -> list[RegistroAntiguo]:
    datos_fichas = repo_fichas.obtener_fichas_eliminadas_antiguas(dias=dias)
    return [
        RegistroAntiguo(
            id_registro=ficha["id_ficha"],
            nombre=ficha["nombre_personaje"],
            fecha_estado=str_a_fecha(ficha["fecha_estado"]),
        )
        for ficha in datos_fichas
    ]


def _antiguedad_reservas(
    repo_reservas: RepoReservas, dias: int
) -> list[RegistroAntiguo]:
    datos_reservas = repo_reservas.obtener_reservas_vencidas_antiguas(dias=dias)
    return [
        RegistroAntiguo(
            id_registro=reserva["id_reserva"],
            nombre=reserva["nombre_personaje"],
            fecha_estado=str_a_fecha(reserva["fecha_estado"]),
        )
        for reserva in datos_reservas
    ]


def detectar_registros_antiguos(
    bd: BaseDeDatos, dias_tolerancia: int
) -> ResultadoLimpiezaRegistros:

    fichas_antiguas = _antiguedad_fichas(repo_fichas=bd.fichas, dias=dias_tolerancia)
    reservas_antiguas = _antiguedad_reservas(
        repo_reservas=bd.reservas, dias=dias_tolerancia
    )
    registros_purgados = len(fichas_antiguas) + len(reservas_antiguas)

    return ResultadoLimpiezaRegistros(
        fichas_antiguas=fichas_antiguas,
        reservas_antiguas=reservas_antiguas,
        registros_purgados=registros_purgados,
    )
