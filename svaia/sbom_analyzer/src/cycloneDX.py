"""
    Este archivo .py define las clases necesarias para parsear los json de los SBOM
    en formato cycloneDX v1.6 con ayuda de pydantic.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class CydxMetadata(BaseModel):
    # This could be expanded if needed with all the possible retrievable metadata
    timestamp: str  # Format date-time

class CydxComponentType(Enum):
    # Si no encuentra una clasificación adecuada, hace default a 'application'
    application = 'application'
    framework = 'framework'
    library = 'library'
    container = 'container'
    platform = 'platform'
    operating_system = 'operating-system'
    device = 'device'
    device_driver = 'device-driver'
    firmware = 'firmware'
    file = 'file'
    machine_learning_model = 'machine-learning-model'
    data = 'data'
    cryptographic_assset = 'cryptographic-asset'

# This also could be expanded
class CydxComponent(BaseModel):
    """
    Hardware/Software component as defined in cycloneDX v1.6 format
    """

    type: CydxComponentType
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    components: Optional[List[CydxComponentType]] = None
    tags: Optional[List[str]] = None
    cpe: Optional[str] = None
    group: Optional[str] = None
    publisher: Optional[str] = None

class CydxServices(BaseModel):
    """
    A service/microservice/function-as-a-service/other type of network or intra-process services
    as defined in cycloneDX v1.6 format
    """

    name: str
    version: Optional[str] = None


# TODO https://cyclonedx.org/docs/1.6/json/#externalReferences
class CydxExternalRef(BaseModel):
    """
    External refs as defined in cycloneDX v1.6 format
    """

    pass


class CydxDependency(BaseModel):
    """
    Dependencies as defined in cycloneDX v1.6 format
    """

    ref: str  # ALMENOS de 1 CHAR DE LARGO


class CydxSBOM(BaseModel):
    bomFormat: str
    specVersion: str
    serialNumber: Optional[
        str
    ]  # MUST match regex ^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$=None
    version: int = 1
    metadata: Optional[CydxMetadata] = None
    components: Optional[List[CydxComponent]] = None
    services: Optional[List[CydxServices]] = None
    externalReferences: Optional[List[CydxExternalRef]] = None
    dependencies: Optional[List[CydxDependency]] = None
