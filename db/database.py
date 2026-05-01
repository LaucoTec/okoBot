import sqlite3 as sql
from pathlib import Path
import db.schema as schema
from db.repos import RepoUsuarios, RepoObras, RepoAliasObras, RepoFichas, RepoReservas


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
        
        # Activar llaves foráneas
        self.conexion.execute("PRAGMA foreign_keys = ON;")

        # Configurar el row_factory para obtener resultados como diccionarios
        self.conexion.row_factory = sql.Row
        
        # Crear esquema si no existe
        schema.iniciarBD(self.conexion)
        
        # Inicializar asistentes de consultas para cada repositorio
        self.usuarios = RepoUsuarios(self.conexion)
        self.obras = RepoObras(self.conexion)
        self.aliasObras = RepoAliasObras(self.conexion)
        self.fichas = RepoFichas(self.conexion)
        self.reservas = RepoReservas(self.conexion)
        
    def cerrar(self):
        self.conexion.close()
        
    def buscarObraPorNombreOAlias(self, nombre):
        """
        Busca una obra por su nombre o por cualquiera de sus alias.
        Retorna un diccionario con los datos de la obra o None si no se encuentra.
        """
        # Buscar por nombre de obra
        obra = self.obras.obtenerObraPorNombre(nombre)
        if obra:
            return dict(obra)
        
        # Buscar por alias
        alias = self.aliasObras.obtenerObraPorAlias(nombre)
        if alias:
            return dict(alias)
        
        return None