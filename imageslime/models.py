"""
Data models for ImageSlime application.
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import sys


class LayerType(Enum):
    """Type of layer in the composition."""
    IMAGE = "image"
    SEGMENTED_OBJECT = "segmented_object"


class ObjectStatus(Enum):
    """Status of a segmented object."""
    ACTIVE = "active"
    DELETED = "deleted"
    HIDDEN = "hidden"


@dataclass
class Point:
    """A 2D point with x and y coordinates."""
    x: float
    y: float
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    @classmethod
    def from_tuple(cls, point_tuple: Tuple[float, float]) -> "Point":
        return cls(x=point_tuple[0], y=point_tuple[1])


@dataclass
class BoundingBox:
    """A bounding box defined by top-left and bottom-right coordinates."""
    x1: float  # left
    y1: float  # top
    x2: float  # right
    y2: float  # bottom
    
    def to_list(self) -> List[float]:
        return [self.x1, self.y1, self.x2, self.y2]
    
    @classmethod
    def from_list(cls, bbox_list: List[float]) -> "BoundingBox":
        return cls(x1=bbox_list[0], y1=bbox_list[1], x2=bbox_list[2], y2=bbox_list[3])
    
    def width(self) -> float:
        return self.x2 - self.x1
    
    def height(self) -> float:
        return self.y2 - self.y1


@dataclass
class SegmentedObject:
    """Represents a segmented object from an image."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Object"
    
    # Source information
    source_image_id: str = ""
    source_image_path: str = ""
    
    # Segmentation data
    mask: Optional[np.ndarray] = None  # Binary mask (H, W)
    mask_base64: Optional[str] = None  # Base64 encoded mask for frontend
    bounding_box: Optional[BoundingBox] = None
    cropped_image_base64: Optional[str] = None  # Base64 encoded cropped image with transparency
    
    # Visual properties
    position: Tuple[float, float] = (0, 0)  # (x, y) position in composition
    rotation: float = 0.0  # Rotation in degrees
    scale: Tuple[float, float] = (1.0, 1.0)  # (width_scale, height_scale)
    opacity: float = 1.0  # 0.0 to 1.0
    
    # Styling
    border_color: str = "#FF0000"  # Red border by default
    border_width: int = 2
    fill_color: Optional[str] = None  # None means use original image
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: ObjectStatus = ObjectStatus.ACTIVE
    
    # Layer ordering
    z_index: int = 0
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "source_image_id": self.source_image_id,
            "source_image_path": self.source_image_path,
            "mask_base64": self.mask_base64,
            "bounding_box": self.bounding_box.to_list() if self.bounding_box else None,
            "position": list(self.position),
            "rotation": self.rotation,
            "scale": list(self.scale),
            "opacity": self.opacity,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "fill_color": self.fill_color,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "z_index": self.z_index,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentedObject":
        """Create from dictionary."""
        obj = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Object"),
            source_image_id=data.get("source_image_id", ""),
            source_image_path=data.get("source_image_path", ""),
            mask_base64=data.get("mask_base64"),
            bounding_box=BoundingBox.from_list(data["bounding_box"]) if data.get("bounding_box") else None,
            position=tuple(data.get("position", [0, 0])),
            rotation=data.get("rotation", 0.0),
            scale=tuple(data.get("scale", [1.0, 1.0])),
            opacity=data.get("opacity", 1.0),
            border_color=data.get("border_color", "#FF0000"),
            border_width=data.get("border_width", 2),
            fill_color=data.get("fill_color"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            status=ObjectStatus(data.get("status", "active")),
            z_index=data.get("z_index", 0),
        )
        return obj


