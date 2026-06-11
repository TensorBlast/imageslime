"""
API endpoints for image operations.
"""

import os
import uuid
import logging
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Form, Depends, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import cv2
import numpy as np
from PIL import Image
import io
import base64

from ..config import get_settings, Settings
from ..models import ImageLayer, ProjectState
from ..services.segmentation import get_segmentation_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images")


class ImageResponse(BaseModel):
    """Response model for image operations."""
    success: bool
    message: str
    image_id: Optional[str] = None
    image_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_base64: Optional[str] = None
    image_base64: Optional[str] = None


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings)
) -> ImageResponse:
    """
    Upload an image file.
    
    Accepts image files (JPEG, PNG, WebP) and stores them for processing.
    """
    try:
        logger.info(f"Upload request received: filename={file.filename}, content_type={file.content_type}, size={file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
        
        # Check content type or file extension
        is_valid_type = (file.content_type in allowed_types) or \
                        (any(file.filename.lower().endswith(ext) for ext in allowed_extensions))
        
        if not is_valid_type:
            logger.warning(f"Invalid file type: {file.content_type}, filename: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content once
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            file_ext = '.png'  # Default to PNG
        
        image_id = str(uuid.uuid4())
        image_path = upload_dir / f"{image_id}{file_ext}"
        
        # Save the file
        with open(image_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Get image dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except:
            # Fallback to OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image file"
                )
            height, width = img.shape[:2]
        
        # Create base64 image for frontend display (1024px max for good quality)
        image_base64 = _create_thumbnail(image_path, max_size=1024)
        
        logger.info(f"Image uploaded: {image_id} ({width}x{height})")
        
        return ImageResponse(
            success=True,
            message="Image uploaded successfully",
            image_id=image_id,
            image_path=str(image_path),
            width=width,
            height=height,
            thumbnail_base64=image_base64,  # Keep for backward compatibility
            image_base64=image_base64      # Use for display
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.get("/{image_id}")
async def get_image(
    image_id: str,
    settings: Settings = Depends(get_settings)
) -> FileResponse:
    """
    Get the original image file.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # Find the image file
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        image_path = upload_dir / f"{image_id}{ext}"
        if image_path.exists():
            return FileResponse(
                path=image_path,
                media_type=f"image/{ext[1:]}",
                filename=f"{image_id}{ext}"
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Image not found"
    )


@router.get("/{image_id}/thumbnail")
async def get_thumbnail(
    image_id: str,
    size: int = 200,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Get a thumbnail of the image.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # Find the image file
    image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        path = upload_dir / f"{image_id}{ext}"
        if path.exists():
            image_path = path
            break
    
    if image_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    thumbnail_base64 = _create_thumbnail(image_path, max_size=size)
    
    return JSONResponse(content={
        "success": True,
        "thumbnail_base64": thumbnail_base64
    })


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Delete an uploaded image.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # Find and delete the image file
    deleted = False
    for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        image_path = upload_dir / f"{image_id}{ext}"
        if image_path.exists():
            image_path.unlink()
            deleted = True
            break
    
    if deleted:
        logger.info(f"Image deleted: {image_id}")
        return JSONResponse(content={
            "success": True,
            "message": "Image deleted successfully"
        })
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )


@router.post("/{image_id}/compute-embeddings")
async def compute_embeddings(
    image_id: str,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Compute and cache embeddings for an image.
    
    This pre-computes the image embeddings for faster segmentation.
    """
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        
        # Find the image file
        image_path = None
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            path = upload_dir / f"{image_id}{ext}"
            if path.exists():
                image_path = str(path)
                break
        
        if image_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Get segmentation service
        seg_service = get_segmentation_service()
        
        if not seg_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Segmentation service not available"
            )
        
        # Compute embeddings
        embeddings = seg_service.compute_embeddings(image_path)
        
        if embeddings:
            logger.info(f"Embeddings computed for image: {image_id}")
            return JSONResponse(content={
                "success": True,
                "message": "Embeddings computed successfully",
                "cache_key": embeddings.get("cache_key")
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to compute embeddings"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compute embeddings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute embeddings: {str(e)}"
        )


@router.get("/list")
async def list_images(
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    List all uploaded images.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    
    if not upload_dir.exists():
        return JSONResponse(content={
            "success": True,
            "images": []
        })
    
    images = []
    for image_file in upload_dir.glob("*"):
        if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            try:
                with Image.open(image_file) as img:
                    width, height = img.size
            except:
                continue
            
            images.append({
                "id": image_file.stem,
                "filename": image_file.name,
                "path": str(image_file),
                "width": width,
                "height": height,
                "size": image_file.stat().st_size
            })
    
    return JSONResponse(content={
        "success": True,
        "images": images
    })


def _create_thumbnail(image_path: str, max_size: int = 200) -> Optional[str]:
    """Create a base64-encoded thumbnail of an image."""
    try:
        with Image.open(image_path) as img:
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}")
        return None
