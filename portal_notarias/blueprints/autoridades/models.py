"""
Autoridad
"""

from typing import List

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from portal_notarias.extensions import database


class Autoridad(database.Model, UniversalMixin):
    """Autoridad"""

    AUDIENCIAS_CATEGORIAS = {
        "NO DEFINIDO": "No Definido",
        "CIVIL FAMILIAR MERCANTIL LETRADO TCYA": "Civil Familiar Mercantil Letrado TCyA",
        "MATERIA ACUSATORIO PENAL ORAL": "Materia Acusatorio Penal Oral",
        "DISTRITALES": "Distritales",
        "SALAS": "Salas",
    }

    ORGANOS_JURISDICCIONALES = {
        "NO DEFINIDO": "No Definido",
        "JUZGADO DE PRIMERA INSTANCIA": "Juzgado de Primera Instancia",
        "JUZGADO DE PRIMERA INSTANCIA ORAL": "Juzgado de Primera Instancia Oral",
        "PLENO O SALA DEL TSJ": "Pleno o Sala del TSJ",
        "TRIBUNAL DISTRITAL": "Tribunal Distrital",
        "TRIBUNAL DE CONCILIACION Y ARBITRAJE": "Tribunal de Conciliación y Arbitraje",
    }

    SEDES = {
        "ND": "ND",
        "DACN": "DACN",
        "DMNC": "DMNC",
        "DPRR": "DPRR",
        "DRGR": "DRGR",
        "DSBN": "DSBN",
        "DSLT": "DSLT",
        "DSPD": "DSPD",
        "DTRC": "DTRC",
    }

    # Nombre de la tabla
    __tablename__ = "autoridades"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    distrito_id: Mapped[int] = mapped_column(ForeignKey("distritos.id"))
    distrito: Mapped["Distrito"] = relationship(back_populates="autoridades")

    # Columnas
    clave: Mapped[str] = mapped_column(String(16), unique=True)
    datawarehouse_id: Mapped[int]  # Columna para comunicación con SAJI
    descripcion: Mapped[str] = mapped_column(String(256))
    descripcion_corta: Mapped[str] = mapped_column(String(64))
    es_archivo_solicitante: Mapped[bool] = mapped_column(default=False)
    es_cemasc: Mapped[bool] = mapped_column(default=False)
    es_defensoria: Mapped[bool] = mapped_column(default=False)
    es_extinto: Mapped[bool] = mapped_column(default=False)
    es_jurisdiccional: Mapped[bool] = mapped_column(default=False)
    es_notaria: Mapped[bool] = mapped_column(default=False)
    es_organo_especializado: Mapped[bool] = mapped_column(default=False)
    es_revisor_escrituras: Mapped[bool] = mapped_column(default=False)
    directorio_edictos: Mapped[str] = mapped_column(String(256), default="", server_default="")

    # Hijos
    usuarios: Mapped[List["Usuario"]] = relationship("Usuario", back_populates="autoridad")
    edictos: Mapped[List["Edicto"]] = relationship("Edicto", back_populates="autoridad")

    def __repr__(self):
        """Representación"""
        return f"<Autoridad {self.clave}>"