@dataclass
class ImageLayer:
    """Represents an image layer in the composition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Layer"
    
    # Image data
    image_path: str = ""
    image_base64: Optional[str] = None
    thumbnail_base64: Optional[str] = None
    
    # Dimensions
    width: int = 0
    height: int = 0
    original_width: int = 0
    original_height: int = 0
    
    # Position and transformation
    position: Tuple[float, float] = (0, 0)  # (x, y)
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    opacity: float = 1.0
    
    # Layer properties
    visible: bool = True
    locked: bool = False
    z_index: int = 0
    
    # Segmentation data for this layer
    embeddings_computed: bool = False
    embeddings_cache_key: Optional[str] = None
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "image_base64": self.image_base64,
            "thumbnail_base64": self.thumbnail_base64,
            "width": self.width,
            "height": self.height,
            "original_width": self.original_width,
            "original_height": self.original_height,
            "position": list(self.position),
            "rotation": self.rotation,
            "scale": list(self.scale),
            "opacity": self.opacity,
            "visible": self.visible,
            "locked": self.locked,
            "z_index": self.z_index,
            "embeddings_computed": self.embeddings_computed,
            "embeddings_cache_key": self.embeddings_cache_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageLayer":
        """Create from dictionary."""
        layer = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Layer"),
            image_path=data.get("image_path", ""),
            image_base64=data.get("image_base64"),
            thumbnail_base64=data.get("thumbnail_base64"),
            width=data.get("width", 0),
            height=data.get("height", 0),
            original_width=data.get("original_width", 0),
            original_height=data.get("original_height", 0),
            position=tuple(data.get("position", [0, 0])),
            rotation=data.get("rotation", 0.0),
            scale=tuple(data.get("scale", [1.0, 1.0])),
            opacity=data.get("opacity", 1.0),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            z_index=data.get("z_index", 0),
            embeddings_computed=data.get("embeddings_computed", False),
            embeddings_cache_key=data.get("embeddings_cache_key"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
        return layer


@dataclass
class ProjectState:
    """Represents the complete state of an ImageSlime project."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Project"
    
    # Canvas properties
    canvas_width: int = 1920
    canvas_height: int = 1080
    canvas_color: str = "#FFFFFF"
    
    # Layers
    image_layers: List[ImageLayer] = field(default_factory=list)
    segmented_objects: List[SegmentedObject] = field(default_factory=list)
    
    # Active selections
    active_layer_id: Optional[str] = None
    active_object_id: Optional[str] = None
    selected_layer_ids: List[str] = field(default_factory=list)
    selected_object_ids: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = time.time()
    
    def get_layer_by_id(self, layer_id: str) -> Optional[ImageLayer]:
        """Get a layer by its ID."""
        for layer in self.image_layers:
            if layer.id == layer_id:
                return layer
        return None
    
    def get_object_by_id(self, object_id: str) -> Optional[SegmentedObject]:
        """Get a segmented object by its ID."""
        for obj in self.segmented_objects:
            if obj.id == object_id:
                return obj
        return None
    
    def get_all_layers_sorted(self) -> List[ImageLayer]:
        """Get all layers sorted by z-index."""
        return sorted(self.image_layers, key=lambda l: l.z_index)
    
    def get_all_objects_sorted(self) -> List[SegmentedObject]:
        """Get all objects sorted by z-index."""
        return sorted(self.segmented_objects, key=lambda o: o.z_index)
    
    def add_layer(self, layer: ImageLayer) -> ImageLayer:
        """Add a new layer to the project."""
        # Set z-index to be highest
        max_z = max([l.z_index for l in self.image_layers], default=-1)
        layer.z_index = max_z + 1
        self.image_layers.append(layer)
        self.update_timestamp()
        return layer
    
    def add_object(self, obj: SegmentedObject) -> SegmentedObject:
        """Add a new segmented object to the project."""
        # Set z-index to be highest
        max_z = max([o.z_index for o in self.segmented_objects], default=-1)
        obj.z_index = max_z + 1
        self.segmented_objects.append(obj)
        self.update_timestamp()
        return obj
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer by ID."""
        for i, layer in enumerate(self.image_layers):
            if layer.id == layer_id:
                self.image_layers.pop(i)
                self.update_timestamp()
                return True
        return False
    
    def remove_object(self, object_id: str) -> bool:
        """Remove a segmented object by ID."""
        for i, obj in enumerate(self.segmented_objects):
            if obj.id == object_id:
                self.segmented_objects.pop(i)
                self.update_timestamp()
                return True
        return False
    
    def bring_layer_to_front(self, layer_id: str) -> bool:
        """Bring a layer to the front (highest z-index)."""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            max_z = max([l.z_index for l in self.image_layers], default=-1)
            layer.z_index = max_z + 1
            self.update_timestamp()
            return True
        return False
    
    def send_layer_to_back(self, layer_id: str) -> bool:
        """Send a layer to the back (lowest z-index)."""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            min_z = min([l.z_index for l in self.image_layers], default=0)
            layer.z_index = min_z - 1
            self.update_timestamp()
            return True
        return False
    
    def bring_layer_forward(self, layer_id: str) -> bool:
        """Bring a layer one step forward."""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            # Find the next highest z-index
            sorted_layers = self.get_all_layers_sorted()
            for i, l in enumerate(sorted_layers):
                if l.id == layer_id and i < len(sorted_layers) - 1:
                    # Swap with next layer
                    next_layer = sorted_layers[i + 1]
                    layer.z_index, next_layer.z_index = next_layer.z_index, layer.z_index
                    self.update_timestamp()
                    return True
        return False
    
    def send_layer_backward(self, layer_id: str) -> bool:
        """Send a layer one step backward."""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            # Find the next lowest z-index
            sorted_layers = self.get_all_layers_sorted()
            for i, l in enumerate(sorted_layers):
                if l.id == layer_id and i > 0:
                    # Swap with previous layer
                    prev_layer = sorted_layers[i - 1]
                    layer.z_index, prev_layer.z_index = prev_layer.z_index, layer.z_index
                    self.update_timestamp()
                    return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "canvas_color": self.canvas_color,
            "image_layers": [l.to_dict() for l in self.image_layers],
            "segmented_objects": [o.to_dict() for o in self.segmented_objects],
            "active_layer_id": self.active_layer_id,
            "active_object_id": self.active_object_id,
            "selected_layer_ids": self.selected_layer_ids,
            "selected_object_ids": self.selected_object_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        """Create from dictionary."""
        project = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled Project"),
            canvas_width=data.get("canvas_width", 1920),
            canvas_height=data.get("canvas_height", 1080),
            canvas_color=data.get("canvas_color", "#FFFFFF"),
            image_layers=[ImageLayer.from_dict(l) for l in data.get("image_layers", [])],
            segmented_objects=[SegmentedObject.from_dict(o) for o in data.get("segmented_objects", [])],
            active_layer_id=data.get("active_layer_id"),
            active_object_id=data.get("active_object_id"),
            selected_layer_ids=data.get("selected_layer_ids", []),
            selected_object_ids=data.get("selected_object_ids", []),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
        return project


# Pydantic models for API communication

class PointModel(BaseModel):
    """Point model for API."""
    x: float
    y: float


class BoundingBoxModel(BaseModel):
    """Bounding box model for API."""
    x1: float
    y1: float
    x2: float
    y2: float


class SegmentationPrompt(BaseModel):
    """Prompt for segmentation."""
    image_id: str
    points: Optional[List[PointModel]] = None
    boxes: Optional[List[BoundingBoxModel]] = None
    text_prompts: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_id": "layer_123",
                "points": [{"x": 100, "y": 200}, {"x": 300, "y": 400}],
                "boxes": None,
                "text_prompts": None,
            }
        }


class SegmentationResult(BaseModel):
    """Result of segmentation."""
    success: bool
    object_id: Optional[str] = None
    mask_base64: Optional[str] = None
    cropped_image_base64: Optional[str] = None
    bounding_box: Optional[BoundingBoxModel] = None
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "object_id": "obj_456",
                "mask_base64": "base64_encoded_mask",
                "bounding_box": {"x1": 100, "y1": 200, "x2": 300, "y2": 400},
                "message": "Segmentation successful",
            }
        }


class LayerOperation(BaseModel):
    """Operation on a layer."""
    layer_id: str
    operation: str  # "move_front", "move_back", "move_up", "move_down", "delete", "toggle_visibility"
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer_id": "layer_123",
                "operation": "move_front",
            }
        }


class ObjectOperation(BaseModel):
    """Operation on a segmented object."""
    object_id: str
    operation: str  # "move_front", "move_back", "delete", "update_position", etc.
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "object_id": "obj_456",
                "operation": "update_position",
                "data": {"x": 100, "y": 200},
            }
        }
