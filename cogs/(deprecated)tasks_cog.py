from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from config import ID_ADVERTENCIAS, ID_LOGS_RESERVAS, ID_RESERVAS
from logs.loggers.db_logger import logger

# Medianoche hora CDMX
diarias = time(hour=0, minute=1, second=0, tzinfo=ZoneInfo("America/Mexico_City"))
medianoche = time(hour=0, minute=0, second=0, tzinfo=ZoneInfo("America/Mexico_City"))


class TareasProgramadas(commands.Cog):
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

    async def actualizarObras(self):
        print("Actualizando obras...")
        # Obtener hilos del canal de reservas y sus IDs
        canalReservas = self.bot.get_channel(ID_RESERVAS)
        hilos = canalReservas.threads
        nombresHilos = [hilo.name for hilo in hilos]
        idsHilos = [hilo.id for hilo in hilos]

        # Agregar obras a la base de datos si no existen
        for nombre, id_hilo in zip(nombresHilos, idsHilos):
            obra = self.bot.bd.obras.obtenerObraPorHilo(id_hilo)
            if obra is None:
                logger.info(f"Creando obra '{nombre}' con hilo {id_hilo}")
                self.bot.bd.obras.crearObra(nombre, id_hilo)

    async def integridadIDs(self):
        logger.info("Verificando integridad de IDs en fichas y reservas...")

        fichas = self.bot.bd.fichas.obtenerTodasFichas()
        eliminadas_fichas = 0
        for ficha in fichas:
            if not await self._ids_validos(ficha["id_hilo"], ficha["id_mensaje"]):
                if self.bot.bd.fichas.eliminarFichaDefinitiva(ficha["id_ficha"]):
                    eliminadas_fichas += 1
                    logger.info(
                        f"Eliminada ficha inválida id_ficha={ficha['id_ficha']} id_hilo={ficha['id_hilo']} id_mensaje={ficha['id_mensaje']}"
                    )

        reservas = self.bot.bd.reservas.obtenerTodasReservas()
        eliminadas_reservas = 0
        for reserva in reservas:
            if not await self._ids_validos(reserva["id_hilo"], reserva["id_mensaje"]):
                if self.bot.bd.reservas.eliminarReservaDefinitiva(
                    reserva["id_reserva"]
                ):
                    eliminadas_reservas += 1
                    logger.info(
                        f"Eliminada reserva inválida id_reserva={reserva['id_reserva']} id_hilo={reserva['id_hilo']} id_mensaje={reserva['id_mensaje']}"
                    )

        logger.info(
            f"Integridad de IDs completada: {eliminadas_fichas} fichas eliminadas, {eliminadas_reservas} reservas eliminadas."
        )

    async def actualizarEstadosReservas(self):
        logger.info("Actualizando estados de reservas por fecha de expiración...")

        reservas = self.bot.bd.reservas.obtenerTodasReservas()
        hoy = datetime.now(tz=ZoneInfo("America/Mexico_City")).date()
        actualizadas = 0

        for reserva in reservas:
            hilo = self.bot.get_channel(reserva["id_hilo"])
            if hilo is None:
                hilo = await self.bot.fetch_channel(reserva["id_hilo"])
            mensaje = await hilo.fetch_message(reserva["id_mensaje"])
            embed = mensaje.embeds[0]

            if reserva["estado"] == "vencida":
                continue

            fecha_expiracion = datetime.strptime(
                reserva["fecha_expiracion"], "%Y-%m-%d"
            ).date()
            if fecha_expiracion < hoy:
                # Ya pasó la fecha de expiración
                if self.bot.bd.reservas.actualizarEstadoReserva(
                    reserva["id_reserva"], "vencida"
                ):
                    embed.color = discord.Color.red()
                    embed.description = (
                        f"Reserva expirada desde {reserva['fecha_expiracion']}"
                    )
                    actualizadas += 1
                    logger.info(
                        f"Reserva vencida: id_reserva={reserva['id_reserva']} fecha_expiracion={fecha_expiracion}"
                    )
            elif fecha_expiracion == hoy and reserva["estado"] == "activa":
                # Hoy es el último día
                if self.bot.bd.reservas.actualizarEstadoReserva(
                    reserva["id_reserva"], "por_expirar"
                ):
                    embed.color = discord.Color.orange()
                    actualizadas += 1
                    logger.info(
                        f"Reserva por expirar hoy: id_reserva={reserva['id_reserva']} fecha_expiracion={fecha_expiracion}"
                    )

            await mensaje.edit(embed=embed)

        logger.info(
            f"Actualización de estados de reservas completada: {actualizadas} reservas actualizadas."
        )

    async def eliminarReservasVencidasAntiguas(self, dias: int = 7):
        logger.info(
            f"Buscando reservas vencidas hace más de {dias} días para eliminar..."
        )

        reservas_vencidas = self.bot.bd.reservas.obtenerReservasVencidasAntiguas(dias)

        if not reservas_vencidas:
            logger.info(f"No hay reservas vencidas hace más de {dias} días.")
            return

        # Preparar embed para Discord
        canalLogs = self.bot.get_channel(ID_LOGS_RESERVAS)
        if canalLogs is None:
            logger.error(
                f"No se pudo obtener el canal de logs de reservas: {ID_LOGS_RESERVAS}"
            )
            return

        eliminadas = 0
        embed = discord.Embed(
            title="Reservas Eliminadas por Vencimiento",
            description=f"Reservas vencidas hace más de {dias} días",
            color=discord.Color.red(),
            timestamp=datetime.now(ZoneInfo("America/Mexico_City")),
        )

        for reserva in reservas_vencidas:
            try:
                hilo = self.bot.get_channel(reserva["id_hilo"])
                if hilo is None:
                    hilo = await self.bot.fetch_channel(reserva["id_hilo"])
                mensaje = await hilo.fetch_message(reserva["id_mensaje"])
                await mensaje.delete()
                # Formatear información de la reserva
                info_reserva = (
                    f"**ID:** {reserva['id_reserva']}\n"
                    f"**Usuario:** {reserva['id_propietario']}\n"
                    f"**Personaje:** {reserva['nombre_personaje']}\n"
                    f"**Obra:** {reserva['id_obra']}\n"
                    f"**Expiración:** {reserva['fecha_expiracion']}"
                )

                # Añadir campo al embed (máximo 25 campos)
                embed.add_field(
                    name=f"Reserva {eliminadas + 1}", value=info_reserva, inline=True
                )

                # Eliminar de la base de datos
                if self.bot.bd.reservas.eliminarReservaDefinitiva(
                    reserva["id_reserva"]
                ):
                    eliminadas += 1
                    logger.info(
                        f"Reserva vencida eliminada: id_reserva={reserva['id_reserva']}"
                    )
            except discord.NotFound:
                logger.warning(
                    f"Mensaje ya no existe para reserva {reserva['id_reserva']}"
                )
            except Exception as e:
                logger.error(
                    f"Error procesando reserva vencida {reserva['id_reserva']}: {e}",
                    exc_info=True,
                )

        # Añadir footer con total
        embed.set_footer(text=f"Total eliminadas: {eliminadas}")

        try:
            await canalLogs.send(embed=embed)
        except Exception as e:
            logger.error(f"Error enviando logs a Discord: {e}", exc_info=True)

        logger.info(
            f"Eliminación de reservas vencidas completada: {eliminadas} reservas eliminadas."
        )

    async def eliminarHilosEliminadosAntiguos(self, dias: int = 7):
        logger.info(
            f"Buscando fichas eliminadas hace más de {dias} días para borrar hilos..."
        )

        fichas_eliminadas = self.bot.bd.fichas.obtenerFichasEliminadasAntiguas(dias)
        eliminados = 0
        no_encontrados = 0

        for ficha in fichas_eliminadas:
            id_hilo = ficha["id_hilo"]
            try:
                thread = self.bot.get_channel(id_hilo)
                if thread is None:
                    thread = await self.bot.fetch_channel(id_hilo)

                await thread.delete(
                    reason=f"Eliminar hilo de ficha eliminada por más de {dias} días"
                )
                eliminados += 1
                logger.info(
                    f"Hilo eliminado: id_hilo={id_hilo} para ficha id_ficha={ficha['id_ficha']}"
                )

            except discord.NotFound:
                no_encontrados += 1
                logger.warning(
                    f"Hilo no encontrado al intentar borrar id_hilo={id_hilo} para ficha id_ficha={ficha['id_ficha']}"
                )
            except discord.Forbidden as e:
                logger.error(
                    f"Permisos insuficientes para borrar hilo id_hilo={id_hilo} de ficha id_ficha={ficha['id_ficha']}: {e}",
                    exc_info=True,
                )
            except Exception as e:
                logger.error(
                    f"Error borrando hilo id_hilo={id_hilo} de ficha id_ficha={ficha['id_ficha']}: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Eliminación de hilos antiguos completada: {eliminados} hilos eliminados, {no_encontrados} no encontrados."
        )

    async def _ids_validos(self, id_hilo: int, id_mensaje: int) -> bool:
        try:
            thread = self.bot.get_channel(id_hilo)
            if thread is None:
                thread = await self.bot.fetch_channel(id_hilo)

            await thread.fetch_message(id_mensaje)
            return True

        except discord.NotFound:
            return False
        except discord.Forbidden as e:
            logger.error(
                f"Permiso denegado al verificar ids {id_hilo}/{id_mensaje}: {e}",
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error(
                f"Error verificando IDs {id_hilo}/{id_mensaje}: {e}", exc_info=True
            )
            return False

    # Diarias a las 23:59
    @tasks.loop(time=diarias)
    async def Diarias(self):
        print("Ejecutando tareas diarias...")
        # Eliminar registros con IDs inválidos
        await self.integridadIDs()
        # Sincronizar obras del foro
        await self.actualizarObras()
        # Actualizar estados de reservas por expiración
        await self.actualizarEstadosReservas()
        # Borrar hilos de fichas eliminadas hace más de 7 días
        await self.eliminarHilosEliminadosAntiguos()
        # Eliminar reservas vencidas antiguas (y registrarlas)
        await self.eliminarReservasVencidasAntiguas(dias=3)

    # Mensuales el día 1 a las 00:00
    @tasks.loop(time=medianoche)
    async def Mensuales(self):
        if datetime.now(ZoneInfo("America/Mexico_City")).day == 1:
            print("Ejecutando tareas mensuales...")
            # Eliminar usuarios que abandonaron el servidor
            await self.eliminarUsuariosAusentes()
            # Marcar fichas y reservas de usuarios inactivos como eliminadas/vencidas
            await self.marcarInactivosPorEliminar()

    async def eliminarUsuariosAusentes(self):
        logger.info("Verificando usuarios que abandonaron el servidor...")

        usuarios = self.bot.bd.usuarios.obtenerTodosUsuarios()

        # Get server from bot's guilds
        servidores = self.bot.guilds
        if not servidores:
            logger.warning("Bot no está en ningún servidor")
            return

        servidor = servidores[0]
        eliminados = 0

        for usuario in usuarios:
            id_usuario = usuario["id_usuario"]
            try:
                miembro = servidor.get_member(id_usuario)
                if miembro is None:
                    # Usuario no está en el servidor, eliminar (cascade elimina fichas/reservas)
                    if self.bot.bd.usuarios.eliminarUsuario(id_usuario):
                        eliminados += 1
                        logger.info(
                            f"Usuario eliminado por ausencia: id_usuario={id_usuario}"
                        )
            except Exception as e:
                logger.error(
                    f"Error verificando usuario {id_usuario}: {e}", exc_info=True
                )

        logger.info(
            f"Limpieza de usuarios ausentes completada: {eliminados} usuarios eliminados."
        )

    async def marcarInactivosPorEliminar(self, dias: int = 5):
        logger.info(
            f"Marcando fichas y reservas de usuarios inactivos (>{dias} días)..."
        )

        usuarios_inactivos = self.bot.bd.usuarios.obtenerUsuariosInactivos(dias)
        canal_advertencias = self.bot.get_channel(ID_ADVERTENCIAS)
        if canal_advertencias is None:
            logger.error(
                f"No se pudo obtener el canal de advertencias: {ID_ADVERTENCIAS}"
            )
            return

        fichas_marcadas = 0
        reservas_marcadas = 0

        for usuario in usuarios_inactivos:
            id_usuario = usuario["id_usuario"]
            try:
                # Marcar fichas activas como eliminadas
                fichas_count = self.bot.bd.fichas.marcarFichasEliminadasPorUsuario(
                    id_usuario
                )
                if fichas_count:
                    fichas_marcadas += fichas_count

                # Marcar reservas activas como vencidas
                reservas_count = self.bot.bd.reservas.marcarReservasVencidasPorUsuario(
                    id_usuario
                )
                if reservas_count:
                    reservas_marcadas += reservas_count

                # Si se marcaron registros, enviar advertencia
                if fichas_count or reservas_count:
                    await self._enviarAdvertenciaInactividad(
                        canal_advertencias, id_usuario
                    )
                    logger.info(
                        f"Advertencia enviada a usuario inactivo {id_usuario}: {fichas_count} fichas, {reservas_count} reservas"
                    )

            except Exception as e:
                logger.error(
                    f"Error procesando usuario inactivo {id_usuario}: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Marcado de inactivos completado: {fichas_marcadas} fichas marcadas, {reservas_marcadas} reservas marcadas."
        )

    async def _enviarAdvertenciaInactividad(
        self, canal: discord.TextChannel, id_usuario: int
    ):
        try:
            usuario = self.bot.get_user(id_usuario)
            if usuario is None:
                logger.warning(
                    f"No se pudo obtener usuario {id_usuario} para advertencia"
                )
                return

            # Crear hilo privado para la advertencia
            hilo = await canal.create_thread(
                name=f"Advertencia - {usuario.name}",
                type=discord.ChannelType.private_thread,
            )

            embed = discord.Embed(
                title="Advertencia de Inactividad",
                description=(
                    "Tus registros se han **eliminado** por inactividad.\n"
                    "Renueva tus fichas con `/ficha restaurar' "
                    "en la brevedad o serán eliminadas permanentemente.\n"
                    "Haz de nuevo las reservas cuando sea posible."
                ),
                color=discord.Color.orange(),
                timestamp=datetime.now(ZoneInfo("America/Mexico_City")),
            )

            await hilo.send(content=usuario.mention, embed=embed)

        except discord.Forbidden as e:
            logger.error(
                f"Permisos insuficientes para crear hilo de advertencia para usuario {id_usuario}: {e}",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Error enviando advertencia a usuario {id_usuario}: {e}", exc_info=True
            )


async def setup(bot):
    await bot.add_cog(TareasProgramadas(bot))
