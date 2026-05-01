import re
from unidecode import unidecode
from config import ID_VERIFICADOR
from discord import Member

def normStr(s: str) -> str:
    s = s.replace("ꜱ", "s")
    s = unidecode(s)
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())

def esVerificador(miembro: Member) -> bool:
    return ID_VERIFICADOR in [role.id for role in miembro.roles]