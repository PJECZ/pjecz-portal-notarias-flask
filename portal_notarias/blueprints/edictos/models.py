"""
Edictos, modelos
"""

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from portal_notarias.extensions import database


class Edicto(database.Model, UniversalMixin):
    """Edicto"""

    # Nombre de la tabla
    __tablename__ = "edictos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    autoridad_id: Mapped[int] = mapped_column(ForeignKey("autoridades.id"))
    autoridad: Mapped["Autoridad"] = relationship(back_populates="edictos")

    # Columnas
    fecha: Mapped[date] = mapped_column(Date(), index=True)
    descripcion: Mapped[str] = mapped_column(String(256))
    expediente: Mapped[str] = mapped_column(String(16), default="")
    numero_publicacion: Mapped[str] = mapped_column(String(16), default="")
    archivo: Mapped[str] = mapped_column(String(256), default="", server_default="")
    url: Mapped[str] = mapped_column(String(512), default="", server_default="")

    # Columnas nuevas
    acuse_num: Mapped[int] = mapped_column(default=0, server_default="0")
    edicto_id_original: Mapped[int] = mapped_column(default=0, server_default="0")

    # Hijos
    edictos_acuses = relationship("EdictoAcuse", back_populates="edicto")

    @property
    def descargar_url(self):
        """URL para descargar el archivo desde el sitio web"""
        if self.id:
            return f"https://www.pjecz.gob.mx/consultas/edictos/descargar/?id={self.id}"
        return ""

    def __repr__(self):
        """Representación"""
        return f"<Edicto {self.descripcion}>"
