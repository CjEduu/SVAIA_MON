from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass

user_roles = Table(
        "user_roles",
        Base.metadata,
        Column("username",String(30),ForeignKey("UsersNew.nombre"),primary_key=True),
        Column("rolename",String(40),ForeignKey("Roles.rol"),primary_key=True)
        )

class Roles(Base):
    __tablename__ = "Roles"
    rol: Mapped[str] = mapped_column(String(40),primary_key = True)
    users: Mapped[list['Users']] = relationship("Users",secondary=user_roles,back_populates="roles")
    

    def __repr__(self):
        return f"<Role(name='{self.rol}')>"

class Proyectos(Base):
    __tablename__ = "Proyectos"
    nombre: Mapped[str] = mapped_column(String(30),primary_key=True)
    owner: Mapped[str] = mapped_column(String(30),nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200))
    fecha_creacion: Mapped[str] = mapped_column(String(26))
    fecha_edicion: Mapped[str] = mapped_column(String(26))
    sec_info: Mapped['SecInfo'] = relationship(
       back_populates='proyecto', uselist=False,cascade= "all, delete"
    )
    analysis_result:Mapped['AnalysisResult'] = relationship(
        back_populates='proyecto', uselist=False,cascade= "all, delete"
    )
    related_cves:Mapped[list['CVE']] = relationship(
        back_populates='proyecto', uselist=True, cascade= "all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Proyecto(id = nombre={self.nombre!r})"

    def to_dict(self) -> dict:
        return {"nombre": self.nombre,
                "owner":self.owner,
                "descripcion":self.descripcion,
                "fecha_creacion":self.fecha_creacion,
                "fecha_edicion":self.fecha_edicion,
                "sec_info":self.sec_info.to_dict(),
                "analysis_result":self.analysis_result.to_dict(),
                "related_cves":[ cve.to_dict() for cve in self.related_cves]
                }

class CVE(Base):
    __tablename__="CVES"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_proyecto: Mapped[str] = mapped_column(
        String(30), ForeignKey('Proyectos.nombre'), nullable=False
    )
    cve_id: Mapped[str] = mapped_column(String(20))
    cvss: Mapped[int]
    confidencialidad: Mapped[str] = mapped_column(String(10))
    integridad: Mapped[str] = mapped_column(String(10))
    disponibilidad: Mapped[str] = mapped_column(String(10))
    literal_formatted: Mapped[str] = mapped_column(String(2000))
    url:Mapped[str] = mapped_column(String(100))
    proyecto: Mapped['Proyectos'] = relationship(
        back_populates='related_cves'   
    )
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre_proyecto": self.nombre_proyecto,
            "cve_id": self.cve_id,
            "cvss": self.cvss,
            "confidencialidad": self.confidencialidad,
            "integridad": self.integridad,
            "disponibilidad": self.disponibilidad,
            "literal_formatted": self.literal_formatted,
            "url":self.url
        }

    
class AnalysisResult(Base):
    __tablename__="AnalysisResult"
    nombre_proyecto: Mapped[str] = mapped_column(
        String(30), ForeignKey('Proyectos.nombre'), primary_key=True
    )
    actualNivelCVSS: Mapped[int]
    actualNivelIntegridad: Mapped[int] = mapped_column(String(20))
    actualNivelConfidencialidad: Mapped[int] = mapped_column(String(20))
    actualNivelDisponibilidad: Mapped[int] = mapped_column(String(20))
    proyecto: Mapped['Proyectos'] = relationship(
        back_populates='analysis_result', uselist=False
    )


    def to_dict(self)->dict:
        return {
            "actualNivelCVSS":self.actualNivelCVSS,
            "actualNivelIntegridad":self.actualNivelIntegridad,
            "actualNivelConfidencialidad":self.actualNivelConfidencialidad,
            "actualNivelDisponibilidad":self.actualNivelDisponibilidad,
        }

class SecInfo(Base):
    __tablename__ = "SecInfo"
    nombre_proyecto: Mapped[str] = mapped_column(
        String(30), ForeignKey('Proyectos.nombre'), primary_key=True
    )
    nivelCVSS: Mapped[int] = mapped_column(Integer())
    nivelIntegridad: Mapped[int] = mapped_column(String(20))
    nivelConfidencialidad: Mapped[int] = mapped_column(String(20))
    nivelDisponibilidad: Mapped[int] = mapped_column(String(20))
    sbomHash: Mapped[int] = mapped_column(String(120))
    proyecto: Mapped['Proyectos'] = relationship(
        back_populates='sec_info', uselist=False
    )

    def to_dict(self)->dict:
        return {
            "nivelCVSS":self.nivelCVSS,
            "nivelIntegridad":self.nivelIntegridad,
            "nivelConfidencialidad":self.nivelConfidencialidad,
            "nivelDisponibilidad":self.nivelDisponibilidad,
            "sbomHash":self.sbomHash
        }
