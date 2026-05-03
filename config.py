import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
# Oko
ID_SERVER = int(os.getenv("ID_SERVER"))
# ID de rol Verificador
ID_VERIFICADOR = int(os.getenv("ID_VERIFICADOR"))
# ID canal general
ID_GENERAL = int(os.getenv("ID_GENERAL"))
# ID canal de verificación
ID_VERIFICACION = int(os.getenv("ID_VERIFICACION"))
# ID de canal de advertencias por inactividad
ID_ADVERTENCIAS = int(os.getenv("ID_ADVERTENCIAS"))
# ID de canal de repositorio de imágenes
ID_REPOSITORIO = int(os.getenv("ID_REPOSITORIO"))
# ID foro de reservas
ID_RESERVAS = int(os.getenv("ID_RESERVAS"))
# ID de logs de obras y alias
ID_LOGS_OBRAS = int(os.getenv("ID_LOGS_OBRAS"))
# ID de logs de reservas
ID_LOGS_RESERVAS = int(os.getenv("ID_LOGS_RESERVAS"))
# Id de logs de fichas
ID_LOGS_FICHAS = int(os.getenv("ID_LOGS_FICHAS"))
