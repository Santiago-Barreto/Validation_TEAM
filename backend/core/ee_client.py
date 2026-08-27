"""Inicialización Google Earth Engine."""

import ee

from backend.core.config import CREDS, PROJECT_ID

ee.Initialize(CREDS, project=PROJECT_ID)
