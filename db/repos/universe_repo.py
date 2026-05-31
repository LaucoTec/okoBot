import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger
from utils.text_utils import normalizar_texto


class RepoObras(AsistenteDeConsultas):
    def crear_obra(self, nombre_obra: str, id_hilo: int) -> bool:
        """Crea una nueva obra en la base de datos. Devuelve True si se creó una nueva obra, o False si ya existía una obra con el mismo nombre normalizado."""
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
        """Obtiene una obra por su ID. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese ID."""
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
        """Obtiene todas las obras registradas en la base de datos, ordenadas por nombre. Devuelve una lista de objetos sql.Row con los datos de cada obra."""
        try:
            return self.consulta_todos("""
                SELECT * FROM obras ORDER BY nombre_obra;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las obras: {e}", exc_info=True)
            return []

    def obtener_obra_por_nombre_normalizado(self, nombre_obra: str) -> sql.Row | None:
        """Obtiene una obra por su nombre normalizado. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese nombre normalizado."""
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
        """Busca obras cuyo nombre normalizado contenga el texto dado. Devuelve una lista de objetos sql.Row con los datos de las obras encontradas, ordenadas por nombre."""
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
        """Obtiene una obra por el ID de su hilo asociado. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese ID de hilo."""
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
        """Actualiza el nombre y el ID de hilo de una obra. Devuelve True si se actualizó la obra, o False si no se encontró ninguna obra con ese ID."""
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
        """Elimina una obra de la base de datos. Devuelve True si se eliminó la obra, o False si no se encontró ninguna obra con ese ID."""
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
