from config import OkoBot
from models.reservation_models import DatosReserva
from services.tasks.reservation_state_task import EstadoReserva
from utils.discord_utils import obtener_usuario
from utils.time_utils import str_a_fecha


async def obtener_datos_reserva(bot: OkoBot, id_reserva: int) -> DatosReserva | None:
    """
    Obtiene una reserva de la base de datos y construye un objeto DatosReserva
    con la información de la obra y del autor.
    """
    reserva = bot.bd.reservas.obtener_reserva_por_id(id_reserva=id_reserva)
    if reserva is None:
        return None

    obra = bot.bd.obras.obtener_obra_por_id(id_obra=reserva["id_obra"])
    if obra is None:
        return None

    autor = await obtener_usuario(bot=bot, usuario_id=reserva["id_propietario"])
    if autor is None:
        return None

    return DatosReserva(
        id_reserva=reserva["id_reserva"],
        id_propietario=reserva["id_propietario"],
        nombre_personaje=reserva["nombre_personaje"],
        id_obra=reserva["id_obra"],
        nombre_obra=obra["nombre_obra"],
        fecha_reserva=str_a_fecha(reserva["fecha_reserva"]),
        fecha_expiracion=str_a_fecha(reserva["fecha_expiracion"]),
        estado=EstadoReserva(reserva["estado"]),
        enlace_imagen=reserva["enlace_imagen"],
        id_hilo=reserva["id_hilo"],
        id_mensaje=reserva["id_mensaje"],
        autor_nombre=autor.display_name,
        autor_icono_url=autor.display_avatar.url,
    )
