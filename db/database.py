import asyncio
import sqlite3 as sql
from contextlib import asynccontextmanager
from pathlib import Path

from db.queries import en_transaccion_var
from db.repos import RepoAliasObras, RepoFichas, RepoObras, RepoReservas, RepoUsuarios
from db.schema import iniciar_bd


class BaseDeDatos:
    """
    Clase para manejo de bases de datos del bot Feu.
    Contiene todos los métodos requeridos para sus comandos incluyendo:
    - Usuarios
    - Fichas de personaje
    - Reservas de apariencia
    - Obras originales y alias
    """

    def __init__(self):
        # Crear conexión a la base de datos
        ruta = Path(__file__).parent / "okoBot.db"
        self.conexion = sql.connect(ruta)

        # Activar llaves foráneas y modo WAL para mejorar integridad y concurrencia
        self.conexion.execute("PRAGMA foreign_keys = ON;")
        self.conexion.execute("PRAGMA journal_mode = WAL;")

        # Dejar autocommit desactivado para manejar transacciones manualmente
        self.conexion.autocommit = False

        # Lock asíncrono para serializar bloques de transacciones complejas
        self._lock = asyncio.Lock()

        # Configurar el row_factory para obtener resultados como diccionarios
        self.conexion.row_factory = sql.Row

        # Crear esquema si no existe
        iniciar_bd(self.conexion)

        # Inicializar asistentes de consultas para cada repositorio
        self.usuarios = RepoUsuarios(self.conexion)
        self.obras = RepoObras(self.conexion)
        self.aliasObras = RepoAliasObras(self.conexion)
        self.fichas = RepoFichas(self.conexion)
        self.reservas = RepoReservas(self.conexion)

    def cerrar(self):
        self.conexion.close()

    @asynccontextmanager
    async def transaccion(self):
        """
        Context manager para manejar transacciones de manera segura.
        Se asegura de hacer commit si todo sale bien, o rollback en caso de error.
        """
        async with self._lock:
            token = en_transaccion_var.set(True)
            try:
                yield

            except Exception:
                self.conexion.rollback()
                raise
            else:
                self.conexion.commit()
            finally:
                en_transaccion_var.reset(token)

    def buscarObraPorNombreOAlias(self, nombre: str) -> sql.Row | None:
        """
        Busca una obra por su nombre o por cualquiera de sus alias.
        Retorna un diccionario con los datos de la obra o None si no se encuentra.
        """
        # Buscar por nombre de obra
        obra = self.obras.obtener_obra_por_nombre_normalizado(nombre)
        if obra:
            return obra

        # Buscar por alias
        alias = self.aliasObras.obtener_obra_por_alias(nombre)
        if alias:
            return alias

        return None
