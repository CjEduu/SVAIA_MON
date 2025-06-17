"""
    Este archivo .py define las clases necesarias para parsear los json de los CVES
"""


from pydantic import BaseModel


class ParsedCVE(BaseModel):
    id:str
    cvss:float
    confidencialidad:str
    integridad:str
    disponibilidad:str
    literal_formatted:str
    url:str

class SBOMAnalisis(BaseModel):
    actualNivelCVSS:int
    actualNivelIntegridad:str
    actualNivelConfidencialidad:str
    actualNivelDisponibilidad:str
    CVES: list

