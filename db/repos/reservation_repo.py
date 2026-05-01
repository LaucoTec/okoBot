import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from logs.loggers.db_logger import logger
from utils.utils import normStr


class RepoReservas(AsistenteDeConsultas):
    def __init__(self, conexion):
        super().__init__(conexion)

    def crearReserva(
        self,
        id_propietario: int,
        nombre_personaje: str,
        id_obra: int,
        fecha_expiracion: str,
        enlace_imagen: str,
        id_hilo: int,
        id_mensaje=None,
    ):
        try:
            nombre_normalizado = normStr(nombre_personaje)
            cursor = self.ejecutar(
                """
                INSERT INTO reservas (id_propietario, nombre_personaje, nombre_normalizado, id_obra, fecha_expiracion, enlace_imagen, id_hilo, id_mensaje) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
                (
                    id_propietario,
                    nombre_personaje,
                    nombre_normalizado,
                    id_obra,
                    fecha_expiracion,
                    enlace_imagen,
                    id_hilo,
                    id_mensaje,
                ),
            )

            return cursor.lastrowid if cursor is not None else None

        except sql.Error as e:
            logger.error(
                f"Error creando reserva para usuario {id_propietario}: {e}",
                exc_info=True,
            )
            raise

    def obtenerReserva(self, id_reserva: int):
        try:
            return self.consultaUno(
                """
                SELECT * FROM reservas WHERE id_reserva = ?;
            """,
                (id_reserva,),
            )

        except sql.Error as e:
            logger.error(f"Error obteniendo reserva {id_reserva}: {e}", exc_info=True)
            return None

    def obtenerReservaPorNombreNormalizado(self, nombre: str):
        try:
            nombre_normalizado = normStr(nombre)
            return self.consultaUno(
                """
                SELECT * FROM reservas WHERE nombre_normalizado = ?;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reserva por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return None

    def obtenerReservasPorNombreNormalizado(self, nombre: str):
        try:
            nombre_normalizado = normStr(nombre)
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE nombre_normalizado = ? ORDER BY fecha_reserva DESC;
            """,
                (nombre_normalizado,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return []

    def obtenerReservasSimilaresPorNombreNormalizado(self, nombre: str):
        try:
            nombre_normalizado = normStr(nombre)
            patron = f"%{nombre_normalizado}%"
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE nombre_normalizado LIKE ? ORDER BY fecha_reserva DESC;
            """,
                (patron,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas por nombre '{nombre_normalizado}': {e}",
                exc_info=True,
            )
            return []

    def obtenerReservasPorUsuario(self, id_propietario: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE id_propietario = ? ORDER BY fecha_reserva DESC;
            """,
                (id_propietario,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas para usuario {id_propietario}: {e}",
                exc_info=True,
            )
            return []

    def obtenerReservasPorObra(self, id_obra: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE id_obra = ? ORDER BY fecha_reserva DESC;
            """,
                (id_obra,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas para obra {id_obra}: {e}", exc_info=True
            )
            return []

    def obtenerReservasPorUsuarioEstado(self, id_propietario: int, estado: str):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE id_propietario = ? AND estado = ? ORDER BY fecha_reserva DESC;
            """,
                (id_propietario, estado),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas para usuario {id_propietario} con estado '{estado}': {e}",
                exc_info=True,
            )
            return []

    def obtenerReservasPorExpiracion(self, fecha_expiracion: str):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM reservas WHERE fecha_expiracion <= ? ORDER BY fecha_expiracion ASC;
            """,
                (fecha_expiracion,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas por expiración {fecha_expiracion}: {e}",
                exc_info=True,
            )
            return []

    def obtenerReservaPorNombreYObra(self, nombre: str, id_obra: int):
        try:
            nombre_normalizado = normStr(nombre)
            return self.consultaUno(
                """
                SELECT * FROM reservas WHERE nombre_normalizado = ? AND id_obra = ?;
            """,
                (nombre_normalizado, id_obra),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reserva por nombre '{nombre_normalizado}' y obra {id_obra}: {e}",
                exc_info=True,
            )
            return None

    def renovarReserva(self, id_reserva: int, fecha_fin: str):
        try:
            cursor = self.ejecutar(
                """
                                   UPDATE reservas SET fecha_reserva = CURRENT_TIMESTAMP, fecha_expiracion = ?, fecha_estado = CURRENT_TIMESTAMP, estado = 'activa' WHERE id_reserva = ?;
                                   """,
                (fecha_fin, id_reserva),
            )
            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(f"Error renovando la reserva {id_reserva}: {e}", exc_info=True)
            raise

    def actualizarEstadoReserva(self, id_reserva: int, nuevo_estado: str):
        if nuevo_estado not in ("activa", "vencida", "por_expirar"):
            logger.warning(f"Estado inválido para reserva {id_reserva}: {nuevo_estado}")
            return False

        try:
            cursor = self.ejecutar(
                """
                UPDATE reservas SET estado = ?, fecha_estado = CURRENT_TIMESTAMP WHERE id_reserva = ?;
            """,
                (nuevo_estado, id_reserva),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando estado de reserva {id_reserva}: {e}", exc_info=True
            )
            raise

    def editarReserva(
        self,
        id_reserva: int,
        nuevo_id_obra: int,
        nuevo_id_hilo: int,
        nuevo_id_mensaje: int,
    ):
        try:
            cursor = self.ejecutar(
                """
                UPDATE reservas SET id_obra = ?, id_hilo = ?, id_mensaje = ? WHERE id_reserva = ?;
            """,
                (nuevo_id_obra, nuevo_id_hilo, nuevo_id_mensaje, id_reserva),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando mensaje de reserva {id_reserva}: {e}",
                exc_info=True,
            )
            raise

    def editarMensajeIdReserva(self, id_reserva: int, nuevo_id_mensaje: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE reservas SET id_mensaje = ? WHERE id_reserva = ?;
            """,
                (nuevo_id_mensaje, id_reserva),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando mensaje de reserva {id_reserva}: {e}",
                exc_info=True,
            )
            raise

    def editarObraIdReserva(self, id_reserva: int, nuevo_id_obra: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE reservas SET id_obra = ? WHERE id_reserva = ?;
            """,
                (nuevo_id_obra, id_reserva),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error actualizando mensaje de reserva {id_reserva}: {e}",
                exc_info=True,
            )
            raise

    def obtenerTodasReservas(self):
        try:
            return self.consultaTodos("""
                SELECT * FROM reservas;
            """)

        except sql.Error as e:
            logger.error(f"Error obteniendo todas las reservas: {e}", exc_info=True)
            return []

    def obtenerReservasVencidasAntiguas(self, dias: int):
        try:
            return self.consultaTodos(
                """
                SELECT * FROM reservas
                WHERE estado = 'vencida'
                  AND fecha_expiracion <= DATETIME('now', ?)
            """,
                (f"-{dias} days",),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo reservas vencidas antiguas: {e}", exc_info=True
            )
            return []

    def marcarReservasVencidasPorUsuario(self, id_usuario: int):
        try:
            cursor = self.ejecutar(
                """
                UPDATE reservas SET estado = 'vencida', fecha_estado = CURRENT_TIMESTAMP
                WHERE id_propietario = ? AND estado = 'activa'
            """,
                (id_usuario,),
            )

            return cursor is not None and cursor.rowcount

        except sql.Error as e:
            logger.error(
                f"Error marcando reservas como vencidas para usuario {id_usuario}: {e}",
                exc_info=True,
            )
            raise

    def eliminarReservaDefinitiva(self, id_reserva: int):
        try:
            cursor = self.ejecutar(
                """
                DELETE FROM reservas WHERE id_reserva = ?;
            """,
                (id_reserva,),
            )

            return cursor is not None and cursor.rowcount > 0

        except sql.Error as e:
            logger.error(
                f"Error eliminando definitivamente reserva {id_reserva}: {e}",
                exc_info=True,
            )
            raise

    def obtenerAutorDeReserva(self, id_reserva: int):
        try:
            return self.consultaUno(
                """
                SELECT u.* FROM usuarios u
                JOIN reservas r ON u.id_usuario = r.id_propietario
                WHERE r.id_reserva = ?;
            """,
                (id_reserva,),
            )

        except sql.Error as e:
            logger.error(
                f"Error obteniendo autor de reserva {id_reserva}: {e}", exc_info=True
            )
            return None
