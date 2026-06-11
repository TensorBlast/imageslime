"""
API endpoints for segmentation operations.
"""

import os
import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import get_settings, Settings
from ..models import (
    Point, BoundingBox, SegmentedObject, 
    SegmentationPrompt, SegmentationResult,
    PointModel, BoundingBoxModel
)
from ..services.segmentation import get_segmentation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/segmentation")


class SegmentWithPointsRequest(BaseModel):
    """Request model for point-based segmentation."""
    image_id: str
    points: List[PointModel]
    labels: Optional[List[int]] = None  # 1 for foreground, 0 for background


class SegmentWithBoxRequest(BaseModel):
    """Request model for box-based segmentation."""
    image_id: str
    box: BoundingBoxModel


class SegmentWithTextRequest(BaseModel):
    """Request model for text-based segmentation."""
    image_id: str
    text_prompt: str


class SegmentWithMultipleTextRequest(BaseModel):
    """Request model for multi-prompt text segmentation."""
    image_id: str
    text_prompts: List[str]  # Multiple text prompts to search for


@router.post("/points", response_model=SegmentationResult)
async def segment_with_points(
    request: SegmentWithPointsRequest,
    settings: Settings = Depends(get_settings)
) -> SegmentationResult:
    """
    Perform segmentation using point prompts.
    
    Accepts one or more points to identify the object to segment.
    Labels can be provided (1 for foreground, 0 for background).
    If no labels are provided, all points are treated as foreground.
    """
    try:
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Find the image file
        upload_dir = os.path.join(settings.UPLOAD_DIR)
        image_path = None
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(upload_dir, f"{request.image_id}{ext}")
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {request.image_id}"
            )
        
        # Convert request points to Point objects
        points = [Point(x=p.x, y=p.y) for p in request.points]
        labels = request.labels
        
        # Perform segmentation
        segmented_obj = seg_service.segment_with_points(
            image_path=image_path,
            points=points,
            labels=labels,
            use_cached_embeddings=True
        )
        
        if segmented_obj is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Segmentation failed"
            )
        
        # Convert bounding box to model
        bbox_model = None
        if segmented_obj.bounding_box:
            bbox_model = BoundingBoxModel(
                x1=segmented_obj.bounding_box.x1,
                y1=segmented_obj.bounding_box.y1,
                x2=segmented_obj.bounding_box.x2,
                y2=segmented_obj.bounding_box.y2
            )
        
        logger.info(f"Segmentation with points successful: {len(points)} points")
        
        return SegmentationResult(
            success=True,
            object_id=segmented_obj.id,
            mask_base64=segmented_obj.mask_base64,
            bounding_box=bbox_model,
            message="Segmentation successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to segment with points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation failed: {str(e)}"
        )


@router.post("/box", response_model=SegmentationResult)
async def segment_with_box(
    request: SegmentWithBoxRequest,
    settings: Settings = Depends(get_settings)
) -> SegmentationResult:
    """
    Perform segmentation using a bounding box prompt.
    
    The bounding box should specify the region containing the object to segment.
    """
    try:
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Find the image file
        upload_dir = os.path.join(settings.UPLOAD_DIR)
        image_path = None
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(upload_dir, f"{request.image_id}{ext}")
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {request.image_id}"
            )
        
        # Convert request box to BoundingBox
        bbox = BoundingBox(
            x1=request.box.x1,
            y1=request.box.y1,
            x2=request.box.x2,
            y2=request.box.y2
        )
        
        # Perform segmentation
        segmented_obj = seg_service.segment_with_box(
            image_path=image_path,
            bbox=bbox,
            use_cached_embeddings=True
        )
        
        if segmented_obj is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Segmentation failed"
            )
        
        # Convert bounding box to model
        bbox_model = None
        if segmented_obj.bounding_box:
            bbox_model = BoundingBoxModel(
                x1=segmented_obj.bounding_box.x1,
                y1=segmented_obj.bounding_box.y1,
                x2=segmented_obj.bounding_box.x2,
                y2=segmented_obj.bounding_box.y2
            )
        
        logger.info("Segmentation with bounding box successful")
        
        return SegmentationResult(
            success=True,
            object_id=segmented_obj.id,
            mask_base64=segmented_obj.mask_base64,
            bounding_box=bbox_model,
            message="Segmentation successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to segment with box: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation failed: {str(e)}"
        )


