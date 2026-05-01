# okoBot - Feu

Bot de Discord desarrollado en Python usando `discord.py` y `SQLite`.

Actualmente enfocado en sistemas de rol para servidores privados, incluyendo reservas de apariencia, gestión de usuarios, alias de obras y automatización básica.

---

# Características actuales

## Sistema de reservas

* Crear reservas de apariencia mediante modal.
* Adjuntar imágenes automáticamente.
* Validación de duplicados.
* Detección fuzzy de nombres similares.
* Renovación de reservas.
* Eliminación de reservas propias.
* Eliminación administrativa.
* Movimiento de reservas entre obras.
* Expiración automática.
* Logs visuales.
* Catálogo interactivo con botones y selects.

## Sistema de alias

* Crear alias para obras.
* Eliminar alias.
* Buscar obras mediante alias.
* Visualización interactiva de aliases.

## Usuarios

* Registro automático.
* Control de actividad.
* Límites personalizados.
* Gestión de fichas y reservas.

## Logging

* Logger separado para:

  * Base de datos
  * Runtime del bot
  * Auditoría

* Rotación automática de archivos.

---

# Tecnologías utilizadas

* Python 3.13
* discord.py
* SQLite
* python-dotenv
* rapidfuzz

---

# Estructura del proyecto

```text
okoBot/
│
├── .git/
├── .venv/
│
├── cogs/
│   ├── aliases_cog.py
│   ├── events_cog.py
│   ├── general_cog.py
│   ├── records_cog.py
│   ├── reservations_cog.py
│   ├── tasks_cog.py
│   ├── users_cog.py
│   └── __init__.py
│
├── db/
│   ├── repos/
│   │   ├── alias_repo.py
│   │   ├── record_repo.py
│   │   ├── reservation_repo.py
│   │   ├── universe_repo.py
│   │   ├── user_repo.py
│   │   └── __init__.py
│   │
│   ├── database.py
│   ├── okoBot.db
│   ├── queries.py
│   ├── schema.py
│   └── __init__.py
│
├── embeds/
│   └── __init__.py
│
├── logs/
│   ├── files/
│   │   └── database.log
│   │
│   ├── loggers/
│   │   ├── audit_logger.py
│   │   ├── bot_logger.py
│   │   ├── db_logger.py
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── services/
│   └── __init__.py
│
├── utils/
│   ├── utils.py
│   └── __init__.py
│
├── views/
│   └── __init__.py
│
├── .env
├── .gitignore
├── config.py
├── main.py
├── README.md
└── requirements.txt
```

---

# Instalación

## 1. Clonar el repositorio

```bash
git clone <repo>
cd okoBot
```

---

## 2. Crear entorno virtual

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Crear archivo `.env`

Crear un archivo llamado `.env` en la raíz del proyecto.

Ejemplo:

```env
TOKEN=TU_TOKEN
ID_SERVER=123456789
ID_VERIFICADOR=123456789
ID_GENERAL=123456789
ID_VERIFICACION=123456789
ID_ADVERTENCIAS=123456789
ID_REPOSITORIO=123456789
ID_RESERVAS=123456789
ID_LOGS_RESERVAS=123456789
```

---

## 5. Ejecutar el bot

```bash
python main.py
```

---

# Estado del proyecto

Proyecto actualmente en desarrollo activo.

La arquitectura está siendo refactorizada progresivamente para separar:

* lógica Discord
* servicios
* vistas
* embeds
* acceso a base de datos

---

# Objetivos futuros

* Persistencia de Views.
* Mejor separación por capas.
* Sistema completo de fichas.
* Más herramientas administrativas.
* Optimización de servicios.
* Mejor sistema de auditoría.

---

# Notas

Este bot fue desarrollado principalmente como proyecto personal y de aprendizaje, enfocado en:

* arquitectura de bots Discord
* SQLite
* diseño modular
* automatización
* sistemas interactivos con Views y Modals

---

# Licencia

Uso privado/personal.
