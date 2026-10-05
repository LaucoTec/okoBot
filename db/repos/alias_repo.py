import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from utils import normalizar_texto


class RepoAliasObras(AsistenteDeConsultas):
    def crear_alias_obra(self, alias: str, id_obra: int) -> int:
        """Crea un nuevo alias para una obra."""

        nombre_normalizado = normalizar_texto(alias)

        cursor = self.ejecutar(
            """
            INSERT INTO alias_obras (alias, id_obra, alias_normalizado) VALUES (?, ?, ?);
        """,
            (alias, id_obra, nombre_normalizado),
        )

        nuevo_alias = cursor.lastrowid
        if nuevo_alias is None:
            raise RuntimeError("No se pudo obtener el ID del nuevo alias.")

        return nuevo_alias

    def obtener_aliases_obras(self) -> list[sql.Row]:
        """Obtiene todos los alias de obras registrados."""

        return self.consulta_todos("""
            SELECT * FROM alias_obras;
        """)

    def obtener_alias_por_id(self, id_alias: int) -> sql.Row | None:
        """Obtiene un alias de obra por su ID."""

        return self.consulta_uno(
            """
            SELECT * FROM alias_obras WHERE id_alias = ?;
        """,
            (id_alias,),
        )

    def obtener_aliases_por_id_obra(self, id_obra: int) -> list[sql.Row]:
        """Obtiene todos los alias asociados a una obra por su ID."""

        return self.consulta_todos(
            """
            SELECT * FROM alias_obras WHERE id_obra = ?;
        """,
            (id_obra,),
        )

    def obtener_aliases_por_nombre(self, nombre_alias: str) -> list[sql.Row]:
        """Busca alias de obras que coincidan parcialmente con un nombre dado."""

        nombre_normalizado = normalizar_texto(nombre_alias)

        return self.consulta_todos(
            """
            SELECT * FROM alias_obras WHERE alias_normalizado LIKE ? ORDER BY alias;
        """,
            (f"%{nombre_normalizado}%",),
        )

    def obtener_alias_por_nombre_exacto(self, nombre_alias: str) -> sql.Row | None:
        """Busca un alias de obra que coincida exactamente con un nombre dado."""

        nombre_normalizado = normalizar_texto(nombre_alias)

        return self.consulta_uno(
            """
            SELECT * FROM alias_obras WHERE alias_normalizado = ? ORDER BY alias;
        """,
            (nombre_normalizado,),
        )

    def obtener_obra_por_alias(self, alias: str) -> sql.Row | None:
        """Obtiene la obra asociada a un alias dado."""

        nombre_normalizado = normalizar_texto(alias)

        return self.consulta_uno(
            """
            SELECT o.* FROM obras o
            JOIN alias_obras a ON o.id_obra = a.id_obra
            WHERE a.alias_normalizado = ?;
        """,
            (nombre_normalizado,),
        )

    def eliminar_alias_obra(self, id_alias: int) -> bool:
        """Elimina un alias de obra por su ID."""

        cursor = self.ejecutar(
            """
            DELETE FROM alias_obras WHERE id_alias = ?;
        """,
            (id_alias,),
        )

        return cursor.rowcount > 0
