import re
from rapidfuzz import fuzz, process
from unidecode import unidecode


def normalizar_texto(texto: str) -> str:
    texto = texto.replace("ꜱ", "s")
    texto = unidecode(texto)
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)

    return " ".join(texto.split())


def obtener_similitud(texto: str, opciones: list[str]) -> tuple[str | None, float]:
    if not opciones:
        return None, 0.0

    if len(texto) <= 7:
        scorer = fuzz.ratio
    else:
        scorer = fuzz.token_sort_ratio

    resultado: tuple[str, float, int] | None = process.extractOne(
        texto, opciones, scorer=scorer
    )

    if resultado:
        puntuacion = resultado[1]
        coincidencia = resultado[0]

        return coincidencia, puntuacion
    else:
        return None, 0.0


def truncar_texto(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto

    return texto[: limite - 3] + "..."
