from fastapi import APIRouter
from .routes import base,patient,project,study,project_study

api_router = APIRouter()
api_router.include_router(base.router, tags=["base"])
api_router.include_router(patient.router, tags=["patient"], prefix="/patient")
api_router.include_router(study.router, tags=["study"], prefix="/study")
api_router.include_router(project.router, tags=["project"], prefix="/project")
api_router.include_router(project_study.router, tags=["project_study"], prefix="/project_study")
