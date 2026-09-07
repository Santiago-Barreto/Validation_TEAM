from typing import Optional

from pydantic import BaseModel, model_validator


class EditarComentario(BaseModel):
    timestamp: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    grupo_id: Optional[str] = None
    comentario: str = ""
    clase_sugerida: Optional[int] = None

    @model_validator(mode="after")
    def exigir_clave_y_texto(self):
        if not (self.comentario or "").strip():
            raise ValueError("El campo 'comentario' es obligatorio.")
        self.comentario = self.comentario.strip()
        gid = (self.grupo_id or "").strip()
        if gid:
            self.grupo_id = gid
            return self
        if self.timestamp is None or self.lat is None or self.lon is None:
            raise ValueError("Indica grupo_id o timestamp+lat+lon.")
        return self
