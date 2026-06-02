from discord.ext import commands, tasks

from logs.loggers.bot_logger import logger as bot_logger
from services.daily_tasks_services import (
    servicio_integridad_ids,
    servicio_log_integridad_ids,
)
from utils.time_utils import generar_hora_cdmx

# Medianoche hora CDMX
diarias = generar_hora_cdmx(0, 1, 0)
mensuales = generar_hora_cdmx(0, 0, 0)


class TareasCog(commands.Cog):
    """
    Coordina la ejecución periódica de tareas automáticas
    del bot mediante servicios especializados. Divididas
    en tareas diarias y mensuales, se encargan de realizar
    acciones como enviar mensajes programados, limpiar datos
    antiguos, o cualquier otra función que requiera ejecución
    periódica sin intervención manual.
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
    async def Diarias(self):
        bot_logger.info("Ejecutando tareas diarias...")

        try:
            # Ejecutar la tarea de integridad de IDs
            resultado_integridad = await servicio_integridad_ids(self.bot)
            await servicio_log_integridad_ids(self.bot, resultado_integridad)

        except Exception as e:
            bot_logger.error(f"Error al ejecutar tareas diarias: {e}")

    # Se ejecuta mensualmente el día 1 a las 00:00 hora CDMX
    @tasks.loop(time=mensuales)
    async def Mensuales(self): ...  # Lógica para tareas mensuales
