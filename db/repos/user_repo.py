import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger


class RepoUsuarios(AsistenteDeConsultas):
    def crear_usuario(self, id_usuario: int) -> bool:
        """Crea un nuevo usuario en la base de datos. Devuelve True si se creó un nuevo usuario, o False si ya existía un usuario con el mismo ID."""
        try:
            cursor = self.ejecutar(
                """
                INSERT OR IGNORE INTO usuarios (id_usuario) VALUES (?);
            """,
                (id_usuario,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error creando usuario {id_usuario}: {e}", exc_info=True)
            raise

    def obtener_usuario_por_id(self, id_usuario: int) -> sql.Row | None:
        """Obtiene un usuario por su ID. Devuelve un objeto sql.Row con los datos del usuario, o None si no se encontró ningún usuario con ese ID."""
        try:
            return self.consulta_uno(
                """
                SELECT * FROM usuarios WHERE id_usuario = ?;
            """,
                (id_usuario,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo usuario {id_usuario}: {e}", exc_info=True)
            return None

    def obtener_usuarios(self) -> list[sql.Row]:
        """Obtiene todas las usuarios registradas en la base de datos. Devuelve una lista de objetos sql.Row con los datos de cada usuario."""
        try:
            return self.consulta_todos("""
                SELECT * FROM usuarios;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todos los usuarios: {e}", exc_info=True)
            return []

    def obtener_usuarios_inactivos(self, dias: int) -> list[sql.Row]:
        """Obtiene los usuarios que no han tenido actividad en los últimos días indicados. Devuelve una lista de objetos sql.Row con los datos de cada usuario inactivo."""
        try:
            return self.consulta_todos(
                """
                SELECT * FROM usuarios
                WHERE ultima_actividad <= DATETIME('now', ?)
            """,
                (f"-{dias} days",),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo usuarios inactivos: {e}", exc_info=True)
            return []

    def actualizar_actividad(self, id_usuario: int) -> bool:
        """Actualiza la fecha de última actividad de un usuario al momento actual. Devuelve True si se actualizó el usuario, o False si no se encontró ningún usuario con ese ID."""
        try:
            cursor = self.ejecutar(
                """
                UPDATE usuarios SET ultima_actividad = CURRENT_TIMESTAMP WHERE id_usuario = ?;
            """,
                (id_usuario,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando actividad para usuario {id_usuario}: {e}",
                exc_info=True,
            )
            raise

    def eliminar_usuario(self, id_usuario: int) -> bool:
        """Elimina un usuario de la base de datos. Devuelve True si se eliminó el usuario, o False si no se encontró ningún usuario con ese ID."""
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM usuarios WHERE id_usuario = ?;
            """,
                (id_usuario,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando usuario {id_usuario}: {e}", exc_info=True)
            raise
