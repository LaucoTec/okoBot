from pathlib import Path
import discord
from discord.ext import commands
import asyncio
from db.database import BaseDeDatos
from config import TOKEN, ID_SERVER


class OkoBot(commands.Bot):
    """
    Clase principal del bot Feu para el servidor Okótbika. Se encarga de:
    - Inicializa la conexión a Discord
    - Inicializar la base de datos y cargar el esquema
    - Cargar y sincronizar los comandos
    - Gestionar eventos
    
    La función del bot es gestionar fichas de personaje y reservas de apariencia
    para obras originales, con comandos organizados en categorías.
    """
    def __init__(self):
        intenciones = discord.Intents.default()
        intenciones.members = True
        intenciones.message_content = True
        
        self.reservasPendientes = {}

        super().__init__(command_prefix="f!", intents=intenciones)
    
    async def setup_hook(self):
        print("Inicializando base de datos...")
        self.bd = BaseDeDatos()
    
        print("Cargando comandos...")
        carpetaComandos = Path(__file__).parent / "cogs"
        for comando in carpetaComandos.glob("*.py"):
            if comando.name != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{comando.stem}")
                    print(f"   - {comando.stem} cargado")
                except Exception as e:
                    print(f"Error cargando {comando.stem}: {e}")
        
        print("Sincronizando comandos...")
        try:
            servidor = discord.Object(id=ID_SERVER)
            self.tree.copy_global_to(guild=servidor)
            sincronizados = await self.tree.sync(guild=servidor)
            print(f"Sincronizados: {len(sincronizados)} comandos")
            for comando in sincronizados:
                print(f"   - {comando.name}")
        except Exception as e:
            print(f"Error sincronizando: {e}")
    
    async def on_ready(self):
        print(f"Conectado como {self.user}")
        print(f"Total comandos registrados: {len(self.tree.get_commands())}\n")
        
    async def close(self):
        print("Desconectado de Discord. Cerrando base de datos...")
        self.bd.cerrar()
        
        await super().close()


async def main():
    bot = OkoBot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())