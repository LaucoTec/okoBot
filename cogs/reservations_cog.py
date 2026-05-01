import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List
from rapidfuzz import fuzz, process
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import CommandOnCooldown, MissingPermissions, MissingRole, CheckFailure
from config import ID_LOGS_RESERVAS, ID_REPOSITORIO, ID_VERIFICADOR
from utils.utils import normStr

class reservaSelect(discord.ui.Select):
    def __init__(self, reservas, callback):
        self.reservas = reservas
        self.callbackFinal = callback
        
        options = []
        
        for r in reservas[:25]:
            options.append(
                discord.SelectOption(
                    label=r['nombre_personaje'][:100],
                    description=f"ID {r['id_reserva']}",
                    value=str(r['id_reserva'])
                )
            )
        
        super().__init__(
            placeholder="Selecciona una reserva",
            min_values=1,
            max_values=1,
            options=options
        )
        
    async def callback(self, interaction: discord.Interaction):
        reservaID = int(self.values[0])
        reserva = next(
            (r for r in self.reservas if r['id_reserva'] == reservaID), 
            None    
        )
        
        if reserva is None:
            await interaction.response.send_message(
                content="No se encontró la reserva seleccionada.",
                ephemeral=True
            )
            return
        
        await self.callbackFinal(interaction,  reserva)

class reservasVista(discord.ui.View):
    def __init__(self, bot, reservas, callback_select=None):
        super().__init__(timeout=120)
        self.bot = bot
        self.reservas = reservas
        self.callbackSelect = callback_select
        self.index = 0
        
        if self.callbackSelect is not None:
            self.add_item(
                reservaSelect(
                    reservas=self.reservas,
                    callback=self.callbackSelect
                )
            )
        self.actualizarBotones()
        
    def actualizarBotones(self):
        self.anterior.disabled = self.index <= 0
        self.siguiente.disabled = self.index >= len(self.reservas)-1
        
    def generarEmbed(self):
        reserva = self.reservas[self.index]
        
        embed = discord.Embed(
            title=reserva['nombre_personaje'],
            color=discord.Color.blurple()
        )
    
        embed.description = (
            f"- **Reserva:** {reserva['id_reserva']}\n"
            f"- **Obra:** <#{reserva['id_hilo']}>\n"
            f"- **Estado:** {reserva['estado']}\n"
            f"- **Fecha de expiración:** {reserva['fecha_expiracion']}"
        )
        embed.set_image(url=reserva['enlace_imagen'])

        embed.set_footer(
            text=f"{self.index + 1}/{len(self.reservas)}"
        )

        return embed
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button):
        self.index -= 1

        self.actualizarBotones()

        await interaction.response.edit_message(
            embed=self.generarEmbed(),
            view=self
        )

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def siguiente(self, interaction: discord.Interaction, button):
        self.index += 1

        self.actualizarBotones()

        await interaction.response.edit_message(
            embed=self.generarEmbed(),
            view=self
        )

class confirmarEliminar(discord.ui.View):
    def __init__(self, bot, reserva, embed):
        super().__init__(timeout=60)
        self.bot = bot
        self.reserva = reserva
        self.ejecutado = False
        self.embed = embed
    
    async def procesar(self, interaction: discord.Interaction):
        if self.ejecutado:
            return
        else:
            self.ejecutado = True
        
        self.embed.color = discord.Color.red()
        self.embed.title = "Confirmado."
        await interaction.edit_original_response(
            content="Reserva eliminada",
            embed=self.embed
        )
        
        canalOg = self.bot.get_channel(self.reserva['id_hilo'])
        if canalOg is None:
            canalOg = await self.bot.fetch_channel(self.reserva['id_hilo'])
        try:
            mensajeOg = await canalOg.fetch_message(self.reserva['id_mensaje'])
        except discord.NotFound:
            return
        
        if mensajeOg.embeds is not None:
            embedOg = mensajeOg.embeds[0]
            embedLog = discord.Embed(
            title=f"Reserva eliminada en {canalOg.name}",
            color=discord.Color.red(),
            description=f"**Nombre de la reserva**: {embedOg.title}"
        )
            embedOg.color = discord.Color.red()
            embedOg.description = "**Reserva cancelada**"
            await mensajeOg.edit(embed=embedOg)
            embedLog.set_thumbnail(url=embedOg.image.url)
            embedLog.set_author(
                name= interaction.user.display_name,
                icon_url=interaction.user.display_avatar.url
            )
            
        canalLog = self.bot.get_channel(ID_LOGS_RESERVAS)
        if canalLog is None:
            canalLog = await self.bot.fetch_channel(ID_LOGS_RESERVAS)
        await canalLog.send(
            content="Reserva eliminada",
            embed=embedLog
        )    
            
        self.bot.bd.reservas.actualizarEstadoReserva(id_reserva=self.reserva['id_reserva'], nuevo_estado="vencida")
        
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await self.procesar(interaction)
        
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button):
        self.embed.color = discord.Color.dark_red()
        await interaction.response.edit_message(
            content="Operación cancelada.",
            embed=self.embed,
            view=None
        )
        self.stop()

