from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

ZH_CDMX = ZoneInfo("America/Mexico_City")


def generar_hora_cdmx(h: int, m: int, s: int) -> time:
    return time(hour=h, minute=m, second=s, tzinfo=ZH_CDMX)


def obtener_fecha_cdmx() -> datetime:
    return datetime.now(tz=ZH_CDMX)


def str_a_fecha(fecha: str) -> datetime:
    return datetime.strptime(fecha, "%d/%m/%Y")


def fecha_a_str(fecha: datetime) -> str:
    return fecha.date().strftime("%d/%m/%Y")


def fecha_iso(fecha: datetime) -> str:
    return fecha.date().isoformat()


def fecha_fin(dias: int, inicio: datetime | None = None) -> datetime:
    hoy = inicio or obtener_fecha_cdmx()

    return hoy + timedelta(days=dias)
