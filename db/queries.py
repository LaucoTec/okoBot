from sqlite3 import Connection, Row


class AsistenteDeConsultas:
    def __init__(self, conexion):
        self.conexion = conexion

    def ejecutar(self, consulta: str, parametros: tuple = ()) -> Connection.cursor:
        with self.conexion:
            cursor = self.conexion.execute(consulta, parametros)
        return cursor

    def consulta_uno(self, consulta: str, parametros: tuple = ()) -> Row | None:
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchone()

    def consulta_todos(self, consulta: str, parametros: tuple = ()) -> list[Row]:
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchall()
