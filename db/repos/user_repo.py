import sqlite3 as sql
from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger

class RepoUsuarios(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)
        
    def crearUsuario(self, id_usuario: int):
        try:
            cursor = self.ejecutar('''
                INSERT OR IGNORE INTO usuarios (id_usuario) VALUES (?);
            ''', (id_usuario,))
            
            if cursor is not None and cursor.rowcount > 0:
                return cursor.lastrowid
            else:
                return id_usuario

        except sql.Error as e:
            logger.error(f"Error creando usuario {id_usuario}: {e}", exc_info=True)
            raise
        
    def obtenerUsuario(self, id_usuario: int):
        try:
            return self.consultaUno('''
                SELECT * FROM usuarios WHERE id_usuario = ?;
            ''', (id_usuario,))

        except sql.Error as e:
            logger.error(f"Error obteniendo usuario {id_usuario}: {e}", exc_info=True)
            return None
    
    def obtenerTodosUsuarios(self):
        try:
            return self.consultaTodos('''
                SELECT * FROM usuarios;
            ''')

        except sql.Error as e:
            logger.error(f"Error obteniendo todos los usuarios: {e}", exc_info=True)
            return []
    
    def obtenerUsuariosInactivos(self, dias: int):
        try:
            return self.consultaTodos('''
                SELECT * FROM usuarios
                WHERE ultima_actividad <= DATETIME('now', ?)
            ''', (f'-{dias} days',))

        except sql.Error as e:
            logger.error(f"Error obteniendo usuarios inactivos: {e}", exc_info=True)
            return []
    
    def actualizarActividad(self, id_usuario: int):
        try:
            cursor = self.ejecutar('''
                UPDATE usuarios SET ultima_actividad = CURRENT_TIMESTAMP WHERE id_usuario = ?;
            ''', (id_usuario,))
            
            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error actualizando actividad para usuario {id_usuario}: {e}", exc_info=True)
            raise
        
    def eliminarUsuario(self, id_usuario: int):
        try:
            cursor = self.ejecutar('''
                DELETE FROM usuarios WHERE id_usuario = ?;
            ''', (id_usuario,))
            
            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando usuario {id_usuario}: {e}", exc_info=True)
            raise