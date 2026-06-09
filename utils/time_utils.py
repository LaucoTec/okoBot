from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ZH_CDMX = ZoneInfo("America/Mexico_City")


def generar_hora_cdmx(h: int, m: int, s: int) -> time:
    return time(hour=h, minute=m, second=s, tzinfo=ZH_CDMX)


def obtener_fecha_cdmx() -> datetime:
    return datetime.now(tz=ZH_CDMX)


def str_a_fecha(fecha: str) -> date:
    return datetime.strptime(fecha, "%d/%m/%Y").date()


def fecha_a_str(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


def fecha_iso(fecha: date) -> str:
    return fecha.isoformat()


def fecha_fin(dias: int, inicio: date | None = None) -> date:
    hoy = inicio or obtener_fecha_cdmx().date()

    return hoy + timedelta(days=dias)
