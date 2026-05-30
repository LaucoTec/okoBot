import sqlite3 as sql

from logs.loggers.db_logger import logger

from ..queries import AsistenteDeConsultas


class RepoUsuarios(AsistenteDeConsultas):
    def crear_usuario(self, id_usuario: int) -> bool:
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
        try:
            return self.consulta_todos("""
                SELECT * FROM usuarios;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todos los usuarios: {e}", exc_info=True)
            return []

    def obtener_usuarios_inactivos(self, dias: int) -> list[sql.Row]:
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
