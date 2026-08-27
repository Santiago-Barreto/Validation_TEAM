from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class Registro(BaseModel):
    lat: float
    lon: float
    nombre: str = ""
    comentario: str = ""
    clasificacion: str = Field(default="comentario")
    anio_contexto: Optional[int] = None
    clase_col3: Optional[int] = None
    clase_col4: Optional[int] = None
    bioma: Optional[str] = None
    clase_sugerida: Optional[int] = None
    creado_por: Optional[str] = None
    foto_url: Optional[str] = None
    grupo_id: Optional[str] = None

    @model_validator(mode="after")
    def chequear_obligatorios(self):
        if not self.comentario or str(self.comentario).strip() == "":
            raise ValueError("El campo 'comentario' es obligatorio.")
        self.clasificacion = "comentario"
        return self


class PuntoLote(BaseModel):
    lat: float
    lon: float


class LoteComentarios(BaseModel):
    """Varios puntos con el mismo comentario / grupo_id."""

    puntos: List[PuntoLote]
    comentario: str = ""
    nombre: str = ""
    clasificacion: str = Field(default="comentario")
    anio_contexto: Optional[int] = None
    bioma: Optional[str] = None
    clase_sugerida: Optional[int] = None
    creado_por: Optional[str] = None
    foto_url: Optional[str] = None
    grupo_id: Optional[str] = None

    @model_validator(mode="after")
    def chequear_lote(self):
        if not self.puntos:
            raise ValueError("Indica al menos un punto.")
        if not self.comentario or str(self.comentario).strip() == "":
            raise ValueError("El campo 'comentario' es obligatorio.")
        self.clasificacion = "comentario"
        return self
