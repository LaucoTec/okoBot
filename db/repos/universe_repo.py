import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from utils.text_utils import normalizar_texto


class RepoObras(AsistenteDeConsultas):
    def crear_obra(self, nombre_obra: str, id_hilo: int) -> int:
        """Crea una nueva obra en la base de datos. Devuelve el ID de la nueva obra."""

        nombre_normalizado = normalizar_texto(nombre_obra)
        cursor = self.ejecutar(
            """
            INSERT INTO obras (nombre_obra, nombre_normalizado, id_hilo) VALUES (?, ?, ?);
        """,
            (nombre_obra, nombre_normalizado, id_hilo),
        )
        id_obra = cursor.lastrowid
        if id_obra is None:
            raise RuntimeError("No se pudo obtener el ID de la nueva obra.")

        return id_obra

    def obtener_obra_por_id(self, id_obra: int) -> sql.Row | None:
        """Obtiene una obra por su ID. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese ID."""

        return self.consulta_uno(
            """
            SELECT * FROM obras WHERE id_obra = ?;
        """,
            (id_obra,),
        )

    # TODO: Evaluar si esta función es necesaria
    def obtener_obras(self) -> list[sql.Row]:
        """Obtiene todas las obras registradas en la base de datos, ordenadas por nombre. Devuelve una lista de objetos sql.Row con los datos de cada obra."""

        return self.consulta_todos("""
            SELECT * FROM obras ORDER BY nombre_obra;
        """)

    def obtener_obra_por_nombre_normalizado(self, nombre_obra: str) -> sql.Row | None:
        """Obtiene una obra por su nombre normalizado. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese nombre normalizado."""

        nombre_normalizado = normalizar_texto(nombre_obra)
        return self.consulta_uno(
            """
            SELECT * FROM obras WHERE nombre_normalizado = ?;
        """,
            (nombre_normalizado,),
        )

    # TODO: Evaluar si esta función es necesaria
    def buscar_obras_por_nombre_normalizado(self, nombre_obra: str) -> list[sql.Row]:
        """Busca obras cuyo nombre normalizado contenga el texto dado. Devuelve una lista de objetos sql.Row con los datos de las obras encontradas, ordenadas por nombre."""

        nombre_normalizado = normalizar_texto(nombre_obra)
        return self.consulta_todos(
            """
            SELECT * FROM obras WHERE nombre_normalizado LIKE ? ORDER BY nombre_obra;
        """,
            (f"%{nombre_normalizado}%",),
        )

    def obtener_obra_por_hilo(self, id_hilo: int) -> sql.Row | None:
        """Obtiene una obra por el ID de su hilo asociado. Devuelve un objeto sql.Row con los datos de la obra, o None si no se encontró ninguna obra con ese ID de hilo."""

        return self.consulta_uno(
            """
            SELECT * FROM obras WHERE id_hilo = ?;
        """,
            (id_hilo,),
        )

    # TODO: Evaluar si esta función es necesaria
    def actualizar_obra(self, id_obra: int, nombre_obra: str) -> bool:
        """Actualiza el nombre de una obra. Devuelve True si se actualizó la obra, o False si no se encontró ninguna obra con ese ID."""

        nombre_normalizado = normalizar_texto(nombre_obra)
        cursor = self.ejecutar(
            """
            UPDATE obras SET nombre_obra = ?, nombre_normalizado = ? WHERE id_obra = ?;
        """,
            (nombre_obra, nombre_normalizado, id_obra),
        )

        return cursor.rowcount > 0

    def eliminar_obra(self, id_obra: int) -> bool:
        """Elimina una obra de la base de datos. Devuelve True si se eliminó la obra, o False si no se encontró ninguna obra con ese ID."""

        cursor = self.ejecutar(
            """
            DELETE FROM obras WHERE id_obra = ?;
        """,
            (id_obra,),
        )

        return cursor.rowcount > 0
