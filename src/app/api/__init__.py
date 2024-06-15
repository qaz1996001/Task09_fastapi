from fastapi import APIRouter
from .routes import base
from .routes import patient
from .routes import project
from .routes import study


api_router = APIRouter()
api_router.include_router(base.router, tags=["base"])
api_router.include_router(patient.router, tags=["patient"], prefix="/patient")
api_router.include_router(study.router, tags=["study"], prefix="/study")
api_router.include_router(project.router, tags=["project"], prefix="/project")
