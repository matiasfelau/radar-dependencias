from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.projects import router as projects_router
from app.api.v1.settings import router as settings_router
from app.api.v1.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router, tags=["system"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(alerts_router, tags=["alerts"])
api_router.include_router(settings_router, tags=["settings"])
