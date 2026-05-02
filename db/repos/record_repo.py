import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger
from utils.text_utils import normalizar_texto


class RepoFichas(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)

    def crearFicha(
        self,
        id_propietario: int,
        nombre_personaje: str,
        id_obra: int,
        id_hilo: int,
        id_mensaje: int,
    ):
        try:
            nombre_normalizado = normalizar_texto(nombre_personaje)
            cursor = self.ejecutar(
                """
                INSERT INTO fichas (id_propietario, nombre_personaje, nombre_normalizado, id_obra, id_hilo, id_mensaje) 
                VALUES (?, ?, ?, ?, ?, ?);
            """,
                (
                    id_propietario,
                    nombre_personaje,
                    nombre_normalizado,
                    id_obra,
                    id_hilo,
                    id_mensaje,
                ),
            )

            return cursor.lastrowid if cursor is not None else None

        except sql.Error as e:
            logger.error(
                f"Error creando ficha para usuario {id_propietario}: {e}", exc_info=True
            )
            raise

    def obtenerFicha(self, id_ficha: int):
        try:
            return self.consultaUno(
                """
                SELECT * FROM fichas WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo ficha {id_ficha}: {e}", exc_info=True)
            return None

    def obtenerFichaPorNombreNormalizado(self, nombre_normalizado: str):
        try:
            return self.consultaUno(
                """
                SELECT * FROM fichas WHERE nombre_normalizado = ?;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo ficha por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return None

    def obtenerFichasPorNombreNormalizado(self, nombre_normalizado: str):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas WHERE nombre_normalizado = ? ORDER BY fecha_creacion DESC;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return []

    def obtenerFichasPorUsuario(self, id_propietario: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas WHERE id_propietario = ? ORDER BY fecha_creacion DESC;
            """,
                (id_propietario,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para usuario {id_propietario}: {e}",
                exc_info=True,
            )
            return []

    def obtenerFichasActivasPorUsuario(self, id_propietario: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas WHERE id_propietario = ? AND estado = 'activa' ORDER BY fecha_creacion DESC;
            """,
                (id_propietario,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas activas para usuario {id_propietario}: {e}",
                exc_info=True,
            )
            return []

    def obtenerFichasPorObra(self, id_obra: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas WHERE id_obra = ? ORDER BY fecha_creacion DESC;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para obra {id_obra}: {e}", exc_info=True
            )
            return []

    def obtenerFichasPorUsuarioEstado(self, id_propietario: int, estado: str):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas WHERE id_propietario = ? AND estado = ? ORDER BY fecha_creacion DESC;
            """,
                (id_propietario, estado),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas para usuario {id_propietario} con estado '{estado}': {e}",
                exc_info=True,
            )
            return []

    def actualizarNombreFicha(self, id_ficha: int, nuevo_nombre: str):
        try:
            nombre_normalizado = normalizar_texto(nuevo_nombre)
            cursor = self.ejecutar(
                """
                UPDATE fichas SET nombre_personaje = ?, nombre_normalizado = ? WHERE id_ficha = ?;
            """,
                (nuevo_nombre, nombre_normalizado, id_ficha),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando nombre de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def actualizarObraFicha(self, id_ficha: int, nuevo_id_obra: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET id_obra = ? WHERE id_ficha = ?;
            """,
                (nuevo_id_obra, id_ficha),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando obra de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def actualizarEstadoFicha(self, id_ficha: int, nuevo_estado: str):
        if nuevo_estado not in ("activa", "eliminada"):
            logger.warning(f"Estado inválido para ficha {id_ficha}: {nuevo_estado}")
            return False

        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = ?, fecha_estado = CURRENT_TIMESTAMP WHERE id_ficha = ?;
            """,
                (nuevo_estado, id_ficha),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando estado de ficha {id_ficha}: {e}", exc_info=True
            )
            raise

    def eliminarFicha(self, id_ficha: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = 'eliminada', fecha_estado = CURRENT_TIMESTAMP WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error eliminando ficha {id_ficha}: {e}", exc_info=True)
            raise

    def obtenerTodasFichas(self):
        try:
            return self.consultaTodos("""
                SELECT * FROM fichas;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las fichas: {e}", exc_info=True)
            return []

    def obtenerFichasEliminadasAntiguas(self, dias: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM fichas
                WHERE estado = 'eliminada'
                  AND fecha_estado <= DATETIME('now', ?)
            """,
                (f"-{dias} days",),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo fichas eliminadas antiguas: {e}", exc_info=True
            )
            return []

    def marcarFichasEliminadasPorUsuario(self, id_usuario: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE fichas SET estado = 'eliminada', fecha_estado = CURRENT_TIMESTAMP
                WHERE id_propietario = ? AND estado = 'activa'
            """,
                (id_usuario,),
            )

            return cursor is not None and cursor.rowcount

        except sql.Error as e:
            logger.error(
                f"Error marcando fichas como eliminadas para usuario {id_usuario}: {e}",
                exc_info=True,
            )
            raise

    def eliminarFichaDefinitiva(self, id_ficha: int):
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM fichas WHERE id_ficha = ?;
            """,
                (id_ficha,),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error eliminando definitivamente ficha {id_ficha}: {e}", exc_info=True
            )
            raise
