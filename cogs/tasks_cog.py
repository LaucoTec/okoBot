from discord.ext import commands, tasks

from config import OkoBot
from logs.loggers.bot_logger import logger as bot_logger
from services.daily_tasks_services import (
    servicio_actualizar_estados_reservas,
    servicio_integridad_ids,
    servicio_log_actualizar_estados_reservas,
    servicio_log_integridad_ids,
    servicio_log_purgar_registros_antiguos,
    servicio_log_sincronizar_obras,
    servicio_purgar_registros_antiguos,
    servicio_sincronizar_obras,
)
from services.montly_tasks_services import (
    servicio_desactivar_usuarios_inactivos,
    servicio_enviar_aviso_pre_mensual,
    servicio_log_desactivar_usuarios_inactivos,
    servicio_log_purgar_usuarios_ausentes,
    servicio_purgar_usuarios_ausentes,
)
from utils.time_utils import generar_hora_cdmx, obtener_fecha_cdmx

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

    def __init__(self, bot: OkoBot):
        self.bot = bot
        self.tareas_diarias.start()
        self.tareas_mensuales.start()
        self.aviso_pre_mensual.start()

    async def cog_unload(self):
        self.tareas_diarias.cancel()
        self.tareas_mensuales.cancel()
        self.aviso_pre_mensual.cancel()

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

    async def tarea_sincronizacion_obras(self):
        try:
            resultado_sincronizacion = await servicio_sincronizar_obras(bot=self.bot)
            await servicio_log_sincronizar_obras(
                bot=self.bot, resultado=resultado_sincronizacion
            )
        except Exception as e:
            bot_logger.error(
                f"Error al ejecutar tarea de sinronización de obras: {e}", exc_info=True
            )

    async def tarea_purgar_registros_antiguos(self):
        try:
            resultado_purga = servicio_purgar_registros_antiguos(
                bd=self.bot.bd, dias_tolerancia=7
            )
            await servicio_log_purgar_registros_antiguos(
                bot=self.bot, resultado=resultado_purga
            )
        except Exception as e:
            bot_logger.error(
                f"Error al ejecutar tarea de purga de registros antiguos: {e}",
                exc_info=True,
            )

    def tarea_actividad_diaria(self):
        bot_logger.info("--Reiniciando conteo de actividad diaria...")
        self.bot.conteoMensajes.clear()

    async def tarea_aviso_pre_mensual(self):
        bot_logger.info("--Enviando aviso pre-mensual...")

        await servicio_enviar_aviso_pre_mensual(self.bot)

    async def tarea_purgar_usuarios_ausentes(self):

        resultado = await servicio_purgar_usuarios_ausentes(self.bot)
        await servicio_log_purgar_usuarios_ausentes(self.bot, resultado)

    async def tarea_desactivar_usuarios_inactivos(self):

        resultado = await servicio_desactivar_usuarios_inactivos(self.bot)
        await servicio_log_desactivar_usuarios_inactivos(self.bot, resultado)

    # Se ejecuta diariamente a las 00:01 hora CDMX
    @tasks.loop(time=diarias)
    async def tareas_diarias(self):
        bot_logger.info("Ejecutando tareas diarias...")

        # Ejecutar la tarea de integridad de IDs
        await self.tarea_integridad_ids()
        # Ejecutar la tarea de actualización de estados de reservas
        await self.tarea_estado_reservas()
        # Ejecutar la tarea de sincronización de obras
        await self.tarea_sincronizacion_obras()
        # Ejecutar la tarea de purga de registros antiguos
        await self.tarea_purgar_registros_antiguos()
        # Reiniciar el conteo de actividad diaria
        self.tarea_actividad_diaria()

    # Se ejecuta a las 00:00 hora CDMX el día 28 de cada mes
    @tasks.loop(time=mensuales)
    async def aviso_pre_mensual(self):
        # Ejecutar sólo si es día 28 del mes
        if obtener_fecha_cdmx().day != 28:
            return
        await self.tarea_aviso_pre_mensual()

    # Se ejecuta mensualmente el día 1 a las 00:00 hora CDMX
    @tasks.loop(time=mensuales)
    async def tareas_mensuales(self):
        if obtener_fecha_cdmx().day != 1:
            return
        bot_logger.info("Ejecutando tareas mensuales...")

        # Ejecutar la tarea de purga de usuarios ausentes
        await self.tarea_purgar_usuarios_ausentes()
        # Ejecutar la tarea de desactivación de usuarios inactivos
        await self.tarea_desactivar_usuarios_inactivos()

    @tareas_diarias.error
    async def tareas_diarias_error(self, error: BaseException):
        bot_logger.error(
            "Error inesperado en el loop de tareas diarias.",
            exc_info=(type(error), error, error.__traceback__),
        )

    @aviso_pre_mensual.error
    async def aviso_pre_mensual_error(self, error: BaseException):
        bot_logger.error(
            "Error inesperado en el loop de aviso pre-mensual.",
            exc_info=(type(error), error, error.__traceback__),
        )

    @tareas_mensuales.error
    async def tareas_mensuales_error(self, error: BaseException):
        bot_logger.error(
            "Error inesperado en el loop de tareas mensuales.",
            exc_info=(type(error), error, error.__traceback__),
        )


async def setup(bot: OkoBot):
    await bot.add_cog(TareasCog(bot))
