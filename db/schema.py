from sqlite3 import Connection


def iniciarBD(conn: Connection):
    # Crear cursor
    cursor = conn.cursor()
    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY NOT NULL,
            max_fichas INTEGER DEFAULT 2,
            max_reservas INTEGER DEFAULT 2,
            duracion_reserva INTEGER DEFAULT 7,
            ultima_actividad TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

    # Tabla de obras originales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id_obra INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_obra TEXT NOT NULL UNIQUE,
            nombre_normalizado TEXT NOT NULL UNIQUE,
            id_hilo INTEGER NOT NULL UNIQUE
            );
            """)

    # Tabla de aliases de obras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alias_obras (
            id_alias INTEGER PRIMARY KEY AUTOINCREMENT,
            alias TEXT NOT NULL UNIQUE,
            alias_normalizado TEXT NOT NULL UNIQUE,
            id_obra INTEGER NOT NULL REFERENCES obras(id_obra) ON DELETE CASCADE
            );
            """)

    # Tablas fichas de personaje
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id_ficha INTEGER PRIMARY KEY AUTOINCREMENT,
            id_propietario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
            nombre_personaje TEXT NOT NULL,
            nombre_normalizado TEXT NOT NULL,
            id_obra INTEGER NOT NULL REFERENCES obras(id_obra),
            id_hilo INTEGER NOT NULL UNIQUE,
            id_mensaje INTEGER NOT NULL UNIQUE,
            estado TEXT DEFAULT 'activa' CHECK(estado IN ('activa', 'eliminada')),
            fecha_creacion  TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_estado TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

    # Tabla de reservas de personaje
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
            id_propietario INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
            nombre_personaje TEXT NOT NULL,
            nombre_normalizado TEXT NOT NULL,
            id_obra INTEGER NOT NULL REFERENCES obras(id_obra),
            fecha_reserva TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_expiracion TEXT NOT NULL,
            fecha_estado TEXT DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'activa' CHECK(estado IN ('activa', 'vencida', 'por_expirar')),
            enlace_imagen TEXT  NOT NULL,
            id_hilo INTEGER NOT NULL UNIQUE,
            id_mensaje INTEGER UNIQUE
            );
            """)

    # Índices para búsquedas por nombre normalizado
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_fichas_nombre_normalizado ON fichas(nombre_normalizado);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_reservas_nombre_normalizado ON reservas(nombre_normalizado);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_obras_nombre_normalizado ON obras(nombre_normalizado);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_alias_obras_alias ON alias_obras(alias);"""
    )

    # Índices para búsquedas por obra
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_fichas_id_obra ON fichas(id_obra);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_reservas_id_obra ON reservas(id_obra);"""
    )

    # Índices para optimizar consultas por propietario
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_fichas_propietario ON fichas(id_propietario);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_reservas_propietario ON reservas(id_propietario);"""
    )

    # Índices para búsquedas por estado y propietario
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_fichas_propietario_estado ON fichas(id_propietario, estado);"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_reservas_propietario_estado ON reservas(id_propietario, estado);"""
    )

    # Índices para búsquedas por expiración
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_reservas_expiracion ON reservas(fecha_expiracion);"""
    )

    # Guardar cambios
    conn.commit()
    cursor.close()
