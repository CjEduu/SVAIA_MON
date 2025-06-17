from dataclasses import dataclass
from functools import lru_cache
from os import path
from typing import Optional

from fastapi import FastAPI

from . import config
from .CVES import ParsedCVE
from .cycloneDX import CydxSBOM
from .secure_log_manager.src.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)
from .utils_cve import find_cves_for_sbom


@dataclass
class ResultError:
    err_str: Optional[str]
    result: bool

@lru_cache
def get_config():
    return config.Settings()


# TODO Make this customizable
log_path = path.join("logs","sbom_analyzer.log")
if not path.exists(log_path):
    open(log_path,'x').close()


log_manager = SecureLogManager(debug_mode=10)
log_manager.configure_logging(log_path)
log_manager.inicializar_log()
log_function = monitor_funciones(log_manager)

app = FastAPI()

@app.post('/analizar_sbom')
def forward_sbom(sbom: CydxSBOM):
    result = analyse_sbom(sbom)    
    return result

@log_function("debug")
def analyse_sbom(sbom: CydxSBOM)->dict:
    """
        Analyses the sbom with the needed techniques, ai, checking vs CVEs...
    """
    cves_list:list[ParsedCVE] = find_cves_for_sbom(sbom)
    level_to_int = {
        "NONE":0,
        "LOW":1,
        "MEDIUM":2,
        "HIGH":3,
        "CRITICAL":4
    }
    int_to_level = {
        0:"NONE",
        1:"LOW",
        2:"MEDIUM",
        3:"HIGH",
        4:"CRITICAL"
    }
    
    maxCVSS = max( [cve.cvss for cve in cves_list] )
    maxIntegridad = int_to_level.get( max([ level_to_int.get(cve.integridad) for cve in cves_list], default=0))
    maxConfidencialidad = int_to_level.get( max([level_to_int.get(cve.confidencialidad) for cve in cves_list], default=0) )
    maxDisponibilidad = int_to_level.get( max( [level_to_int.get(cve.disponibilidad) for cve in cves_list], default=0) )
    return              { 'actualNivelCVSS': maxCVSS,
                          'actualNivelIntegridad':  maxIntegridad,
                          'actualNivelConfidencialidad': maxConfidencialidad,
                          'actualNivelDisponibilidad': maxDisponibilidad,
                          'CVES': [ cve.model_dump() for cve in cves_list] } 

