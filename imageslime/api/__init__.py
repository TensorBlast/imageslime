"""
API endpoints for ImageSlime application.
"""

from fastapi import APIRouter

# Create main router
router = APIRouter(prefix="/api/v1")

# Import and include sub-routers
from . import images, segmentation, layers, project

router.include_router(images.router, tags=["images"])
router.include_router(segmentation.router, tags=["segmentation"])
router.include_router(layers.router, tags=["layers"])
router.include_router(project.router, tags=["project"])

__all__ = ["router"]
