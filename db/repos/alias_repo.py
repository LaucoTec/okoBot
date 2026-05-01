import sqlite3 as sql
from utils.utils import normStr
from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger

class RepoAliasObras(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)
        
    def crearAliasObra(self, alias: str, id_obra: int):
        try:
            nombre_normalizado = normStr(alias)
            cursor = self.ejecutar('''
                INSERT INTO alias_obras (alias, id_obra, alias_normalizado) VALUES (?, ?, ?);
            ''', (alias, id_obra, nombre_normalizado))

            return cursor.lastrowid if cursor is not None else None

        except sql.Error as e:
            logger.error(f"Error creando alias '{alias}' para obra {id_obra}: {e}", exc_info=True)
            raise
        
    def obtenerAliasesObras(self):
        try:
            return self.consultaTodos('''
                SELECT * FROM alias_obras;
            ''')

        except sql.Error as e:
            logger.error(f"Error obteniendo todos los alias de obras: {e}", exc_info=True)
            return []
    
    def obtenerAliasObra(self, id_alias: int):
        try:
            return self.consultaUno('''
                SELECT * FROM alias_obras WHERE id_alias = ?;
            ''', (id_alias,))

        except sql.Error as e:
            logger.error(f"Error obteniendo alias {id_alias}: {e}", exc_info=True)
            return None
        
    def obtenerAliasesObra(self, id_obra: int):
        try:
            return self.consultaTodos('''
                SELECT * FROM alias_obras WHERE id_obra = ?;
            ''', (id_obra,))
    
        except sql.Error as e:
            logger.error(f"Error obteniendo aliases para obra {id_obra}: {e}", exc_info=True)
            return []
        
    def buscarAliasesPorNombre(self, nombre_alias: str):
        try:
            nombre_normalizado = normStr(nombre_alias)
            return self.consultaTodos('''
                SELECT * FROM alias_obras WHERE alias_normalizado LIKE ? ORDER BY alias;
            ''', (f"%{nombre_normalizado}%",))

        except sql.Error as e:
            logger.error(f"Error buscando aliases por nombre '{nombre_alias}': {e}", exc_info=True)
            return []
    
    def obtenerObraPorAlias(self, alias: str):
        try:
            nombre_normalizado = normStr(alias)
            return self.consultaUno('''
                SELECT o.* FROM obras o
                JOIN alias_obras a ON o.id_obra = a.id_obra
                WHERE a.alias_normalizado = ?;
            ''', (nombre_normalizado,))

        except sql.Error as e:
            logger.error(f"Error obteniendo obra por alias '{alias}': {e}", exc_info=True)
            return None
        
    def eliminarAliasObra(self, id_alias: int):
        try:
            cursor = self.ejecutar('''
                DELETE FROM alias_obras WHERE id_alias = ?;
            ''', (id_alias,))

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando alias {id_alias}: {e}", exc_info=True)
            raise