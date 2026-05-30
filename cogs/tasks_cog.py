from discord.ext import commands, tasks

from utils.time_utils import generar_hora_cdmx

# Medianoche hora CDMX
diarias = generar_hora_cdmx(0, 1, 0)
mensuales = generar_hora_cdmx(0, 0, 0)


class TareasCog(commands.Cog):
    """
    Cog para gestionar tareas programadas diarias y mensuales. Se encarga de:
    - Diarias: Actualizar obras del foro, actualizar estados de reservas por expiración,
    eliminar registros con IDs inválidos, borrar hilos de fichas eliminadas
    hace más de 7 días, eliminar reservas vencidas antiguas.
    - Mensuales: Eliminar usuarios que abandonaron el servidor, marcar fichas
    y reservas de usuarios inactivos como eliminadas/vencidas.
    """

    def __init__(self, bot):
        self.bot = bot
        self.Diarias.start()
        self.Mensuales.start()

    async def cog_unload(self):
        self.Diarias.cancel()
        self.Mensuales.cancel()

    # Se ejecuta diariamente a las 00:01 hora CDMX
    @tasks.loop(time=diarias)
    async def Diarias(self): ...  # Lógica para tareas diarias

    # Se ejecuta mensualmente el día 1 a las 00:00 hora CDMX
    @tasks.loop(time=mensuales)
    async def Mensuales(self): ...  # Lógica para tareas mensuales
