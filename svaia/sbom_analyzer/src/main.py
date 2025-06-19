from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from sbom_analyzer.src import config
from sbom_analyzer.src.CVES import ParsedCVE
from sbom_analyzer.src.cycloneDX import CydxSBOM
from sbom_analyzer.src.utils_cve import find_cves_for_sbom
from secure_log_manager.src.SecureLogManager import (
    SecureLogManager,
    monitor_funciones,
)


@dataclass
class ResultError:
    err_str: Optional[str]
    result: bool

@lru_cache
def get_config():
    return config.Settings()


# TODO Make this customizable
parent_path = Path(__file__).parent.parent
absolute_log_path = Path( parent_path / "logs/sbom_analyzer.log").resolve()
if not absolute_log_path.exists():
    open(absolute_log_path,'x').close()

log_manager = SecureLogManager(debug_mode=10)
log_manager.configure_logging(absolute_log_path)
log_manager.inicializar_log()
log_function = monitor_funciones(log_manager)

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message":"pong"}


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
    
    maxCVSS = max( [cve.cvss for cve in cves_list],default=0 )
    maxIntegridad = int_to_level.get( max([ level_to_int.get(cve.integridad) for cve in cves_list], default=0))
    maxConfidencialidad = int_to_level.get( max([level_to_int.get(cve.confidencialidad) for cve in cves_list], default=0) )
    maxDisponibilidad = int_to_level.get( max( [level_to_int.get(cve.disponibilidad) for cve in cves_list], default=0) )
    return              { 'actualNivelCVSS': maxCVSS,
                          'actualNivelIntegridad':  maxIntegridad,
                          'actualNivelConfidencialidad': maxConfidencialidad,
                          'actualNivelDisponibilidad': maxDisponibilidad,
                          'CVES': [ cve.model_dump() for cve in cves_list] } 

