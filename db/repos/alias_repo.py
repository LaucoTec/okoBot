import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers import db_logger as logger
from utils import normalizar_texto


class RepoAliasObras(AsistenteDeConsultas):
    def crear_alias_obra(self, alias: str, id_obra: int) -> int | None:
        """Crea un nuevo alias para una obra."""
        try:
            nombre_normalizado = normalizar_texto(alias)
            cursor = self.ejecutar(
                """
                INSERT INTO alias_obras (alias, id_obra, alias_normalizado) VALUES (?, ?, ?);
            """,
                (alias, id_obra, nombre_normalizado),
            )

            return cursor.lastrowid

        except sql.Error as e:
            logger.error(
                f"Error creando alias '{alias}' para obra {id_obra}: {e}", exc_info=True
            )
            raise

    def obtener_aliases_obras(self) -> list[sql.Row]:
        """Obtiene todos los alias de obras registrados."""
        try:
            return self.consulta_todos("""
                SELECT * FROM alias_obras;
            """)

        except sql.Error as e:
            logger.error(
                f"Error obteniendo todos los alias de obras: {e}", exc_info=True
            )
            return []

    def obtener_alias_por_id(self, id_alias: int) -> sql.Row | None:
        """Obtiene un alias de obra por su ID."""
        try:
            return self.consulta_uno(
                """
                SELECT * FROM alias_obras WHERE id_alias = ?;
            """,
                (id_alias,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo alias {id_alias}: {e}", exc_info=True)
            return None

    def obtener_aliases_por_id_obra(self, id_obra: int) -> list[sql.Row]:
        """Obtiene todos los alias asociados a una obra por su ID."""
        try:
            return self.consulta_todos(
                """
                SELECT * FROM alias_obras WHERE id_obra = ?;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo aliases para obra {id_obra}: {e}", exc_info=True
            )
            return []

    def obtener_aliases_por_nombre(self, nombre_alias: str) -> list[sql.Row]:
        """Busca alias de obras que coincidan parcialmente con un nombre dado."""
        try:
            nombre_normalizado = normalizar_texto(nombre_alias)
            return self.consulta_todos(
                """
                SELECT * FROM alias_obras WHERE alias_normalizado LIKE ? ORDER BY alias;
            """,
                (f"%{nombre_normalizado}%",),
            )

        except sql.Error as e:
            logger.error(
                f"Error buscando aliases por nombre '{nombre_alias}': {e}",
                exc_info=True,
            )
            return []

    def obtener_alias_por_nombre_exacto(self, nombre_alias: str) -> sql.Row | None:
        """Busca un alias de obra que coincida exactamente con un nombre dado."""
        try:
            nombre_normalizado = normalizar_texto(nombre_alias)
            return self.consulta_uno(
                """
                SELECT * FROM alias_obras WHERE alias_normalizado = ? ORDER BY alias;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error buscando aliases por nombre '{nombre_alias}': {e}",
                exc_info=True,
            )
            return None

    def obtener_obra_por_alias(self, alias: str) -> sql.Row | None:
        """Obtiene la obra asociada a un alias dado."""
        try:
            nombre_normalizado = normalizar_texto(alias)
            return self.consulta_uno(
                """
                SELECT o.* FROM obras o
                JOIN alias_obras a ON o.id_obra = a.id_obra
                WHERE a.alias_normalizado = ?;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo obra por alias '{alias}': {e}", exc_info=True
            )
            return None

    def eliminar_alias_obra(self, id_alias: int) -> bool:
        """Elimina un alias de obra por su ID."""
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM alias_obras WHERE id_alias = ?;
            """,
                (id_alias,),
            )

            return cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando alias {id_alias}: {e}", exc_info=True)
            raise
