from discord import Color, Embed

from embeds.embed_base import AccionesLogs, generico_advertencia, generico_log
from services.tasks.afk_users import ResultadoUsuariosInactivos, UsuarioInactivo


def aviso_previo():
    embed = Embed(title="Recordatorio de limpieza mensual", color=Color.gold())

    embed.description = (
        "**¡Hola a todos! Aquí Feu:** <:oko_buenardo:1334018424547971095> \n\n "
        "Quisiera recordarles que como cada mes, este próximo día primero habrá limpieza.\n"
        "Esto significa que se eliminarán registros que ya no son útiles, como:\n"
        "- Se eliminarán todas aquellas fichas y reservas de personas que ya no están activas en el servidor.\n"
        "- Se purgarán todos los registros relacionados a usuarios que han salido del servidor.\n\n"
        "Mientras que la eliminación es revertible, restaurando la ficha y volviendo a hacer una reserva, es importante mantenerse participando para evitarse molestias. \n"
        "Por el otro lado, la purga **NO** es reversible, y los registros eliminados no podrán ser recuperados.\n\n"
        "Avisados quedan, sigan disfrutando del servidor y nos veremos dentro de unos días. <:oko_buenardo:1334018424547971095>"
    )

    embed.set_footer(
        text="Este mensaje es un aviso automático de Feu, el bot del servidor Okótbika."
    )

    return embed


def log_purga_usuarios_ausentes(resultado) -> Embed:
    usuarios_eliminados = len(resultado.usuarios)
    embed = generico_log(
        accion=AccionesLogs.DELETE,
        titulo=f"Se eliminaron {usuarios_eliminados} usuarios que salieron del servidor.",
        descripcion="".join(
            f"- **Usuario**: ID - {usuario.id}, Nombre - {usuario.nombre}\n"
            for usuario in resultado.usuarios
        ),
        autor=None,
        id_operacion="N/A",
    )

    return embed


def advertencia_usuario_inactivo(usuario: UsuarioInactivo) -> Embed:
    mensaje = (
        "¡Hola! Este es un recordatorio de que has estado inactivo en el servidor durante un tiempo. \n\n"
        "Debido a esto y como parte de las tareas de mantenimiento, tus fichas y reservas han quedado invalidadas.\n"
        "Si desea seguir participando, favor de restaurar sus fichas y volver a hacer sus reservas. De lo contrario, sus registros serán eliminados en los próximos días.\n\n"
        "**Reservas:**\n"
        "".join(f"- {nombre}\n" for nombre in usuario.reservas.values())
        + "\n**Fichas:**\n".join(f"- {nombre}\n" for nombre in usuario.fichas.values())
        + "\n\n"
        "Gracias por su atención y esperamos que continúe disfrutando del servidor."
    )
    embed = generico_advertencia(
        mensaje=mensaje, titulo=f"{usuario.nombre} - Aviso de inactividad"
    )
    return embed


def log_desactivar_usuario_inactivo(
    resultado: ResultadoUsuariosInactivos,
) -> tuple[Embed, Embed, Embed]:
    embed_usuario = generico_log(
        accion=AccionesLogs.EDIT,
        titulo=f"{len(resultado.usuarios)} usuarios inactivos han sido desactivados.",
        descripcion="".join(
            f"- **Usuario**: ID - {usuario.id}, Nombre - {usuario.nombre}\n"
            for usuario in resultado.usuarios
        ),
        autor=None,
        id_operacion="N/A",
    )

    embed_fichas = generico_log(
        accion=AccionesLogs.EDIT,
        titulo=f"Fichas desactivadas: {sum(len(u.fichas) for u in resultado.usuarios)}",
        descripcion="".join(
            f"- **Ficha**: ID - {id_ficha}, Nombre - {nombre}\n"
            for usuario in resultado.usuarios
            for id_ficha, nombre in usuario.fichas.items()
        ),
        autor=None,
        id_operacion="N/A",
    )
    embed_reservas = generico_log(
        accion=AccionesLogs.EDIT,
        titulo=f"Reservas desactivadas: {sum(len(u.reservas) for u in resultado.usuarios)}",
        descripcion="".join(
            f"- **Reserva**: ID - {id_reserva}, Nombre - {nombre}\n"
            for usuario in resultado.usuarios
            for id_reserva, nombre in usuario.reservas.items()
        ),
        autor=None,
        id_operacion="N/A",
    )
    return embed_usuario, embed_fichas, embed_reservas
