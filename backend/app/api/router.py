from fastapi import APIRouter

from app.api import catalog, categories, listings, users

router = APIRouter()

router.include_router(users.router)
router.include_router(categories.router)
router.include_router(listings.router)
router.include_router(catalog.router)
