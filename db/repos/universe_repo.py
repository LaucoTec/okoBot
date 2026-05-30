import sqlite3 as sql

from logs.loggers.db_logger import logger
from utils.text_utils import normalizar_texto

from ..queries import AsistenteDeConsultas


class RepoObras(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)

    def crear_obra(self, nombre_obra: str, id_hilo: int) -> bool:
        try:
            nombre_normalizado = normalizar_texto(nombre_obra)
            cursor = self.ejecutar(
                """
                INSERT OR IGNORE INTO obras (nombre_obra, nombre_normalizado, id_hilo) VALUES (?, ?, ?);
            """,
                (nombre_obra, nombre_normalizado, id_hilo),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error creando obra '{nombre_obra}': {e}", exc_info=True)
            raise

    def obtener_obra_por_id(self, id_obra: int) -> sql.Row | None:
        try:
            return self.consulta_uno(
                """
                SELECT * FROM obras WHERE id_obra = ?;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo obra {id_obra}: {e}", exc_info=True)
            return None

    # TODO: Evaluar si esta función es necesaria
    def obtener_obras(self) -> list[sql.Row]:
        try:
            return self.consulta_todos("""
                SELECT * FROM obras ORDER BY nombre_obra;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las obras: {e}", exc_info=True)
            return []

    def obtener_obra_por_nombre_normalizado(self, nombre_obra: str) -> sql.Row | None:
        try:
            nombre_normalizado = normalizar_texto(nombre_obra)
            return self.consulta_uno(
                """
                SELECT * FROM obras WHERE nombre_normalizado = ?;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo obra por nombre '{nombre_obra}': {e}", exc_info=True
            )
            return None

    # TODO: Evaluar si esta función es necesaria
    def buscar_obras_por_nombre_normalizado(self, nombre_obra: str) -> list[sql.Row]:
        try:
            nombre_normalizado = normalizar_texto(nombre_obra)
            return self.consulta_todos(
                """
                SELECT * FROM obras WHERE nombre_normalizado LIKE ? ORDER BY nombre_obra;
            """,
                (f"%{nombre_normalizado}%",),
            )

        except sql.Error as e:
            logger.error(
                f"Error buscando obras por nombre '{nombre_obra}': {e}", exc_info=True
            )
            return []

    def obtener_obra_por_hilo(self, id_hilo: int) -> sql.Row | None:
        try:
            return self.consulta_uno(
                """
                SELECT * FROM obras WHERE id_hilo = ?;
            """,
                (id_hilo,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo obra por hilo {id_hilo}: {e}", exc_info=True
            )
            return None

    # TODO: Evaluar si esta función es necesaria
    def actualizar_obra(self, id_obra: int, nombre_obra: str, id_hilo: int) -> bool:
        try:
            nombre_normalizado = normalizar_texto(nombre_obra)
            cursor = self.ejecutar(
                """
                UPDATE obras SET nombre_obra = ?, nombre_normalizado = ?, id_hilo = ? WHERE id_obra = ?;
            """,
                (nombre_obra, nombre_normalizado, id_hilo, id_obra),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error actualizando obra {id_obra}: {e}", exc_info=True)
            raise

    def eliminar_obra(self, id_obra: int) -> bool:
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM obras WHERE id_obra = ?;
            """,
                (id_obra,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando obra {id_obra}: {e}", exc_info=True)
            raise
