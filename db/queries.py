class AsistenteDeConsultas:
    def __init__(self, conexion):
        self.conexion = conexion

    def ejecutar(self, consulta: str, parametros: tuple = ()):
        with self.conexion:
            cursor = self.conexion.execute(consulta, parametros)
        return cursor

    def consultaUno(self, consulta: str, parametros: tuple = ()):
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchone()

    def consultaTodos(self, consulta: str, parametros: tuple = ()):
        cursor = self.conexion.execute(consulta, parametros)
        return cursor.fetchall()
