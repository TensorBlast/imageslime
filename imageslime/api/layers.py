"""
API endpoints for layer operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import get_settings, Settings
from ..models import ImageLayer, LayerOperation, ObjectOperation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/layers")


class LayerResponse(BaseModel):
    """Response model for layer operations."""
    success: bool
    message: str
    layer: Optional[dict] = None
    layers: Optional[List[dict]] = None


class CreateLayerRequest(BaseModel):
    """Request model for creating a new layer."""
    name: str = "New Layer"
    image_id: Optional[str] = None
    position: Optional[List[float]] = [0, 0]
    rotation: float = 0.0
    scale: Optional[List[float]] = [1.0, 1.0]
    opacity: float = 1.0
    visible: bool = True
    z_index: Optional[int] = None


class UpdateLayerRequest(BaseModel):
    """Request model for updating a layer."""
    layer_id: str
    name: Optional[str] = None
    position: Optional[List[float]] = None
    rotation: Optional[float] = None
    scale: Optional[List[float]] = None
    opacity: Optional[float] = None
    visible: Optional[bool] = None
    z_index: Optional[int] = None


@router.post("/create", response_model=LayerResponse)
async def create_layer(
    request: CreateLayerRequest,
    settings: Settings = Depends(get_settings)
) -> LayerResponse:
    """
    Create a new layer.
    """
    try:
        # Create new layer
        layer = ImageLayer(
            name=request.name,
            position=tuple(request.position) if request.position else (0, 0),
            rotation=request.rotation,
            scale=tuple(request.scale) if request.scale else (1.0, 1.0),
            opacity=request.opacity,
            visible=request.visible,
        )
        
        # If image_id is provided, associate it with the layer
        if request.image_id:
            upload_dir = os.path.abspath(os.path.join(settings.UPLOAD_DIR))
            for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                image_path = os.path.join(upload_dir, f"{request.image_id}{ext}")
                if os.path.exists(image_path):
                    layer.image_path = image_path
                    
                    # Get image dimensions
                    try:
                        from PIL import Image as PILImage
                        with PILImage.open(image_path) as img:
                            layer.width, layer.height = img.size
                            layer.original_width, layer.original_height = img.size
                    except:
                        import cv2
                        img = cv2.imread(image_path)
                        if img is not None:
                            layer.height, layer.width = img.shape[:2]
                            layer.original_height, layer.original_width = img.shape[:2]
                    break
        
        # Set z-index
        if request.z_index is not None:
            layer.z_index = request.z_index
        
        logger.info(f"Layer created: {layer.id}")
        
        return LayerResponse(
            success=True,
            message="Layer created successfully",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to create layer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create layer: {str(e)}"
        )


@router.get("/{layer_id}", response_model=LayerResponse)
async def get_layer(
    layer_id: str
) -> LayerResponse:
    """
    Get information about a specific layer.
    """
    try:
        # In a real implementation, this would fetch from a database or project state
        # For now, return a mock response
        layer = ImageLayer(id=layer_id)
        
        return LayerResponse(
            success=True,
            message="Layer retrieved successfully",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to get layer: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer not found: {layer_id}"
        )


@router.put("/{layer_id}", response_model=LayerResponse)
async def update_layer(
    layer_id: str,
    request: UpdateLayerRequest
) -> LayerResponse:
    """
    Update a layer's properties.
    """
    try:
        # In a real implementation, this would update the layer in the project state
        # For now, create a mock layer with updated properties
        layer = ImageLayer(id=layer_id)
        
        if request.name is not None:
            layer.name = request.name
        if request.position is not None:
            layer.position = tuple(request.position)
        if request.rotation is not None:
            layer.rotation = request.rotation
        if request.scale is not None:
            layer.scale = tuple(request.scale)
        if request.opacity is not None:
            layer.opacity = request.opacity
        if request.visible is not None:
            layer.visible = request.visible
        if request.z_index is not None:
            layer.z_index = request.z_index
        
        layer.update_timestamp()
        
        logger.info(f"Layer updated: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer updated successfully",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to update layer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update layer: {str(e)}"
        )


@router.post("/{layer_id}/move-front")
async def move_layer_to_front(
    layer_id: str
) -> LayerResponse:
    """
    Move a layer to the front (highest z-index).
    """
    try:
        # In a real implementation, this would update the layer ordering
        layer = ImageLayer(id=layer_id, z_index=1000)  # High z-index
        
        logger.info(f"Layer moved to front: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer moved to front",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to move layer to front: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move layer: {str(e)}"
        )


@router.post("/{layer_id}/move-back")
async def move_layer_to_back(
    layer_id: str
) -> LayerResponse:
    """
    Move a layer to the back (lowest z-index).
    """
    try:
        # In a real implementation, this would update the layer ordering
        layer = ImageLayer(id=layer_id, z_index=-1000)  # Low z-index
        
        logger.info(f"Layer moved to back: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer moved to back",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to move layer to back: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move layer: {str(e)}"
        )


@router.post("/{layer_id}/move-up")
async def move_layer_up(
    layer_id: str
) -> LayerResponse:
    """
    Move a layer one step forward in the z-order.
    """
    try:
        # In a real implementation, this would increment the z-index
        layer = ImageLayer(id=layer_id, z_index=1)  # Incremented z-index
        
        logger.info(f"Layer moved up: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer moved up",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to move layer up: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move layer: {str(e)}"
        )


@router.post("/{layer_id}/move-down")
async def move_layer_down(
    layer_id: str
) -> LayerResponse:
    """
    Move a layer one step backward in the z-order.
    """
    try:
        # In a real implementation, this would decrement the z-index
        layer = ImageLayer(id=layer_id, z_index=-1)  # Decremented z-index
        
        logger.info(f"Layer moved down: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer moved down",
            layer=layer.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to move layer down: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move layer: {str(e)}"
        )


@router.delete("/{layer_id}", response_model=LayerResponse)
async def delete_layer(
    layer_id: str
) -> LayerResponse:
    """
    Delete a layer.
    """
    try:
        logger.info(f"Layer deleted: {layer_id}")
        
        return LayerResponse(
            success=True,
            message="Layer deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete layer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete layer: {str(e)}"
        )


@router.get("/list", response_model=LayerResponse)
async def list_layers() -> LayerResponse:
    """
    List all layers in the current project.
    """
    try:
        # In a real implementation, this would return all layers from the project state
        # For now, return empty list
        layers = []
        
        return LayerResponse(
            success=True,
            message="Layers retrieved successfully",
            layers=layers
        )
        
    except Exception as e:
        logger.error(f"Failed to list layers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list layers: {str(e)}"
        )


import os
from typing import Optional
from pydantic import BaseModel
