from typing import Union

from nvdlib import searchCVE
from nvdlib.classes import CVE

from sbom_analyzer.src.cve_parser import format_single_cve
from sbom_analyzer.src.CVES import ParsedCVE
from sbom_analyzer.src.cycloneDX import CydxComponentType,CydxSBOM

def infer_cpe(component)->Union[str,None]:
    """Infer CPE components if cpe field is missing."""
    if not (component.type and (component.group or component.publisher) and component.version):
        return None
    # Map type to part
    part_map = {
        CydxComponentType.application: "a",
        CydxComponentType.library: "a",
        CydxComponentType.operating_system: "o",
        CydxComponentType.device: "h"
    }
    part = part_map.get(component.type,"a") 
    vendor = component.group or component.publisher
    product = component.name
    version = component.version
    return f"cpe:2.3:{part}:{vendor}:{product}:{version}:*:*:*:*:*:*:*"
    

def construct_cpe(sbom_component)->Union[str,None]:
    # https://nvd.nist.gov/developers/vulnerabilities
    # "cpe:2.3:[part]:[vendor]:[product]:[version]:[update]:[edition]:[language]:[sw_edition]:[target_sw]:[target_hw]:[other]"
    # Los sbom suelen incluir el cpe, si no lo tienen hay que formarlo. Part,vendor,product,version son REQUIRED
    cpe_data = sbom_component.cpe if sbom_component.cpe else infer_cpe(sbom_component)
    if not cpe_data:
        # NO podemos buscarlo en la API de CVE con el CPE
        return None
    
    return cpe_data


def find_cves_for_sbom(sbom:CydxSBOM)->list[ParsedCVE]:
    component_cve:list[CVE] = list()
    for component in sbom.components:
        cpe_string = component.cpe if component.cpe else construct_cpe(component)
        try:
            # Buscamos por CPE, si no tenemos CPE, intentamos hacer una keyword search en la descripción con el nombre del componente
            results = searchCVE(
                cpeName=cpe_string,
                keywordSearch = component.name + " " + component.description  if not cpe_string else None 
            )
        except Exception as e:
            print(f"Error querying NVD for {cpe_string}: {e}")
        else:
            component_cve.extend(results)

    # We parse them
    parsed_cves:list[ParsedCVE] = []
    for cve in component_cve:
        cvss = cve.metrics.cvssMetricV31[0].cvssData
        parsed_cves.append(
            ParsedCVE(
                id = cve.id,
                cvss = cvss.baseScore,
                confidencialidad = cvss.confidentialityImpact,
                integridad = cvss.integrityImpact,
                disponibilidad = cvss.availabilityImpact,
                literal_formatted = format_single_cve(cve),
                url = cve.url
                
            )
        )
        
    return parsed_cves    

if __name__ == "__main__":
    cyclonedx_bom:CydxSBOM = CydxSBOM.parse_file('./testSBOMS/bom.json')
    result:list[ParsedCVE] = find_cves_for_sbom(cyclonedx_bom)
    for cve in result:
        print(cve)
