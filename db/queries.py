from sqlite3 import Connection, Cursor, Row
from typing import Any


class AsistenteDeConsultas:
    def __init__(self, conexion: Connection):
        self.conexion = conexion

    def ejecutar(self, consulta: str, parametros: tuple[Any, ...] = ()) -> Cursor:
        with self.conexion:
            cursor = self.conexion.execute(consulta, parametros)
        return cursor

    def consulta_uno(
        self, consulta: str, parametros: tuple[Any, ...] = ()
    ) -> Row | None:
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchone()

    def consulta_todos(
        self, consulta: str, parametros: tuple[Any, ...] = ()
    ) -> list[Row]:
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchall()
