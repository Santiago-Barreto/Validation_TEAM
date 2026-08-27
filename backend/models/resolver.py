from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class ResolverComentario(BaseModel):
    timestamp: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    grupo_id: Optional[str] = None
    resuelto: Literal["check", "x"]

    @model_validator(mode="after")
    def exigir_clave(self):
        gid = (self.grupo_id or "").strip()
        if gid:
            self.grupo_id = gid
            return self
        if self.timestamp is None or self.lat is None or self.lon is None:
            raise ValueError("Indica grupo_id o timestamp+lat+lon.")
        return self
