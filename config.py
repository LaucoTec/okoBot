import os
from pathlib import Path
from typing import overload

import discord
from discord.ext import commands
from dotenv import load_dotenv

from db import BaseDeDatos
from logs.loggers.bot_logger import logger as bot_logger
from logs.loggers.db_logger import logger as db_logger

load_dotenv()


@overload
def _env(key: str, *, cast: type[str] = str, required: bool = True) -> str: ...


@overload
def _env(key: str, *, cast: type[int], required: bool = True) -> int: ...


def _env(key: str, *, cast: type = str, required: bool = True):
    value = os.getenv(key)
    if value is None:
        if required:
            raise ValueError(f"Missing required environment variable: {key}")
        return None

    if cast is int:
        try:
            return int(value)

        except ValueError as exc:
            raise ValueError(
                f"Environment variable {key!r} must be an integer, got {value!r}"
            ) from exc

    return value


TOKEN = _env("TOKEN")
# Oko
ID_SERVER = _env("ID_SERVER", cast=int)
# ID de rol Verificador
ID_VERIFICADOR = _env("ID_VERIFICADOR", cast=int)
# ID canal general
ID_GENERAL = _env("ID_GENERAL", cast=int)
# ID canal de verificación
ID_VERIFICACION = _env("ID_VERIFICACION", cast=int)
# ID de canal de advertencias por inactividad
ID_ADVERTENCIAS = _env("ID_ADVERTENCIAS", cast=int)
# ID de canal de repositorio de imágenes
ID_REPOSITORIO = _env("ID_REPOSITORIO", cast=int)
# ID foro de reservas
ID_RESERVAS = _env("ID_RESERVAS", cast=int)
# ID de logs de obras y alias
ID_LOGS_OBRAS = _env("ID_LOGS_OBRAS", cast=int)
# ID de logs de reservas
ID_LOGS_RESERVAS = _env("ID_LOGS_RESERVAS", cast=int)
# Id de logs de fichas
ID_LOGS_FICHAS = _env("ID_LOGS_FICHAS", cast=int)


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
        bot_logger.info("Inicializando base de datos...")
        self.bd = BaseDeDatos()
        db_logger.info("Base de datos inicializada y esquema cargado.")
        intenciones = discord.Intents.default()
        intenciones.members = True
        intenciones.message_content = True

        self.reservasPendientes = {}
        self.conteoMensajes = {}

        super().__init__(command_prefix="f!", intents=intenciones)

    async def setup_hook(self):
        bot_logger.info("Iniciando bot...")
        bot_logger.info("Cargando comandos...")
        carpetaComandos = Path(__file__).parent / "cogs"
        for comando in carpetaComandos.glob("*.py"):
            if comando.name != "__init__.py":
                try:
                    await self.load_extension(f"cogs.{comando.stem}")
                    bot_logger.info(f"   - {comando.stem} cargado")
                except Exception as e:
                    bot_logger.error(f"Error cargando {comando.stem}: {e}")

        bot_logger.info("Sincronizando comandos...")
        try:
            servidor = discord.Object(id=ID_SERVER)
            self.tree.copy_global_to(guild=servidor)
            sincronizados = await self.tree.sync(guild=servidor)
            bot_logger.info(f"Sincronizados: {len(sincronizados)} comandos")
            for comando in sincronizados:
                bot_logger.info(f"   - {comando.name}")
        except Exception as e:
            bot_logger.error(f"Error sincronizando: {e}")

    async def on_ready(self):
        print(f"Conectado como {self.user}")
        print(f"Total comandos registrados: {len(self.tree.get_commands())}\n")
        bot_logger.info(
            f"Bot conectado como {self.user} con {len(self.tree.get_commands())} comandos registrados."
        )

    async def on_disconnect(self):
        bot_logger.warning("Desconectado de Discord. Intentando reconectar...")

    async def close(self):
        bot_logger.info("Desconectado de Discord. Cerrando base de datos...")
        self.bd.cerrar()
        db_logger.info("Base de datos cerrada. Bot apagado.")

        await super().close()
