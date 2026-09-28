from contextvars import ContextVar
from sqlite3 import Connection, Cursor, Row
from typing import Any

en_transaccion_var: ContextVar[bool] = ContextVar("en_transaccion", default=False)


class AsistenteDeConsultas:
    def __init__(self, conexion: Connection):
        self.conexion = conexion

    def ejecutar(self, consulta: str, parametros: tuple[Any, ...] = ()) -> Cursor:
        cursor = self.conexion.cursor()
        try:
            cursor.execute(consulta, parametros)
        except Exception:
            self.conexion.rollback()
            raise

        if not en_transaccion_var.get():
            self.conexion.commit()

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