class confirmarEditar(discord.ui.View):
    def __init__(self, bot, reserva, obraNueva, obraVieja, motivo):
        super().__init__(timeout=60)
        self.bot = bot
        self.reserva = reserva
        self.obra = obraNueva
        self.obraVieja = obraVieja
        self.motivo = motivo
        self.ejecutado = False
        
    async def procesar(self, interaction: discord.Interaction):
        if self.ejecutado:
            return
        else:
            self.ejecutado = True

        hiloViejo = self.bot.get_channel(self.reserva['id_hilo'])
        if hiloViejo is None:
            hiloViejo = await self.bot.fetch_channel(self.reserva['id_hilo'])
        try:
            mensajeViejo = await hiloViejo.fetch_message(self.reserva['id_mensaje'])
        except discord.NotFound:
            await interaction.edit_original_response(
                content="El mensaje de la reserva ya no existe. Por favor pida al usuario hacer una reserva nueva.",
                embed=None,
                view=None
            )
            self.stop()
            return
        
        hiloNuevo = self.bot.get_channel(self.obra['id_hilo'])
        if hiloNuevo is None:
            hiloNuevo = await self.bot.fetch_channel(self.obra['id_hilo'])
        
        if not mensajeViejo.embeds:
            await interaction.edit_original_response(
                content="Ha ocurrido un error con el mensaje original, favor de borrarlo y pedir al usuario una reserva nueva.",
                embed=None,
                view=None
            )
            self.stop()
            return
        else:
            embed = mensajeViejo.embeds[0]
            
        mensajeNuevo = await hiloNuevo.send(
            content=mensajeViejo.content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )
        
        await mensajeViejo.delete()
        
        self.bot.bd.reservas.editarReserva(
            id_reserva=self.reserva['id_reserva'],
            nuevo_id_obra=self.obra['id_obra'],
            nuevo_id_hilo=hiloNuevo.id,
            nuevo_id_mensaje=mensajeNuevo.id
        )
        
        await interaction.edit_original_response(
            content="Reserva movida correctamente.",
            view=None
            )
        self.stop()
        
        canalLog =  self.bot.get_channel(ID_LOGS_RESERVAS)
        if canalLog is None:
            canalLog = await self.bot.fetch_channel(ID_LOGS_RESERVAS)
            
        embedLog = discord.Embed(
            title= self.motivo,
            color=discord.Color.pink()
        )
        embedLog.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )
        
        embedLog.description = (
            f"**Nombre pj:** {self.reserva['nombre_personaje']}\n"
            f"**Obra antigua:** {self.obraVieja['nombre_obra']}\n"
            f"**Obra nueva:** {self.obra['nombre_obra']}"
        )
        
        embedLog.set_footer(text=f"ID reserva: {self.reserva['id_reserva']}")
        
        await canalLog.send(
            content="Reserva actualizada",
            embed=embedLog
        )
    
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green)
    async def confirmar(self, interaction: discord.Interaction, button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        await self.procesar(interaction)
        
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red)
    async def cancelar(self, interaction: discord.Interaction, button):
        await interaction.response.edit_message(
            content="Operación cancelada.",
            embed=None,
            view=None
        )
        self.stop()

