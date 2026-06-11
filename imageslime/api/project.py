"""
API endpoints for project operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import json
import os
from datetime import datetime

from ..config import get_settings, Settings
from ..models import ProjectState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/project")


class ProjectResponse(BaseModel):
    """Response model for project operations."""
    success: bool
    message: str
    project: Optional[dict] = None


class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""
    name: str = "Untitled Project"
    canvas_width: int = 1920
    canvas_height: int = 1080
    canvas_color: str = "#FFFFFF"


class SaveProjectRequest(BaseModel):
    """Request model for saving a project."""
    project_data: dict


@router.post("/create", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest
) -> ProjectResponse:
    """
    Create a new project.
    """
    try:
        project = ProjectState(
            name=request.name,
            canvas_width=request.canvas_width,
            canvas_height=request.canvas_height,
            canvas_color=request.canvas_color,
        )
        
        logger.info(f"Project created: {project.id}")
        
        return ProjectResponse(
            success=True,
            message="Project created successfully",
            project=project.to_dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.post("/save", response_model=ProjectResponse)
async def save_project(
    request: SaveProjectRequest,
    settings: Settings = Depends(get_settings)
) -> ProjectResponse:
    """
    Save a project to a file.
    """
    try:
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(settings.TEMP_DIR)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate filename
        project_data = request.project_data
        project_id = project_data.get("id", "untitled")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_{project_id}_{timestamp}.json"
        filepath = os.path.join(temp_dir, filename)
        
        # Save project to file
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        logger.info(f"Project saved: {filepath}")
        
        return ProjectResponse(
            success=True,
            message="Project saved successfully",
            project={"filepath": filepath, **project_data}
        )
        
    except Exception as e:
        logger.error(f"Failed to save project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save project: {str(e)}"
        )


@router.post("/load", response_model=ProjectResponse)
async def load_project(
    filepath: str
) -> ProjectResponse:
    """
    Load a project from a file.
    """
    try:
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project file not found: {filepath}"
            )
        
        # Load project from file
        with open(filepath, 'r') as f:
            project_data = json.load(f)
        
        # Convert to ProjectState and back to dict to validate
        project = ProjectState.from_dict(project_data)
        
        logger.info(f"Project loaded: {filepath}")
        
        return ProjectResponse(
            success=True,
            message="Project loaded successfully",
            project=project.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load project: {str(e)}"
        )


@router.get("/export/{project_id}")
async def export_project(
    project_id: str,
    format: str = "png",
    settings: Settings = Depends(get_settings)
) -> FileResponse:
    """
    Export the current project as an image.
    
    Supported formats: png, jpeg
    Note: Export is now handled client-side for better performance.
    This endpoint is kept for backward compatibility.
    """
    try:
        temp_dir = os.path.join(settings.TEMP_DIR)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create a placeholder - actual export is done in frontend
        canvas_width = 1920
        canvas_height = 1080
        image = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)
        
        cv2.putText(
            image,
            f"Project: {project_id}",
            (100, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (0, 0, 0),
            3
        )
        
        temp_file = os.path.join(temp_dir, f"export_{project_id}.{format}")
        cv2.imwrite(temp_file, image)
        
        return FileResponse(
            path=temp_file,
            media_type=f"image/{format}",
            filename=f"imageslime_export_{project_id}.{format}"
        )
        
    except Exception as e:
        logger.error(f"Failed to export project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export project: {str(e)}"
        )


@router.get("/list")
async def list_projects(
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    List all saved projects.
    """
    try:
        temp_dir = os.path.join(settings.TEMP_DIR)
        
        if not os.path.exists(temp_dir):
            return JSONResponse(content={
                "success": True,
                "projects": []
            })
        
        projects = []
        for filename in os.listdir(temp_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(temp_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        project_data = json.load(f)
                    
                    projects.append({
                        "filename": filename,
                        "filepath": filepath,
                        "name": project_data.get("name", "Untitled"),
                        "id": project_data.get("id", ""),
                        "created_at": project_data.get("created_at", ""),
                        "updated_at": project_data.get("updated_at", ""),
                        "size": os.path.getsize(filepath)
                    })
                except:
                    continue
        
        return JSONResponse(content={
            "success": True,
            "projects": projects
        })
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    settings: Settings = Depends(get_settings)
) -> JSONResponse:
    """
    Delete a saved project.
    """
    try:
        temp_dir = os.path.join(settings.TEMP_DIR)
        
        # Find and delete project files
        deleted = False
        for filename in os.listdir(temp_dir):
            if filename.startswith(f"project_{project_id}_") and filename.endswith('.json'):
                filepath = os.path.join(temp_dir, filename)
                os.remove(filepath)
                deleted = True
                break
        
        if deleted:
            logger.info(f"Project deleted: {project_id}")
            return JSONResponse(content={
                "success": True,
                "message": "Project deleted successfully"
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
