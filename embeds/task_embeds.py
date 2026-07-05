from discord import Embed

from embeds.embed_base import AccionesLogs, generico_log
from services.tasks.integrity_task import ResultadoIntegridad
from services.tasks.purge_expired import ResultadoLimpiezaRegistros
from services.tasks.reservation_state_task import ResultadoActualizacionEstado
from services.tasks.universes_update_task import ResultadoSincronizacionObras


def log_integridad_ids(
    registros: ResultadoIntegridad,
) -> tuple[Embed, Embed]:
    fichas_eliminadas = len(registros.fichas_invalidas)
    reservas_eliminadas = len(registros.reservas_invalidas)
    embed_fichas = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {fichas_eliminadas} fichas porque sus mensajes y/o hilos ya no existen.",
        descripcion="".join(
            f"- **Ficha**: ID - {registro.id_registro}, Nombre - {registro.nombre}\n"
            for registro in registros.fichas_invalidas
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_reservas = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {reservas_eliminadas} reservas porque sus mensajes y/o obras ya no existen.",
        descripcion="".join(
            f"- **Reserva**: ID - {registro.id_registro}, Nombre - {registro.nombre}\n"
            for registro in registros.reservas_invalidas
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed_fichas, embed_reservas


def log_estados_reservas(
    registros: ResultadoActualizacionEstado,
) -> tuple[Embed, Embed]:

    embed_por_expirar = generico_log(
        accion=AccionesLogs.EDIT,
        titulo="Tarea Actualización Estados Reservas - Fichas por expirar hoy",
        descripcion="".join(
            f"- **Reserva**: ID - {reserva.id_reserva}, Nombre - {reserva.nombre_reserva}"
            for reserva in registros.reservas_por_expirar
        ),
        autor=None,
        id_operacion="N/A",
    )
    embed_expiradas = generico_log(
        accion=AccionesLogs.EDIT,
        titulo="Tarea Actualización Estados Reservas - Fichas vencidas hoy",
        descripcion="".join(
            f"- **Reserva**: ID - {reserva.id_reserva}, Nombre - {reserva.nombre_reserva}"
            for reserva in registros.reservas_vencidas
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed_por_expirar, embed_expiradas


def log_sincronizacion_obras(
    registros: ResultadoSincronizacionObras,
) -> tuple[Embed, Embed, Embed]:

    obras_creadas = len(registros.obras_creadas)
    obras_actualizadas = len(registros.obras_actualizadas)
    obras_eliminadas = len(registros.obras_eliminadas)

    embed_creadas = generico_log(
        accion=AccionesLogs.CREATE,
        titulo=f"Se crearon {obras_creadas} en la base de datos.",
        descripcion="".join(
            f"- **Obra**: ID hilo - {creada.id_hilo}, Nombre - {creada.nombre}\n"
            for creada in registros.obras_creadas
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_actualizadas = generico_log(
        accion=AccionesLogs.EDIT,
        titulo=f"Se actualizaron {obras_actualizadas} en la base de datos.",
        descripcion="".join(
            f"- **Obra**: ID - {actualizada.id_obra}, Nombre - ~~{actualizada.nombre_anterior}~~ -> **{actualizada.nombre_nuevo}**\n"
            for actualizada in registros.obras_actualizadas
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_eliminadas = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {obras_eliminadas} en la base de datos.",
        descripcion="".join(
            f"- **Obra**: ID - {eliminada.id_obra}, Nombre - {eliminada.nombre}\n"
            for eliminada in registros.obras_eliminadas
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed_creadas, embed_actualizadas, embed_eliminadas


def log_purga_registros(
    registros: ResultadoLimpiezaRegistros,
) -> tuple[Embed, Embed]:
    fichas_eliminadas = len(registros.fichas_antiguas)
    reservas_eliminadas = len(registros.reservas_antiguas)

    embed_fichas = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {fichas_eliminadas} fichas antiguas.",
        descripcion="".join(
            f"- **Ficha**: ID - {registro.id_registro}, Nombre - {registro.nombre}, Fecha estado - {registro.fecha_estado}\n"
            for registro in registros.fichas_antiguas
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_reservas = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {reservas_eliminadas} reservas antiguas.",
        descripcion="".join(
            f"- **Reserva**: ID - {registro.id_registro}, Nombre - {registro.nombre}, Fecha estado - {registro.fecha_estado}\n"
            for registro in registros.reservas_antiguas
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed_fichas, embed_reservas
