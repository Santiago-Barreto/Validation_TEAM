from typing import List, Optional

from fastapi import APIRouter, Query

from backend.services import solar_service

router = APIRouter()


@router.get("/solar")
def solar_plants(
    biomas: Optional[List[str]] = Query(
        None, description="Biomas ejecutados (visibles UI)"
    ),
):
    return solar_service.listar_plantas(biomas or [])
