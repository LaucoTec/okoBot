from discord.ext import commands, tasks

from config import OkoBot
from logs.loggers.bot_logger import logger as bot_logger
from services.daily_tasks_services import (
    servicio_actualizar_estados_reservas,
    servicio_integridad_ids,
    servicio_log_actualizar_estados_reservas,
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
        self.tareas_diarias.start()
        self.tareas_mensuales.start()

    async def cog_unload(self):
        self.tareas_diarias.cancel()
        self.tareas_mensuales.cancel()

    async def tarea_integridad_ids(self):
        try:
            resultado_integridad = await servicio_integridad_ids(self.bot)
            await servicio_log_integridad_ids(self.bot, resultado_integridad)
        except Exception as e:
            bot_logger.error(
                f"Error al ejecutar tarea de integridad: {e}", exc_info=True
            )

    async def tarea_estado_reservas(self):
        try:
            resultado_estados = await servicio_actualizar_estados_reservas(bot=self.bot)
            await servicio_log_actualizar_estados_reservas(
                bot=self.bot, resultado=resultado_estados
            )
        except Exception as e:
            bot_logger.error(
                f"Error al ejecutar tarea de actualización de estados: {e}",
                exc_info=True,
            )

    # Se ejecuta diariamente a las 00:01 hora CDMX
    @tasks.loop(time=diarias)
    async def tareas_diarias(self):
        bot_logger.info("Ejecutando tareas diarias...")

        # Ejecutar la tarea de integridad de IDs
        await self.tarea_integridad_ids()
        await self.tarea_estado_reservas()

    # Se ejecuta mensualmente el día 1 a las 00:00 hora CDMX
    @tasks.loop(time=mensuales)
    async def tareas_mensuales(self): ...  # Lógica para tareas mensuales


async def setup(bot: OkoBot):
    await bot.add_cog(TareasCog(bot))
