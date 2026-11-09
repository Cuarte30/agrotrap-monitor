from datetime import date
from database import Base
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class CampoRegion(Base):
    __tablename__ = "campos_regiones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(
        String, unique=True, index=True
    )  # Ej: Noetinger, Pelado, Lomello, Loncopan
    latitud_centro = Column(Float)
    longitud_centro = Column(Float)
    boundary_geojson = Column(
        Text, nullable=True
    )  # Para bordes exactos si cargamos GeoJSON

    trampas = relationship("Trampa", back_populates="campo_region")


class Trampa(Base):
    __tablename__ = "trampas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)  # Ej: TR-NOET-01
    campo_id = Column(Integer, ForeignKey("campos_regiones.id"))
    lote = Column(String, index=True)  # Ej: Lote 14
    plaga_objetivo = Column(String, index=True)  # Ej: Spodoptera frugiperda
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)

    campo_region = relationship("CampoRegion", back_populates="trampas")
    monitoreos = relationship(
        "Monitoreo", back_populates="trampa", cascade="all, delete-orphan"
    )


class Monitoreo(Base):
    __tablename__ = "monitoreos"

    id = Column(Integer, primary_key=True, index=True)
    trampa_id = Column(Integer, ForeignKey("trampas.id"))
    fecha_muestreo = Column(String, default=lambda: date.today().isoformat())
    estadio_fenologico = Column(String)  # Ej: V4, V6, R1, R3
    capturas = Column(Integer, nullable=False, default=0)
    observaciones = Column(String, nullable=True)

    trampa = relationship("Trampa", back_populates="monitoreos")


class Umbral(Base):
    __tablename__ = "umbrales"

    id = Column(Integer, primary_key=True, index=True)
    plaga = Column(String, index=True)
    estadio = Column(String)  # 'VE-V8' o 'R1-R6'
    umbral_amarillo = Column(Integer)  # Alerta
    umbral_rojo = Column(Integer)  # Control / Peligro