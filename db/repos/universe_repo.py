import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger
from utils.utils import normStr


class RepoObras(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)

    def crearObra(self, nombre_obra: str, id_hilo: int):
        try:
            nombre_normalizado = normStr(nombre_obra)
            cursor = self.ejecutar(
                """
                INSERT OR IGNORE INTO obras (nombre_obra, nombre_normalizado, id_hilo) VALUES (?, ?, ?);
            """,
                (nombre_obra, nombre_normalizado, id_hilo),
            )

            if cursor is not None and cursor.rowcount > 0:
                return cursor.lastrowid
            else:
                return self.obtenerObraPorNombre(nombre_obra)["id_obra"]

        except sql.Error as e:
            logger.error(f"Error creando obra '{nombre_obra}': {e}", exc_info=True)
            raise

    def obtenerObra(self, id_obra: int):
        try:
            return self.consultaUno(
                """
                SELECT * FROM obras WHERE id_obra = ?;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo obra {id_obra}: {e}", exc_info=True)
            return None

    def obtenerObras(self):
        try:
            return self.consultaTodos("""
                SELECT * FROM obras ORDER BY nombre_obra;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las obras: {e}", exc_info=True)
            return []

    def obtenerObraPorNombre(self, nombre_obra: str):
        try:
            nombre_normalizado = normStr(nombre_obra)
            return self.consultaUno(
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

    def buscarObrasPorNombre(self, nombre_obra: str):
        try:
            nombre_normalizado = normStr(nombre_obra)
            return self.consultaTodos(
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

    def obtenerObraPorHilo(self, id_hilo: int):
        try:
            return self.consultaUno(
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

    def actualizarObra(self, id_obra: int, nombre_obra: str, id_hilo: int):
        try:
            nombre_normalizado = normStr(nombre_obra)
            cursor = self.ejecutar(
                """
                UPDATE obras SET nombre_obra = ?, nombre_normalizado = ?, id_hilo = ? WHERE id_obra = ?;
            """,
                (nombre_obra, nombre_normalizado, id_hilo, id_obra),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error actualizando obra {id_obra}: {e}", exc_info=True)
            raise

    def eliminarObra(self, id_obra: int):
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM obras WHERE id_obra = ?;
            """,
                (id_obra,),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando obra {id_obra}: {e}", exc_info=True)
            raise
