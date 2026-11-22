import sqlite3 as sql

from db.queries import AsistenteDeConsultas
from utils.text_utils import normalizar_texto


class RepoFichas(AsistenteDeConsultas):
    def crear_ficha(
        self,
        id_propietario: int,
        nombre_personaje: str,
        id_obra: int,
        id_hilo: int,
        id_mensaje: int,
    ) -> int:
        """Crea una nueva ficha de personaje para un usuario en una obra específica."""

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

        id_ficha = cursor.lastrowid
        if id_ficha is None:
            raise RuntimeError("No se pudo obtener el ID de la nueva ficha.")

        return id_ficha

    def obtener_ficha_por_id(self, id_ficha: int) -> sql.Row | None:
        """Obtiene una ficha de personaje por su ID."""

        return self.consulta_uno(
            """
            SELECT * FROM fichas WHERE id_ficha = ?;
        """,
            (id_ficha,),
        )

    def obtener_fichas(self) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes registradas en la base de datos."""

        return self.consulta_todos("""
            SELECT * FROM fichas;
        """)

    def obtener_ficha_por_nombre_normalizado(
        self, nombre_normalizado: str
    ) -> sql.Row | None:
        """Obtiene una ficha de personaje por su nombre normalizado."""

        return self.consulta_uno(
            """
            SELECT * FROM fichas WHERE nombre_normalizado = ?;
        """,
            (nombre_normalizado,),
        )

    # TODO: Revisar si es necesaria esta función
    def obtener_fichas_por_nombre_normalizado(
        self, nombre_normalizado: str
    ) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes que coinciden con un nombre normalizado."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas WHERE nombre_normalizado = ? ORDER BY fecha_creacion DESC;
        """,
            (nombre_normalizado,),
        )

    def obtener_fichas_por_usuario(self, id_propietario: int) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes creadas por un usuario específico."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas WHERE id_propietario = ? ORDER BY fecha_creacion DESC;
        """,
            (id_propietario,),
        )

    def obtener_fichas_por_obra(self, id_obra: int) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes asociadas a una obra específica."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas WHERE id_obra = ? ORDER BY fecha_creacion DESC;
        """,
            (id_obra,),
        )

    def obtener_fichas_por_usuario_y_estado(
        self, id_propietario: int, estado: str
    ) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes creadas por un usuario específico con un estado determinado (activa o eliminada)."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas WHERE id_propietario = ? AND estado = ? ORDER BY fecha_creacion DESC;
        """,
            (id_propietario, estado),
        )

    def obtener_fichas_eliminadas_antiguas(self, dias: int) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes que han estado en estado 'eliminada' por más de un número determinado de días."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas
            WHERE estado = 'eliminada'
                AND fecha_estado <= DATETIME('now', ?)
        """,
            (f"-{dias} days",),
        )

    def obtener_fichas_pendientes(self) -> list[sql.Row]:
        """Obtiene todas las fichas de personajes que no han sido sincronizadas con el sistema externo."""

        return self.consulta_todos(
            """
            SELECT * FROM fichas WHERE sincronizado != 0;
        """
        )

    def actualizar_nombre_ficha(self, id_ficha: int, nuevo_nombre: str) -> bool:
        """Actualiza el nombre de un personaje en una ficha específica."""

        nombre_normalizado = normalizar_texto(nuevo_nombre)
        cursor = self.ejecutar(
            """
            UPDATE fichas SET nombre_personaje = ?, nombre_normalizado = ? WHERE id_ficha = ?;
        """,
            (nuevo_nombre, nombre_normalizado, id_ficha),
        )

        return cursor.rowcount > 0

    def actualizar_obra_ficha(self, id_ficha: int, nuevo_id_obra: int) -> bool:
        """Actualiza la obra asociada a una ficha de personaje específica."""

        cursor = self.ejecutar(
            """
            UPDATE fichas SET id_obra = ? WHERE id_ficha = ?;
        """,
            (nuevo_id_obra, id_ficha),
        )

        return cursor.rowcount > 0

    def actualizar_estado_ficha(self, id_ficha: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de una ficha de personaje específica (activa o eliminada)."""

        if nuevo_estado not in ("activa", "eliminada"):
            raise ValueError("El estado debe ser 'activa' o 'eliminada'.")

        cursor = self.ejecutar(
            """
            UPDATE fichas SET estado = ?, fecha_estado = CURRENT_TIMESTAMP WHERE id_ficha = ?;
        """,
            (nuevo_estado, id_ficha),
        )

        return cursor.rowcount > 0

    def actualizar_sincronizacion_ficha(self, id_ficha: int, nuevo_estado: int) -> bool:
        """Actualiza el estado de sincronización de una ficha de personaje específica."""

        if nuevo_estado not in (0, 1, 2, 3):
            raise ValueError(
                "El estado de sincronización debe ser 0 (sincronizado), 1 (desincronizado), 2 (sin ID de mensaje) o 3 (referencia inválida)."
            )

        cursor = self.ejecutar(
            """
            UPDATE fichas SET sincronizado = ? WHERE id_ficha = ?;
        """,
            (nuevo_estado, id_ficha),
        )

        return cursor.rowcount > 0

    def eliminar_ficha_definitivo(self, id_ficha: int) -> bool:
        """Elimina definitivamente una ficha de personaje de la base de datos."""

        cursor = self.ejecutar(
            """
            DELETE FROM fichas WHERE id_ficha = ?;
        """,
            (id_ficha,),
        )

        return cursor.rowcount > 0
