import discord 
from discord.ext import commands
from config import ID_GENERAL, ID_VERIFICACION
from logs.loggers.db_logger import logger

class Eventos(commands.Cog):
    """
Cog para gestionar eventos generales del servidor, como:
- Conteo de mensajes para actualizar actividad de usuarios en la base de datos
- Enviar mensajes de bienvenida efímeros a nuevos miembros para recordarse la verificación
    """
    def __init__(self, bot):
        self.bot = bot
        self.conteoMensajes = {}
        
    @commands.Cog.listener()
    async def on_message(self, mensaje):
        if mensaje.author.bot:
            return
        
        # ---Conteo de mensajes para actualizar actividad---
        # Conteo de mensajes por usuario
        idUsuario = mensaje.author.id
        if idUsuario not in self.conteoMensajes:
            self.conteoMensajes[idUsuario] = 0
        self.conteoMensajes[idUsuario] += 1
        
        # Actualizar BD si supera umbral de 5 mensajes
        if self.conteoMensajes[idUsuario] >= 5:
            try:
                self.bot.bd.usuarios.actualizarActividad(idUsuario)
                self.conteoMensajes[idUsuario] = 0  # Reiniciar conteo
            except Exception as e:
                logger.error(f"Error actualizando actividad para usuario {idUsuario}: {e}", exc_info=True)
                
        # ---Reservas pendientes---
        data = self.bot.reservasPendientes.get(mensaje.author.id)
        ref = mensaje.reference
        # Verificar que el mensaje es una respuesta al mensaje de reserva pendiente y que contiene una imagen
        if ref is None:
            return
        if data is None:
            return
        if not mensaje.attachments:
            return
        
        if ref.message_id == data.get("mensaje_id") and mensaje.channel.id == data.get("canal_id"):
            await self.bot.get_cog("ReservaCog").procesarImagen(mensaje)

    @commands.Cog.listener()
    async def on_member_join(self, miembro):
        # Mensaje efímero en general para recordar verificarse
        canalGeneral = self.bot.get_channel(ID_GENERAL)
        canalVerificacion = self.bot.get_channel(ID_VERIFICACION)
        if canalGeneral is not None and canalVerificacion is not None:
            try:
                await canalGeneral.send(f"Estimado {miembro.mention}: No olvide completar la verificación en {canalVerificacion.mention} para evitar ser expulsado.", delete_after=20)
            except Exception as e:
                logger.error(f"Error enviando mensaje de bienvenida para {miembro.id}: {e}", exc_info=True)
                
async def setup(bot):
    await bot.add_cog(Eventos(bot))