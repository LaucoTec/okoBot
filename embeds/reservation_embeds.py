from discord import Color, Embed

from models.reservation_models import DatosReserva
from services.tasks.reservation_state_task import EstadoReserva
from utils.time_utils import fecha_a_str

RESERVATION_COLOR = {
    EstadoReserva.ACTIVA: Color.green(),
    EstadoReserva.POR_EXPIRAR: Color.orange(),
    EstadoReserva.VENCIDA: Color.red(),
}


def embed_reserva(reserva: DatosReserva) -> Embed:
    embed = Embed(
        title=reserva.nombre_personaje, color=RESERVATION_COLOR[reserva.estado]
    )

    embed.description = (
        f"- **__Estado__**: {reserva.estado.value.replace('_', ' ').title()}\n"
        f"- **Fecha de reserva**: {fecha_a_str(reserva.fecha_reserva)}\n"
        f"- **Fecha de expiración**: {fecha_a_str(reserva.fecha_expiracion)}"
    )

    embed.set_author(name=reserva.autor_nombre, icon_url=reserva.autor_icono_url)

    embed.set_footer(text=f"Reserva #{reserva.id_reserva}")

    embed.set_image(url=reserva.enlace_imagen)

    return embed