class reservaModal(discord.ui.Modal, title="Crear Reserva de Apariencia"):
    nombrePj = discord.ui.TextInput(label="Nombre del personaje", placeholder="Ej: Steel", required=True)
    obra = discord.ui.TextInput(label="Obra original", placeholder="Ej: Max Steel (Reboot)", required=True)
    placeholder = discord.ui.TextInput(label="¿No está el universo de tu personaje?", 
                                       style=discord.TextStyle.paragraph, 
                                       required=False,
                                       default="Si no hay un foro específico para la obra, escriba 'solicitar' junto al nombre de la obra en el campo anterior."
                                       )
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    async def cancelarReserva(self, userID):
        await asyncio.sleep(120)
        if userID in self.bot.reservasPendientes:
            temp =self.bot.reservasPendientes.pop(userID, None)
            canal = self.bot.get_channel(temp.get("canal_id"))
            if canal is None:
                canal = await self.bot.fetch_channel(temp.get("canal_id"))
            await canal.send(f"Reserva pendiente del usuario <@{userID}> ha sido cancelada por falta de respuesta.", delete_after=10)
    
    def obtenerSimilitud(self, nombrePj, reservasActivas):
        if not reservasActivas:
            return None, 0
        
        if len(nombrePj) <= 7:
            scorer = fuzz.ratio
        else:
            scorer = fuzz.token_sort_ratio
        
        resultado = process.extractOne(
            nombrePj, 
            reservasActivas,
            scorer=scorer
        )
        
        if resultado:
            puntuacion = resultado[1]
            coincidencia = resultado[0]
            return coincidencia, puntuacion
        else:
            return None, 0
    
    async def revisarDuplicados(self, idObra, nombrePj, interaction ):
        reservas = self.bot.bd.reservas.obtenerReservasPorObra(idObra)
        idUsuario = interaction.user.id
        nombreNorm = normStr(nombrePj)
        
        for reserva in reservas:
            if nombreNorm == reserva['nombre_normalizado']:
                if reserva['estado'] != 'vencida':
                    return "BLOQUEO_OCUPADO", reserva['nombre_personaje']
                
                if reserva['estado'] == "vencida" and reserva['id_propietario'] == idUsuario:
                    return "BLOQUEO_RECIENTE", reserva['nombre_personaje']
                
                continue
        
        reservasPersonales = {r['nombre_normalizado']: r['nombre_personaje'] for r in reservas if r['id_propietario'] == idUsuario and r['estado'] == "vencida"}
        if reservasPersonales:
            _, puntuacionPersonal = self.obtenerSimilitud(nombrePj=nombreNorm, reservasActivas=reservasPersonales)
            if puntuacionPersonal >= 90:
                return "BLOQUEO_RECIENTE", reserva['nombre_personaje']
        
        mapeoNombres = {r['nombre_normalizado']: r['nombre_personaje'] for r in reservas if r['estado'] != "vencida"}
        reservasActivas = list(mapeoNombres.keys())
        if reservasActivas:
            mejorCoincidencia, puntuacion = self.obtenerSimilitud(nombrePj=nombreNorm, reservasActivas=reservasActivas)
            if mejorCoincidencia and puntuacion >= 70:
                return "ADVERTENCIA", mapeoNombres[mejorCoincidencia]
            
        return "LIBRE", None 
            
        
    
    async def on_submit(self, interaction: discord.Interaction):
        bd = self.bot.bd
        mensaje = ""
        
        nombre = self.nombrePj.value.strip()
        obraIngresada = self.obra.value.strip()
        
        if "solicitar" in obraIngresada.lower():
            mensaje += "> *Has indicado que el universo de tu personaje **no** está en la lista.* \n\n"
            mensaje += "El equipo de administración revisará tu solicitud y podría crear un nuevo foro para esa obra. "
            mensaje += "Mientras tanto, tu reserva estará guardada en un canal temporal.\n\n"
            obra = dict(bd.obras.obtenerObra(3))
        else:    
            obra = bd.buscarObraPorNombreOAlias(obraIngresada)
            if obra is None:
                await interaction.response.send_message(
                    f"No se encontró la obra '{obraIngresada}'. Por favor, verifica el nombre o alias e inténtalo de nuevo.",
                    ephemeral=True
                )
                return
        
        embed = discord.Embed(
            title=f"Reserva recibida",
            color=discord.Color.brand_green()
        )
        contenido = f"Nombre: {nombre}\nObra: {obra['nombre_obra']}\n"
        
        estado, duplicado = await self.revisarDuplicados(idObra=obra['id_obra'], nombrePj=nombre, interaction=interaction)
        if estado == "BLOQUEO_OCUPADO":
            embed.color = discord.Color.red()
            embed.description = f"Ya existe una reserva para este personaje.\nVuelva a verificar o reserve a otro."
            mensaje = "Operación cancelada."
            await interaction.response.send_message(
                content=mensaje,
                embed=embed,
                delete_after=20,
                ephemeral=True
            )
            return
        elif estado == "BLOQUEO_RECIENTE":
            embed.color = discord.Color.dark_red()
            embed.description = f"Esta reserva fue eliminada o expiró recientemente. \n Espere unos días antes de poderlo volver a reservar."
            mensaje = "Operación cancelada."
            await interaction.response.send_message(
                content=mensaje,
                embed=embed,
                delete_after=20,
                ephemeral=True
            )
            return
        elif estado == "ADVERTENCIA":
            embed.color = discord.Color.yellow()
            contenido += f"Existe una reserva '{duplicado}' potencialmente duplicada. \n Verifique que no sea el caso y continúe.\n\n"
            mensaje += "**Revise antes de continuar**."
        else:
            contenido += "- No hay ninguna reserva colisionando, puede seguir sin problemas.\n"
            
        contenido += "\nAhora, **responde** a este mensaje con la imagen de tu personaje para completar la reserva."
        contenido += "\n-# Si no respondes con una imagen dentro de los próximos 2 minutos, la reserva se cancelará automáticamente."
        embed.description = contenido
        
        self.bot.reservasPendientes[interaction.user.id] = {
            "nombre_personaje": nombre,
            "obra": obra,
            "obraIngresada": obraIngresada,
            "mensaje_id": None,
            "canal_id": interaction.channel_id
        }
        
        await interaction.response.send_message(
            content=mensaje,
            embed=embed,
            delete_after=120
            )
        
        msj = await interaction.original_response()
        self.bot.reservasPendientes[interaction.user.id]['mensaje_id'] = msj.id

        # Iniciar tarea para cancelar reserva si no se completa en 2 minutos
        asyncio.create_task(self.cancelarReserva(interaction.user.id))

