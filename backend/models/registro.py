"""Modelo de comentario / corrección del equipo TEAM."""

from typing import Literal, Optional

from pydantic import BaseModel, model_validator

# correction = propuesta de cambio; confirmed = OK; doubt = revisar; note = nota libre
ClasificacionTeam = Literal["correction", "confirmed", "doubt", "note"]

CAMPOS_OBLIGATORIOS = {"nombre", "comentario", "clasificacion"}


class Registro(BaseModel):
    lat: float
    lon: float
    nombre: str = ""
    comentario: str = ""
    clasificacion: ClasificacionTeam
    anio_contexto: Optional[int] = None
    clase_col3: Optional[int] = None
    clase_col4: Optional[int] = None
    bioma: Optional[str] = None
    clase_sugerida: Optional[int] = None

    @model_validator(mode="after")
    def chequear_obligatorios(self):
        for campo in CAMPOS_OBLIGATORIOS:
            valor = getattr(self, campo)
            if not valor or str(valor).strip() == "":
                raise ValueError(f"El campo '{campo}' es obligatorio.")
        return self
