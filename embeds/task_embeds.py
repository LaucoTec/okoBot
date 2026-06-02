from discord import Embed

from embeds.embed_base import generico_log
from services.tasks.integrity_task import ResultadoIntegridad


def log_integridad_ids(
    registros: ResultadoIntegridad,
) -> tuple[Embed, Embed]:
    fichas_eliminadas = len(registros.fichas_invalidas)
    reservas_eliminadas = len(registros.reservas_invalidas)
    embed_fichas = generico_log(
        accion="DELETE",
        titulo=f"Se eliminaron {fichas_eliminadas} fichas porque sus mensajes y/o hilos ya no existen.",
        descripcion="".join(
            f"- ID Ficha: {registro.id_registro}, Nombre ficha: {registro.nombre}\n"
            for registro in registros.fichas_invalidas
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_reservas = generico_log(
        accion="DELETE",
        titulo=f"Se eliminaron {reservas_eliminadas} reservas porque sus mensajes y/o obras ya no existen.",
        descripcion="".join(
            f"- ID Reserva: {registro.id_registro}, Nombre reserva: {registro.nombre}\n"
            for registro in registros.reservas_invalidas
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed_fichas, embed_reservas