@router.post("/text", response_model=List[SegmentationResult])
async def segment_with_text(
    request: SegmentWithTextRequest,
    settings: Settings = Depends(get_settings)
) -> List[SegmentationResult]:
    """
    Perform segmentation using a text prompt.
    
    This will find and segment all instances of the concept described by the text.
    """
    try:
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Find the image file
        upload_dir = os.path.join(settings.UPLOAD_DIR)
        image_path = None
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(upload_dir, f"{request.image_id}{ext}")
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {request.image_id}"
            )
        
        # Perform segmentation
        segmented_objects = seg_service.segment_with_text(
            image_path=image_path,
            text_prompt=request.text_prompt
        )
        
        # Convert results to response models
        results = []
        for obj in segmented_objects:
            bbox_model = None
            if obj.bounding_box:
                bbox_model = BoundingBoxModel(
                    x1=obj.bounding_box.x1,
                    y1=obj.bounding_box.y1,
                    x2=obj.bounding_box.x2,
                    y2=obj.bounding_box.y2
                )
            
            results.append(SegmentationResult(
                success=True,
                object_id=obj.id,
                mask_base64=obj.mask_base64,
                bounding_box=bbox_model,
                message=f"Found object: {obj.name}"
            ))
        
        logger.info(f"Text segmentation found {len(results)} objects for: {request.text_prompt}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to segment with text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation failed: {str(e)}"
        )


@router.post("/text-multiple", response_model=Dict[str, List[SegmentationResult]])
async def segment_with_multiple_text(
    request: SegmentWithMultipleTextRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, List[SegmentationResult]]:
    """
    Perform segmentation using a text prompt.
    
    This will find and segment all instances of the concept described by the text.
    """
    try:
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Find the image file
        upload_dir = os.path.join(settings.UPLOAD_DIR)
        image_path = None
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(upload_dir, f"{request.image_id}{ext}")
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {request.image_id}"
            )
        
        # Perform segmentation
        segmented_objects = seg_service.segment_with_text(
            image_path=image_path,
            text_prompt=request.text_prompt
        )
        
        # Convert results to response models
        results = []
        for obj in segmented_objects:
            bbox_model = None
            if obj.bounding_box:
                bbox_model = BoundingBoxModel(
                    x1=obj.bounding_box.x1,
                    y1=obj.bounding_box.y1,
                    x2=obj.bounding_box.x2,
                    y2=obj.bounding_box.y2
                )
            
            results.append(SegmentationResult(
                success=True,
                object_id=obj.id,
                mask_base64=obj.mask_base64,
                bounding_box=bbox_model,
                message=f"Found object: {obj.name}"
            ))
        
        logger.info(f"Text segmentation found {len(results)} objects for: {request.text_prompt}")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to segment with text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation failed: {str(e)}"
        )


@router.post("/text-multiple")
async def segment_with_multiple_text(
    request: SegmentWithMultipleTextRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, List[SegmentationResult]]:
    """
    Perform segmentation using multiple text prompts.
    
    This will find and segment all instances of EACH concept described by the text prompts.
    For example, prompts=["person", "car"] will find all people AND all cars in the image.
    """
    try:
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Find the image file
        upload_dir = os.path.join(settings.UPLOAD_DIR)
        image_path = None
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = os.path.join(upload_dir, f"{request.image_id}{ext}")
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {request.image_id}"
            )
        
        # Perform segmentation with multiple text prompts
        objects_by_prompt = seg_service.segment_with_multiple_text_prompts(
            image_path=image_path,
            text_prompts=request.text_prompts
        )
        
        # Convert results to response models
        results_by_prompt = {}
        for prompt, objects in objects_by_prompt.items():
            prompt_results = []
            for obj in objects:
                bbox_model = None
                if obj.bounding_box:
                    bbox_model = BoundingBoxModel(
                        x1=obj.bounding_box.x1,
                        y1=obj.bounding_box.y1,
                        x2=obj.bounding_box.x2,
                        y2=obj.bounding_box.y2
                    )
                
                prompt_results.append(SegmentationResult(
                    success=True,
                    object_id=obj.id,
                    mask_base64=obj.mask_base64,
                    bounding_box=bbox_model,
                    message=f"Found object: {obj.name}"
                ))
            results_by_prompt[prompt] = prompt_results
        
        logger.info(f"Multi-prompt segmentation found {sum(len(v) for v in results_by_prompt.values())} objects")
        
        return results_by_prompt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to segment with multiple text prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Segmentation failed: {str(e)}"
        )


@router.get("/model-info")
async def get_model_info() -> JSONResponse:
    """
    Get information about the loaded segmentation model.
    """
    try:
        seg_service = get_segmentation_service()
        model_info = seg_service.get_model_info()
        
        return JSONResponse(content={
            "success": True,
            "model_info": model_info
        })
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_cache() -> JSONResponse:
    """
    Clear the embedding cache.
    """
    try:
        seg_service = get_segmentation_service()
        seg_service.clear_cache()
        
        logger.info("Embedding cache cleared")
        
        return JSONResponse(content={
            "success": True,
            "message": "Embedding cache cleared"
        })
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
