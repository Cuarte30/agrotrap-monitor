from typing import Optional
from pydantic import BaseModel


class CampoRegionCreate(BaseModel):
    nombre: str
    latitud_centro: float
    longitud_centro: float
    boundary_geojson: Optional[str] = None


class TrampaCreate(BaseModel):
    codigo: str
    campo_id: int
    lote: str
    plaga_objetivo: str
    latitud: float
    longitud: float


class MonitoreoCreate(BaseModel):
    trampa_id: int
    fecha_muestreo: str
    estadio_fenologico: str
    capturas: int
    observaciones: Optional[str] = ""