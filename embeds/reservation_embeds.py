from discord import Color, Embed

from services.tasks.reservation_state_task import EstadoReserva

RESERVATION_COLOR = {
    EstadoReserva.ACTIVA: Color.green(),
    EstadoReserva.POR_EXPIRAR: Color.orange(),
    EstadoReserva.VENCIDA: Color.red(),
}


def reserva_embed() -> Embed:
    embed = Embed()

    return embed
