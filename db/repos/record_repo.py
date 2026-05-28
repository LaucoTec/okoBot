import sqlite3 as sql

from logs.loggers.db_logger import logger
from utils.text_utils import normalizar_texto

from ..queries import AsistenteDeConsultas


class RepoFichas(AsistenteDeConsultas):
    def crear_ficha(
        self,
        id_propietario: int,
        nombre_personaje: str,
        id_obra: int,
        id_hilo: int,
        id_mensaje: int,
    ) -> int | None:
        try:
            nombre_normalizado = normalizar_texto(nombre_personaje)
            cursor = self.ejecutar(
                """
                INSERT INTO fichas (id_propietario, nombre_personaje, nombre_normalizado, id_obra, id_hilo, id_mensaje) 
                VALUES (?, ?, ?, ?, ?, ?);
            """,
                (
                    id_propietario,
                    nombre_personaje,
                    nombre_normalizado,
                    id_obra,
                    id_hilo,
                    id_mensaje,
                ),
            )

            return cursor.lastrowid

        except sql.Error as e:
            logger.error(
                f"Error creando ficha para usuario {id_propietario}: {e}", exc_info=True
            )
            raise

    def obtener_ficha_por_id(self, id_ficha: int) -> sql.Row | None:
        try:
            return self.consulta_uno(
                """
                SELECT * FROM fichas WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo ficha {id_ficha}: {e}", exc_info=True)
            return None

    def obtener_fichas(self) -> list[sql.Row]:
        try:
            return self.consulta_todos("""
                SELECT * FROM fichas;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las fichas: {e}", exc_info=True)
            return []

    def obtener_ficha_por_nombre_normalizado(
        self, nombre_normalizado: str
    ) -> sql.Row | None:
        try:
            return self.consulta_uno(
                """
                SELECT * FROM fichas WHERE nombre_normalizado = ?;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo ficha por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return None

    # TODO: Revisar si es necesaria esta función
    def obtener_fichas_por_nombre_normalizado(
        self, nombre_normalizado: str
    ) -> list[sql.Row]:
        try:
            return self.consulta_todos(
                """
                SELECT * FROM fichas WHERE nombre_normalizado = ? ORDER BY fecha_creacion DESC;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return []

    def obtener_fichas_por_usuario(self, id_propietario: int) -> list[sql.Row]:
        try:
            return self.consulta_todos(
                """
                SELECT * FROM fichas WHERE id_propietario = ? ORDER BY fecha_creacion DESC;
            """,
                (id_propietario,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para usuario {id_propietario}: {e}",
                exc_info=True,
            )
            return []

    def obtener_fichas_por_obra(self, id_obra: int) -> list[sql.Row]:
        try:
            return self.consulta_todos(
                """
                SELECT * FROM fichas WHERE id_obra = ? ORDER BY fecha_creacion DESC;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para obra {id_obra}: {e}", exc_info=True
            )
            return []

    def obtener_fichas_por_usuario_y_estado(
        self, id_propietario: int, estado: str
    ) -> list[sql.Row]:
        try:
            return self.consulta_todos(
                """
                SELECT * FROM fichas WHERE id_propietario = ? AND estado = ? ORDER BY fecha_creacion DESC;
            """,
                (id_propietario, estado),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para usuario {id_propietario} con estado '{estado}': {e}",
                exc_info=True,
            )
            return []

    def obtener_fichas_eliminadas_antiguas(self, dias: int) -> list[sql.Row]:
        try:
            return self.consulta_todos(
                """
                SELECT * FROM fichas
                WHERE estado = 'eliminada'
                  AND fecha_estado <= DATETIME('now', ?)
            """,
                (f"-{dias} days",),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas eliminadas antiguas: {e}", exc_info=True
            )
            return []

    def actualizar_nombre_ficha(self, id_ficha: int, nuevo_nombre: str) -> bool:
        try:
            nombre_normalizado = normalizar_texto(nuevo_nombre)
            cursor = self.ejecutar(
                """
                UPDATE fichas SET nombre_personaje = ?, nombre_normalizado = ? WHERE id_ficha = ?;
            """,
                (nuevo_nombre, nombre_normalizado, id_ficha),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando nombre de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def actualizar_obra_ficha(self, id_ficha: int, nuevo_id_obra: int) -> bool:
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET id_obra = ? WHERE id_ficha = ?;
            """,
                (nuevo_id_obra, id_ficha),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando obra de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def actualizar_estado_ficha(self, id_ficha: int, nuevo_estado: str) -> bool:
        if nuevo_estado not in ("activa", "eliminada"):
            logger.warning(f"Estado inválido para ficha {id_ficha}: {nuevo_estado}")
            return False

        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = ?, fecha_estado = CURRENT_TIMESTAMP WHERE id_ficha = ?;
            """,
                (nuevo_estado, id_ficha),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando estado de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def eliminar_ficha_suave(self, id_ficha: int) -> bool:
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = 'eliminada', fecha_estado = CURRENT_TIMESTAMP WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando ficha {id_ficha}: {e}", exc_info=True)
            raise

    def eliminar_ficha_definitivo(self, id_ficha: int) -> bool:
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM fichas WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error eliminando definitivamente ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    # TODO Refactorizar servicio para eliminar esta función
    def marcarFichasEliminadasPorUsuario(self, id_usuario: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = 'eliminada', fecha_estado = CURRENT_TIMESTAMP
                WHERE id_propietario = ? AND estado = 'activa'
            """,
                (id_usuario,),
            )

            return cursor is not None and cursor.rowcount

        except sql.Error as e:
            logger.error(
                f"Error marcando fichas como eliminadas para usuario {id_usuario}: {e}",
                exc_info=True,
            )
            raise
