from fastapi import APIRouter          # ← add this
from .endpoints import parcels, auth, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(parcels.router)
