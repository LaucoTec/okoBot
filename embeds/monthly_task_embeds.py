from discord import Color, Embed

from embeds.embed_base import AccionesLogs, generico_log


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
