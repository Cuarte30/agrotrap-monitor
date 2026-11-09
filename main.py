from typing import List
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import models
import schema

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgroTrap Monitor - División Agropecuaria")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UMBRALES_DB = {
    "Rachiplusia nu": {"amarillo": 6, "rojo": 12},
    "Spodoptera frugiperda": {"amarillo": 5, "rojo": 15},
    "Helicoverpa zea": {"amarillo": 3, "rojo": 10},
    "Chinche de los cuernos": {"amarillo": 2, "rojo": 5},
}


@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h2>Error: No se encontró el archivo templates/index.html</h2>"


# --- API UMBRALES ---
@app.get("/api/umbrales")
def obtener_umbrales():
    return UMBRALES_DB


@app.post("/api/umbrales")
def actualizar_umbrales(datos: dict):
    global UMBRALES_DB
    UMBRALES_DB = datos
    return {"status": "ok", "umbrales": UMBRALES_DB}


# --- API CAMPOS Y TRAMPAS ---
@app.post("/api/campos")
def crear_campo(campo: schema.CampoRegionCreate, db: Session = Depends(get_db)):
    db_campo = models.CampoRegion(**campo.dict())
    db.add(db_campo)
    db.commit()
    db.refresh(db_campo)
    return db_campo


@app.get("/api/campos")
def listar_campos(db: Session = Depends(get_db)):
    return db.query(models.CampoRegion).all()


@app.post("/api/trampas")
def crear_trampa(trampa: schema.TrampaCreate, db: Session = Depends(get_db)):
    db_trampa = models.Trampa(**trampa.dict())
    db.add(db_trampa)
    db.commit()
    db.refresh(db_trampa)
    return db_trampa


@app.get("/api/trampas")
def listar_trampas(db: Session = Depends(get_db)):
    return db.query(models.Trampa).all()


@app.put("/api/trampas/{trampa_id}")
def actualizar_trampa(
    trampa_id: int, datos: schema.TrampaCreate, db: Session = Depends(get_db)
):
    trampa = (
        db.query(models.Trampa).filter(models.Trampa.id == trampa_id).first()
    )
    if not trampa:
        raise HTTPException(status_code=444, detail="Trampa no encontrada")

    trampa.codigo = datos.codigo
    trampa.lote = datos.lote
    trampa.plaga_objetivo = datos.plaga_objetivo
    trampa.latitud = datos.latitud
    trampa.longitud = datos.longitud
    db.commit()
    db.refresh(trampa)
    return trampa


@app.delete("/api/trampas/{trampa_id}")
def eliminar_trampa(trampa_id: int, db: Session = Depends(get_db)):
    trampa = (
        db.query(models.Trampa).filter(models.Trampa.id == trampa_id).first()
    )
    if not trampa:
        raise HTTPException(status_code=404, detail="Trampa no encontrada")

    # Borrar monitoreos asociados primero para mantener integridad
    db.query(models.Monitoreo).filter(
        models.Monitoreo.trampa_id == trampa_id
    ).delete()
    db.delete(trampa)
    db.commit()
    return {"status": "deleted", "id": trampa_id}


# --- API MONITOREOS ---
@app.post("/api/monitoreos/lote")
def carga_masiva_oficina(
    lecturas: List[schema.MonitoreoCreate], db: Session = Depends(get_db)
):
    objetos = [models.Monitoreo(**item.dict()) for item in lecturas]
    db.bulk_save_objects(objetos)
    db.commit()
    return {"status": "ok", "registros_procesados": len(lecturas)}


@app.get("/api/mapa/presion")
def mapa_presion(plaga: str = "Todas", db: Session = Depends(get_db)):
    campos = db.query(models.CampoRegion).all()
    resultado = []

    for c in campos:
        trampas_data = []
        for t in c.trampas:
            if plaga != "Todas" and t.plaga_objetivo != plaga:
                continue

            ultimo = (
                db.query(models.Monitoreo)
                .filter(models.Monitoreo.trampa_id == t.id)
                .order_by(models.Monitoreo.fecha_muestreo.desc())
                .first()
            )

            capturas = ultimo.capturas if ultimo else 0
            umb = UMBRALES_DB.get(
                t.plaga_objetivo, {"amarillo": 5, "rojo": 15}
            )

            if capturas >= umb["rojo"]:
                estado_color = "rojo"
            elif capturas >= umb["amarillo"]:
                estado_color = "amarillo"
            else:
                estado_color = "verde"

            trampas_data.append(
                {
                    "id": t.id,
                    "codigo": t.codigo,
                    "lote": t.lote,
                    "plaga": t.plaga_objetivo,
                    "lat": t.latitud,
                    "lng": t.longitud,
                    "capturas": capturas,
                    "estado_color": estado_color,
                    "umbral_amarillo": umb["amarillo"],
                    "umbral_rojo": umb["rojo"],
                    "estadio": ultimo.estadio_fenologico if ultimo else "-",
                    "fecha": ultimo.fecha_muestreo if ultimo else "-",
                }
            )

        if trampas_data:
            resultado.append(
                {
                    "id": c.id,
                    "campo": c.nombre,
                    "lat": c.latitud_centro,
                    "lng": c.longitud_centro,
                    "trampas": trampas_data,
                }
            )

    return resultado