import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from utils.text_utils import normalizar_texto


class RepoReservas(AsistenteDeConsultas):
    def crear_reserva(
        self,
        id_propietario: int,
        nombre_personaje: str,
        id_obra: int,
        fecha_expiracion: str,
        enlace_imagen: str,
        id_hilo: int,
        id_mensaje: int | None = None,
    ) -> int:
        """Crea una nueva reserva en la base de datos."""

        nombre_normalizado = normalizar_texto(nombre_personaje)
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
        id_reserva = cursor.lastrowid
        if id_reserva is None:
            raise RuntimeError("No se pudo obtener el ID de la nueva reserva.")

        return id_reserva

    def obtener_reserva_por_id(self, id_reserva: int) -> sql.Row | None:
        """Obtiene una reserva por su ID."""

        return self.consulta_uno(
            """
            SELECT * FROM reservas WHERE id_reserva = ?;
        """,
            (id_reserva,),
        )

    # TODO: Revisar si es necesaria esta función
    def obtener_reservas(self) -> list[sql.Row]:
        """Obtiene todas las reservas de la base de datos."""

        return self.consulta_todos("""
            SELECT * FROM reservas;
        """)

    def obtener_reserva_por_nombre_normalizado(self, nombre: str) -> sql.Row | None:
        """Obtiene una reserva por su nombre normalizado. Devuelve la reserva más reciente si hay varias con el mismo nombre."""

        nombre_normalizado = normalizar_texto(nombre)
        return self.consulta_uno(
            """
            SELECT * FROM reservas WHERE nombre_normalizado = ? ORDER BY fecha_reserva DESC;
        """,
            (nombre_normalizado,),
        )

    # TODO: Verifica si esta función es necesaria
    def obtener_reservas_por_nombre_normalizado(self, nombre: str) -> list[sql.Row]:
        """Obtiene todas las reservas que coinciden con el nombre normalizado, ordenadas por fecha de reserva descendente."""

        nombre_normalizado = normalizar_texto(nombre)
        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE nombre_normalizado = ? ORDER BY fecha_reserva DESC;
        """,
            (nombre_normalizado,),
        )

    # TODO: Verifica si esta función es necesaria junto a la anterior
    def obtener_reservas_similares_por_nombre_normalizado(
        self, nombre: str
    ) -> list[sql.Row]:
        """Obtiene todas las reservas que contienen el nombre normalizado, ordenadas por fecha de reserva descendente."""

        nombre_normalizado = normalizar_texto(nombre)
        patron = f"%{nombre_normalizado}%"
        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE nombre_normalizado LIKE ? ORDER BY fecha_reserva DESC;
        """,
            (patron,),
        )

    def obtener_reservas_por_usuario(self, id_propietario: int) -> list[sql.Row]:
        """Obtiene todas las reservas de un usuario específico, ordenadas por fecha de reserva descendente."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE id_propietario = ? ORDER BY fecha_reserva DESC;
        """,
            (id_propietario,),
        )

    def obtener_reservas_por_obra(self, id_obra: int) -> list[sql.Row]:
        """Obtiene todas las reservas de una obra específica, ordenadas por fecha de reserva descendente."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE id_obra = ? ORDER BY fecha_reserva DESC;
        """,
            (id_obra,),
        )

    def obtener_reservas_por_usuario_y_estado(
        self, id_propietario: int, estado: str
    ) -> list[sql.Row]:
        """Obtiene todas las reservas de un usuario específico con un estado determinado, ordenadas por fecha de reserva descendente."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE id_propietario = ? AND estado = ? ORDER BY fecha_reserva DESC;
        """,
            (id_propietario, estado),
        )

    # TODO: Revisar si se está usando realmente esta función
    def obtener_reservas_por_expiracion(self, fecha_expiracion: str) -> list[sql.Row]:
        """Obtiene todas las reservas que expiran antes o en la fecha dada, ordenadas por fecha de expiración ascendente."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE fecha_expiracion <= ? ORDER BY fecha_expiracion ASC;
        """,
            (fecha_expiracion,),
        )

    # TODO: Revisar si se está usando realmente esta función, parece muy específica
    def obtener_reserva_por_nombre_y_obra(
        self, nombre: str, id_obra: int
    ) -> sql.Row | None:
        """Obtiene una reserva por su nombre normalizado y obra. Devuelve la reserva más reciente si hay varias con el mismo nombre y obra."""

        nombre_normalizado = normalizar_texto(nombre)
        return self.consulta_uno(
            """
            SELECT * FROM reservas WHERE nombre_normalizado = ? AND id_obra = ? ORDER BY fecha_reserva DESC;
        """,
            (nombre_normalizado, id_obra),
        )

    def obtener_reservas_vencidas_antiguas(self, dias: int) -> list[sql.Row]:
        """Obtiene todas las reservas que están vencidas y expiraron hace más de 'dias' días, ordenadas por fecha de expiración ascendente."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas
            WHERE estado = 'vencida'
                AND fecha_expiracion <= DATETIME('now', ?)
            ORDER BY fecha_expiracion ASC;
        """,
            (f"-{dias} days",),
        )

    def obtener_reservas_pendientes(self) -> list[sql.Row]:
        """Obtiene todas las reservas que no han sido sincronizadas con el sistema externo."""

        return self.consulta_todos(
            """
            SELECT * FROM reservas WHERE sincronizado != 0;
        """
        )

    def actualizar_expiracion_reserva(self, id_reserva: int, fecha_fin: str) -> bool:
        """Renueva la fecha de expiración de una reserva y la marca como activa."""

        cursor = self.ejecutar(
            """
            UPDATE reservas SET fecha_reserva = CURRENT_TIMESTAMP, fecha_expiracion = ?, fecha_estado = CURRENT_TIMESTAMP, estado = 'activa' WHERE id_reserva = ?;
        """,
            (fecha_fin, id_reserva),
        )
        return cursor.rowcount > 0

    def actualizar_estado_reserva(self, id_reserva: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de una reserva. El nuevo estado debe ser 'activa', 'vencida' o 'por_expirar'."""

        if nuevo_estado not in ["activa", "vencida", "por_expirar"]:
            raise ValueError("El estado debe ser 'activa', 'vencida' o 'por_expirar'.")

        cursor = self.ejecutar(
            """
            UPDATE reservas SET estado = ?, fecha_estado = CURRENT_TIMESTAMP WHERE id_reserva = ?;
        """,
            (nuevo_estado, id_reserva),
        )

        return cursor.rowcount > 0

    def actualizar_obra_e_hilo(
        self,
        id_reserva: int,
        nuevo_id_obra: int,
        nuevo_id_hilo: int,
        nuevo_id_mensaje: int,
    ) -> bool:
        """Actualiza el ID de obra, hilo y mensaje asociado a una reserva."""

        cursor = self.ejecutar(
            """
            UPDATE reservas SET id_obra = ?, id_hilo = ?, id_mensaje = ? WHERE id_reserva = ?;
        """,
            (nuevo_id_obra, nuevo_id_hilo, nuevo_id_mensaje, id_reserva),
        )

        return cursor.rowcount > 0

    # TODO: Revisar si es redundante con la función anterior
    def actualizar_mensaje_reserva(
        self, id_reserva: int, nuevo_id_mensaje: int
    ) -> bool:
        """Actualiza el ID del mensaje asociado a una reserva."""

        cursor = self.ejecutar(
            """
            UPDATE reservas SET id_mensaje = ? WHERE id_reserva = ?;
        """,
            (nuevo_id_mensaje, id_reserva),
        )

        return cursor.rowcount > 0

    # TODO: Revisar si es redundante con la función anterior
    def actualizar_obra_id_reserva(self, id_reserva: int, nuevo_id_obra: int) -> bool:
        """Actualiza el ID de obra asociado a una reserva."""

        cursor = self.ejecutar(
            """
            UPDATE reservas SET id_obra = ? WHERE id_reserva = ?;
        """,
            (nuevo_id_obra, id_reserva),
        )

        return cursor.rowcount > 0

    def actualizar_sincronizacion_reserva(
        self, id_reserva: int, nuevo_estado: int
    ) -> bool:
        """Actualiza el estado de sincronización de una reserva."""

        if nuevo_estado not in (0, 1, 2, 3):
            raise ValueError(
                "El estado de sincronización debe ser 0 (sincronizado), 1 (desincronizado), 2 (sin ID de mensaje) o 3 (referencia inválida)."
            )

        cursor = self.ejecutar(
            """
            UPDATE reservas SET sincronizado = ? WHERE id_reserva = ?;
        """,
            (nuevo_estado, id_reserva),
        )

        return cursor.rowcount > 0

    # TODO: Refactorizar servicio para eliminar esta función
    def marcarReservasVencidasPorUsuario(self, id_usuario: int) -> int:
        """Marca todas las reservas activas de un usuario como vencidas. Devuelve el número de reservas actualizadas."""

        cursor = self.ejecutar(
            """
            UPDATE reservas SET estado = 'vencida', fecha_estado = CURRENT_TIMESTAMP
            WHERE id_propietario = ? AND estado = 'activa'
        """,
            (id_usuario,),
        )

        return cursor.rowcount

    def eliminar_reserva_definitiva(self, id_reserva: int) -> bool:
        """Elimina una reserva de la base de datos. Devuelve True si se eliminó una reserva."""

        cursor = self.ejecutar(
            """
            DELETE FROM reservas WHERE id_reserva = ?;
        """,
            (id_reserva,),
        )

        return cursor.rowcount > 0
