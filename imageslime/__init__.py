"""
ImageSlime - Interactive Image Segmentation and Editing Tool

A browser-based image editor that uses Meta's SAM3 model for segmentation,
allowing users to select, manipulate, and combine objects from multiple images.
"""

__version__ = "0.1.0"
__author__ = "ImageSlime Team"
__description__ = "Interactive image segmentation and editing with SAM3"

from .config import Settings
from .models import ImageLayer, SegmentedObject, ProjectState

# Export main components
__all__ = ["__version__", "Settings", "ImageLayer", "SegmentedObject", "ProjectState"]
