import os
from collections import deque
from datetime import datetime, timezone

LOG_FILE = "./logs/RegistroSeguro.log"

def existe_archivo(archivo):
    return os.path.exists(archivo)

def archivo_vacio(archivo):
    return  os.path.getsize(archivo) == 0

def get_tiempo_legible():
    """
    Devuelve el tiempo actual en un formato legible
    """
    # Obtener la hora actual en UTC
    tiempo_utc = datetime.now(timezone.utc)

    # Formatear la hora en UTC con la zona horaria
    tiempo_legible = tiempo_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    return tiempo_legible

def read_last_line(file_path) -> str:
    with open(file_path, 'r') as file:
        last_line = deque(file, maxlen=1)[0].strip()
        return last_line