class ReservaCog(commands.Cog):
    """
    Cog para gestionar las reservas de apariencia en el foro de reservas.
    Permite a los usuarios crear, editar y eliminar reservas, y registra todas las acciones en un canal de logs.
    """
    def __init__(self, bot):
        self.bot = bot
        
        self.tz = ZoneInfo("America/Mexico_City")
    
    reservaGroup = app_commands.Group(name="reserva", description="Comandos para gestionar reservas de apariencia")
    
    async def procesarImagen(self, mensaje: discord.Message):
        if not mensaje.attachments:
            return

        imagen = mensaje.attachments[0]
        if not  imagen.content_type or not imagen.content_type.startswith("image/"):
            await mensaje.channel.send("Por favor, responde con una imagen válida para completar la reserva.", delete_after=10)
            return
        data = self.bot.reservasPendientes.get(mensaje.author.id, None)
        if not data:
            return
        canal = self.bot.get_channel(ID_REPOSITORIO)
        if canal is None:
            canal = await self.bot.fetch_channel(ID_REPOSITORIO)
        
        archivo = await imagen.to_file()
        mensajeReservas = await canal.send(content=f"Reserva de {mensaje.author} (ID: {mensaje.author.id})", file=archivo)
        data['url_imagen'] = mensajeReservas.attachments[0].url
        data['autor'] = mensaje.author
        
        await self.registrarReserva(data)

        self.bot.reservasPendientes.pop(mensaje.author.id, None)
        await mensaje.delete()
        
    async def registrarReserva(self, data: dict):
        try:
            canalReserva = data['obra'].get('id_hilo')
            usuario = self.bot.bd.usuarios.obtenerUsuario(data['autor'].id)
            duracionReserva = usuario['duracion_reserva']
            fechaInicio = datetime.now(self.tz)
            fechaFin = fechaInicio + timedelta(days=duracionReserva)

            idReserva = self.bot.bd.reservas.crearReserva(
                id_propietario=data['autor'].id,
                nombre_personaje=data['nombre_personaje'],
                id_obra=data['obra']['id_obra'],
                fecha_expiracion=fechaFin.date().isoformat(),
                enlace_imagen=data['url_imagen'],
                id_hilo=canalReserva
            )
            
            data['id_reserva'] = idReserva

            msj = await self.embedReserva(data=data, fechaInicio=fechaInicio, fechaFin=fechaFin)
            msjLog = await self.embedLog(data=data, fechaInicio=fechaInicio, fechaFin=fechaFin)
            
            canal = self.bot.get_channel(canalReserva)
            if canal is None:
                canal = await self.bot.fetch_channel(canalReserva)
                
            canalLog = self.bot.get_channel(ID_LOGS_RESERVAS)
            if canalLog is None:
                canalLog = await self.bot.fetch_channel(ID_LOGS_RESERVAS)
            
            reserva = await canal.send(
                content=data['autor'].mention,
                embed=msj,
                allowed_mentions=discord.AllowedMentions.none()
                )
            
            await canalLog.send(content="Reserva creada.", embed=msjLog)

            self.bot.bd.reservas.editarMensajeIdReserva(id_reserva=idReserva, nuevo_id_mensaje=reserva.id)
        except Exception as e:
            print(e)
        
    async def embedReserva(self, data: dict, fechaInicio, fechaFin):
        inicioStr = fechaInicio.date().strftime("%d/%m/%Y")
        finStr = fechaFin.date().strftime("%d/%m/%Y")
        
        embed = discord.Embed(
            title= data['nombre_personaje'],
            color=discord.Color.green()
        )
        embed.set_author(
            name=data['autor'].display_name,
            icon_url=data['autor'].display_avatar.url
        )
        
        if "solicitar" in data['obraIngresada'].lower():
            obraIngresada = data['obraIngresada'].lower().replace("solicitar","").strip()
            embed.description = (
                f"**Obra solicitada:** {obraIngresada}\n"
                f"**Inicio:** {inicioStr}\n"
                f"**Expira:** {finStr}"
            )
        else:
            embed.description = (
                f"**Inicio:** {inicioStr}\n"
                f"**Expira:** {finStr}"
            )
        
        embed.set_image(url=data['url_imagen'])
        
        embed.set_footer(text=f"ID reserva: {data['id_reserva']}")
        
        return embed
    
    async def embedLog(self, data: dict, fechaInicio, fechaFin):
        inicioStr = fechaInicio.date().strftime("%d/%m/%Y")
        finStr = fechaFin.date().strftime("%d/%m/%Y")
        
        embed = discord.Embed(
            title=f"Nueva reserva en {data['obra']['nombre_obra']}",
            color=discord.Color.yellow()
        )
        embed.set_author(
            name=data['autor'].display_name,
            icon_url=data['autor'].display_avatar.url
        )
        
        embed.description = (
            f"**Nombre pj:** {data['nombre_personaje']}\n"
            f"**Inicio:** {inicioStr}\n"
            f"**Expira:** {finStr}"
        )
        
        embed.set_thumbnail(url=data['url_imagen'])
        
        embed.set_footer(text=f"ID reserva: {data['id_reserva']}")
        
        return embed
    
    async def autocompletarReserva(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        bd = interaction.client.bd 
        userID = interaction.user.id
        
        reservas = bd.reservas.obtenerReservasPorUsuario(userID)
        resultados = []
        for r in reservas:
            if current.lower() in r["nombre_personaje"].lower() and r['estado'] != "vencida":
                resultados.append(
                    app_commands.Choice(
                        name=r["nombre_personaje"],
                        value=r["id_reserva"]
                    )
                )

        return resultados[:25]
    
    async def autocompletarReservaRenovada(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        bd = interaction.client.bd 
        userID = interaction.user.id
        
        reservas = bd.reservas.obtenerReservasPorUsuarioEstado(id_propietario=userID, estado="por_expirar")
        resultados = []
        for r in reservas:
            if current.lower() in r["nombre_personaje"].lower():
                resultados.append(
                    app_commands.Choice(
                        name=r["nombre_personaje"],
                        value=r["id_reserva"]
                    )
                )

        return resultados[:25]
    
    async def callbackEliminarAdmin(self, interaction, reserva):
        embed = discord.Embed(
            title="Confirmación",
            color=discord.Color.orange()
        )

        embed.description = (
            "¿Desea realmente eliminar esta reserva?\n"
            f"**Nombre:** {reserva['nombre_personaje']}\n"
            f"**ID:** {reserva['id_reserva']}"
        )

        embed.set_thumbnail(
            url=reserva['enlace_imagen']
        )

        botones = confirmarEliminar(
            bot=self.bot,
            reserva=reserva,
            embed=embed
        )

        await interaction.response.edit_message(
            content="Eliminación de reserva",
            embed=embed,
            view=botones
        )
        
    async def autocompletarObra(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Sugiere obras existentes conforme escribe."""
        if len(current) < 2:
            todasObras = self.bot.bd.obras.obtenerObras()
        else:
            resultado = self.bot.bd.buscarObraPorNombreOAlias(current)
            if resultado:
                todasObras = [resultado]
            else:
                todasObras = self.bot.bd.obras.buscarObrasPorNombre(current)
        
        if not todasObras:
            return []
        
        return [
            app_commands.Choice(name=obra["nombre_obra"], value=obra["nombre_obra"])
            for obra in todasObras[:25]
        ]
        
    @reservaGroup.command(name="crear", description="Crear una nueva reserva de apariencia")
    @app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.user.id))
    async def crearReserva(self, interaction: discord.Interaction):
        idUsuario = interaction.user.id
        self.bot.bd.usuarios.crearUsuario(interaction.user.id)
        self.bot.bd.usuarios.actualizarUsuario(interaction.user.id)
        
        if idUsuario in self.bot.reservasPendientes:
            await interaction.response.send_message(
                content="Ya tienes una reserva en proceso. Termínala antes de iniciar otra.",
                ephemeral=True
                )
            return
        
        reservas = self.bot.bd.reservas.obtenerReservasPorUsuario(idUsuario)
        fichas = self.bot.bd.fichas.obtenerFichasPorUsuario(idUsuario)
        perfil = self.bot.bd.usuarios.obtenerUsuario(idUsuario)
        
        if len(fichas) >= perfil['max_fichas']:
            await interaction.response.send_message(
                content="No puedes iniciar una reserva sin al menos un espacio de ficha disponible.",
                ephemeral=True
            )
            return
        
        cont = sum(1 for r in reservas if r['estado'] != "vencida")
        if cont >= perfil['max_reservas']:
            await interaction.response.send_message(
                content="Ya estás en tu límite de reservas actual. Espera a que venzan o elimina alguna.",
                ephemeral=True
            )
            return
        
        modal = reservaModal(self.bot)
        await interaction.response.send_modal(modal)
        
    @reservaGroup.command(name="mover", description="Edita la obra de una reserva.")
    @app_commands.describe(id_reserva="El ID de la reserva a editar", obra_nueva="Nombre o alias de la obra destino", motivo="(Opcional) Razón para el cambio.")
    @app_commands.default_permissions(administrator=True)
    async def editarReserva(self, interaction: discord.Interaction, id_reserva: int, obra_nueva: str, motivo:str="Obra previamente no creada."):
        reserva = self.bot.bd.reservas.obtenerReserva(id_reserva)
        if reserva is None:
            await interaction.response.send_message(
                content="No se encontró la reserva. Verifica que el ID sea el correcto.",
                ephemeral=True
                )
            return
        
        obraNuevaData = self.bot.bd.buscarObraPorNombreOAlias(obra_nueva)
        if obraNuevaData is None:
            await interaction.response.send_message(
                content="No se encontró la obra. Verifica el nombre o alias usado.",
                ephemeral=True
                )
            return
        
        obraViejaData = self.bot.bd.obras.obtenerObra(reserva['id_obra'])
        
        embed = discord.Embed(
            title="Confirmar cambio de obra.",
            color=discord.Color.yellow()
        )
        embed.add_field(
            name="Reserva",
            value=f"{reserva['nombre_personaje']}",
            inline=False
        )
        embed.add_field(
            name="Obra actual",
            value=f"{obraViejaData['nombre_obra']}",
            inline=True
        )
        embed.add_field(
            name="Obra nueva",
            value=f"{obraNuevaData['nombre_obra']}",
            inline=True
        )
        
        botones = confirmarEditar(bot=self.bot, reserva=reserva, obraNueva=obraNuevaData, obraVieja=obraViejaData, motivo=motivo)
        
        await interaction.response.send_message(
            content="Editando una reserva...",
            embed=embed,
            view=botones,
            ephemeral=True
        )
        
    @reservaGroup.command(name="eliminar", description="Elimina una de tus reservas.")
    @app_commands.describe(id_reserva="La reserva a eliminar")
    @app_commands.autocomplete(id_reserva=autocompletarReserva)
    @app_commands.checks.cooldown(1, 300.0, key=lambda i: (i.user.id))
    async def eliminarReserva(self, interaction: discord.Interaction, id_reserva: int):
        self.bot.bd.usuarios.crearUsuario(interaction.user.id)
        self.bot.bd.usuarios.actualizarUsuario(interaction.user.id)
        
        reserva = self.bot.bd.reservas.obtenerReserva(id_reserva)
        if reserva is None:
            await interaction.response.send_message(
                content="No se encontró la reserva.",
                ephemeral=True
            )
            return
        if reserva['id_propietario'] != interaction.user.id:
            await interaction.response.send_message(
                content="No puedes eliminar reservas de otros usuarios.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="Confirmación.",
            color=discord.Color.orange()
        )
        embed.description = (
            "¿Desea realmente eliminar esta reserva?\n"
            f"**Nombre:** {reserva['nombre_personaje']}\n"
            f"**ID:** {reserva['id_reserva']}"
        )
        embed.set_thumbnail(
            url=reserva['enlace_imagen']
        )
        botones = confirmarEliminar(bot=self.bot, reserva=reserva, embed=embed)
        
        await interaction.response.send_message(
            content="Eliminación de una reserva.",
            embed=embed,
            view=botones,
            ephemeral=True
        )
    @reservaGroup.command(name="eliminar_veri", description="Elimina una reserva de cualquier usuario.")
    @app_commands.describe(usuario="El usuario a obtener sus reservas")
    @app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.user.id))
    @app_commands.checks.has_role(ID_VERIFICADOR)
    async def eliminarReservaAdmin(self, interaction: discord.Interaction, usuario: discord.User):
        reservas = self.bot.bd.reservas.obtenerReservasPorUsuarioEstado(usuario.id, "activa")
        if not reservas:
            embed = discord.Embed(
                title="Eliminando una reserva",
                description="Este usuario no cuenta con ninguna reserva activa.",
                color=discord.Color.dark_gray()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        vista = reservasVista(
            bot=self.bot,
            reservas=reservas,
            callback_select=self.callbackEliminarAdmin
        )

        await interaction.response.send_message(
            content=f"Reservas activas de {usuario.mention}",
            embed=vista.generarEmbed(),
            view=vista,
            allowed_mentions=discord.AllowedMentions.none(),
            delete_after=300
        )
        
    @reservaGroup.command(name="listar", description="Muestra las reservas de un usuario u obra. Prioriza obra.")
    @app_commands.describe(usuario="El usuario a obtener sus reservas", obra="La obra a obtener sus reservas")
    @app_commands.autocomplete(obra=autocompletarObra)
    @app_commands.checks.cooldown(1, 20.0, key=lambda i: (i.user.id))
    async def listarReserva(self, interaction: discord.Interaction, usuario: discord.User | None=None, obra: str | None=None):
        usuario = usuario or interaction.user
        self.bot.bd.usuarios.crearUsuario(interaction.user.id)
        self.bot.bd.usuarios.actualizarUsuario(interaction.user.id)
        
        if obra:
            reservas = self.bot.bd.buscarObraPorNombreOAlias(obra)
        else:
            reservas = self.bot.bd.reservas.obtenerReservasPorUsuario(usuario.id)
        
        reservas = self.bot.bd.reservas.obtenerReservasPorUsuarioEstado(usuario.id, "activa")
        if not reservas:
            embed = discord.Embed(
                title="Revisando reservas.",
                description="Este usuario/obra no cuenta con ninguna reserva.",
                color=discord.Color.dark_gray()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

            return

        vista = reservasVista(
            bot=self.bot,
            reservas=reservas
        )

        await interaction.response.send_message(
            content=f"Reservas activas de {usuario.mention}",
            embed=vista.generarEmbed(),
            view=vista,
            allowed_mentions=discord.AllowedMentions.none(),
            delete_after=300
        )
        
    @reservaGroup.command(name="renovar", description="Renueva una reserva propia el día de su vencimiento.")
    @app_commands.describe(reserva="La reserva a renovar, sólo si es su último día.")
    @app_commands.autocomplete(reserva=autocompletarReservaRenovada)
    @app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.user.id))
    async def renovarReserva(self, interaction: discord.Interaction, reserva: int):
        self.bot.bd.usuarios.crearUsuario(interaction.user.id)
        self.bot.bd.usuarios.actualizarUsuario(interaction.user.id)
        usuario = self.bot.bd.usuarios.obtenerUsuario(interaction.user.id)
        duracionReserva = usuario['duracion_reserva']
        
        renovar = self.bot.bd.reservas.obtenerReserva(reserva)
        if not renovar or renovar['estado'] != "por_expirar":
            embed = discord.Embed(
                title="Renovación de reserva",
                description="No se ha encontrado una reserva válida.",
                color=discord.Color.light_grey()
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return
        
        fechaInicio = datetime.now(self.tz)
        fechaFin = fechaInicio + timedelta(days=duracionReserva)
        
        embed= discord.Embed(
            title="Renovación de reserva",
            color=discord.Color.greyple()
        )
        embed.description = (
            "> *Datos*\n\n"
            f"**Nombre:** {renovar['nombre_personaje']}\n"
            f"**Obra:** <#{renovar['id_hilo']}>\n"
            f"**Nueva fecha de expiración:** {fechaFin.date()}"
        )
        
        if self.bot.bd.reservas.renovarReserva(id_reserva=reserva, fecha_fin=fechaFin.date().isoformat()):
            inicioStr = fechaInicio.date().strftime("%d/%m/%Y")
            finStr = fechaFin.date().strftime("%d/%m/%Y")
        
            canalOg = self.bot.get_channel(renovar['id_hilo'])
            if canalOg is None:
                canalOg = await self.bot.fetch_channel(renovar['id_hilo'])
            try:
                mensajeOg = await canalOg.fetch_message(renovar['id_mensaje'])
            except discord.NotFound:
                embed = discord.Embed(
                title="Renovación de reserva",
                description="El mensaje original se ha eliminada, haga una nueva reserva.",
                color=discord.Color.light_grey()
                )
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True
                )
                return
            
            embedNuevo = mensajeOg.embeds[0]
            embedNuevo.description = (
                f"**Inicio:** {inicioStr}\n"
                f"**Expira:** {finStr}"
            )
            embedNuevo.color = discord.Color.green()
            mensajeNuevo = await canalOg.send(
                content=interaction.user.mention,
                embed=embedNuevo,
                allowed_mentions=discord.AllowedMentions.none()
            )
            if self.bot.bd.reservas.editarMensajeIdReserva(id_reserva=reserva, nuevo_id_mensaje= mensajeNuevo.id):
                await interaction.response.send_message(
                    content="Reserva renovada.",
                    embed=embed,
                    delete_after=300
                )
                
                await mensajeOg.delete()
                
                description = f"**Personaje**: {renovar['nombre_personaje']}\n" + embedNuevo.description
                embedLog = discord.Embed(
                    title=f"Reserva renovada en {canalOg.name}",
                    color=discord.Color.teal(),
                    description=description
                )
                canalLog = self.bot.get_channel(ID_LOGS_RESERVAS)
                if canalLog is None:
                    canalLog = await self.bot.fetch_channel(ID_LOGS_RESERVAS)
                await canalLog.send(
                    content="Reserva renovada",
                    embed=embedLog
                )    
        
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(color=discord.Color.darker_gray())
        if isinstance(error, CommandOnCooldown):
            tiempo = int(error.retry_after)
            minutos = tiempo // 60
            segundos = tiempo % 60
            embed.description = f"Espere ⏱️ {minutos} minutos con {segundos} segundos antes de usar este comando nuevamente."
        elif isinstance(error, MissingRole):
            embed.description = "Esta acción esta reservada para nuestros Archivistas. 🔎"
        elif isinstance(error, MissingPermissions):
            embed.description = "Únicamente los 👑 Señores de la Cámara Alta pueden acceder a este comando. ⛔"
        else:
            embed.description = "Error desconocido."
            print(f"Error no manejado: {error}")
            
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
            delete_after=20
        )
        
async def setup(bot):
    await bot.add_cog(ReservaCog(bot))