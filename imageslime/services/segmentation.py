"""
Segmentation service using SAM3 model.
"""

import os
import time
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import io
import base64

from ..config import get_settings
from ..models import Point, BoundingBox, SegmentedObject, ImageLayer

logger = logging.getLogger(__name__)


class SAM3SegmentationService:
    """
    Service for performing segmentation using SAM3 model.
    Handles model loading, embedding computation, and mask generation.
    """
    
    def __init__(self):
        """Initialize the segmentation service."""
        self.settings = get_settings()
        self.model = None
        self.device = self.settings.SAM3_DEVICE
        self.half_precision = self.settings.SAM3_HALF_PRECISION
        self.model_loaded = False
        self.embedding_cache: Dict[str, Any] = {}  # Cache for image embeddings
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the SAM3 model."""
        try:
            logger.info(f"Initializing SAM3 model on device: {self.device}")
            
            # Import ultralytics SAM3
            from ultralytics.models.sam import SAM3SemanticPredictor, SAM
            
            # Check if model file exists
            model_path = self.settings.SAM3_MODEL_PATH
            if not os.path.exists(model_path):
                logger.warning(f"SAM3 model file not found at {model_path}. "
                             f"Please download sam3.pt from Hugging Face and place it in the project directory.")
                # Try to use the model name directly
                model_path = "sam3.pt"
            
            # Initialize SAM3 model for visual prompts (points, boxes)
            # The SAM class in Ultralytics automatically uses SAM3 when sam3.pt is loaded
            try:
                self.model = SAM(model_path)
                logger.info("SAM3 model initialized for visual prompts")
                self.model_loaded = True
            except Exception as e:
                logger.error(f"Failed to initialize SAM3 model: {e}")
                self.model_loaded = False
                self.model = None
            
            # Initialize SAM3 semantic model for text-based concept segmentation
            try:
                self.semantic_model = SAM3SemanticPredictor(
                    overrides=dict(
                        model=model_path,
                        conf=self.settings.SEGMENTATION_CONFIDENCE,
                        half=self.half_precision,
                        device=self.device,
                    )
                )
                logger.info("SAM3 semantic model initialized for text prompts")
            except Exception as e:
                logger.warning(f"Failed to initialize SAM3 semantic model: {e}")
                self.semantic_model = None
            logger.info("SAM3 models initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import SAM3 model: {e}")
            logger.error("Please install ultralytics>=8.3.237: pip install -U ultralytics")
            self.model_loaded = False
        except Exception as e:
            logger.error(f"Failed to initialize SAM3 model: {e}")
            self.model_loaded = False
    
    def is_available(self) -> bool:
        """Check if the segmentation service is available."""
        return self.model_loaded and (self.model is not None or self.semantic_model is not None)
    
    def compute_embeddings(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Pre-load image for faster segmentation.
        
        For SAM3 with Ultralytics, we don't need to pre-compute embeddings separately.
        The model handles this internally. We just cache the image path for reference.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing metadata, or None if failed
        """
        if not self.is_available():
            logger.error("SAM3 model not available")
            return None
        
        try:
            cache_key = f"embeddings_{image_path}_{os.path.getmtime(image_path)}"
            
            # Check cache
            if cache_key in self.embedding_cache:
                logger.debug(f"Using cached reference for {image_path}")
                return self.embedding_cache[cache_key]
            
            logger.info(f"Caching reference for {image_path}")
            
            # Load image to verify it exists and get dimensions
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert to RGB (SAM expects RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Store metadata in cache
            embeddings_data = {
                "image_path": image_path,
                "image_shape": image_rgb.shape,
                "timestamp": time.time(),
                "cache_key": cache_key,
            }
            
            # Limit cache size
            if len(self.embedding_cache) >= self.settings.EMBEDDING_CACHE_SIZE:
                # Remove oldest entry
                oldest_key = min(self.embedding_cache.keys(), 
                               key=lambda k: self.embedding_cache[k]["timestamp"])
                del self.embedding_cache[oldest_key]
            
            self.embedding_cache[cache_key] = embeddings_data
            logger.info(f"Image reference cached for {image_path}")
            
            return embeddings_data
            
        except Exception as e:
            logger.error(f"Failed to cache image reference for {image_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def segment_with_points(
        self, 
        image_path: str, 
        points: List[Point], 
        labels: Optional[List[int]] = None,
        use_cached_embeddings: bool = True
    ) -> Optional[SegmentedObject]:
        """
        Segment an image using point prompts.
        
        Args:
            image_path: Path to the image file
            points: List of points (x, y coordinates)
            labels: List of labels for each point (1 for foreground, 0 for background)
            use_cached_embeddings: Whether to use cached embeddings
            
        Returns:
            SegmentedObject containing the mask and metadata, or None if failed
        """
        if not self.is_available():
            logger.error("SAM3 model not available")
            return None
        
        try:
            # Convert points to format expected by SAM
            # For one object with multiple points: points=[[[x1, y1], [x2, y2], ...]], labels=[[1, 1, ...]]
            # This tells SAM all points belong to the same object
            sam_points = [[[p.x, p.y] for p in points]]
            
            # If no labels provided, assume all points are foreground
            if labels is None:
                sam_labels = [[1] * len(points)]
            else:
                sam_labels = [labels]
            
            # Use the main model for prediction
            # Ultralytics SAM3 handles everything internally
            results = self.model.predict(
                source=image_path,
                points=sam_points,
                labels=sam_labels,
                conf=self.settings.SEGMENTATION_CONFIDENCE,
            )
            
            # Process results
            if results and len(results) > 0:
                result = results[0]
                
                # Extract mask - SAM should return one mask for all points
                masks = result.masks.data if hasattr(result, 'masks') else None
                if masks is not None and len(masks) > 0:
                    # Take the first mask (SAM should return one mask for all our points)
                    mask = masks[0].cpu().numpy()
                    mask = (mask > 0).astype(np.uint8) * 255  # Convert to binary mask
                    
                    # Get bounding box
                    bbox = result.boxes.xyxy[0].cpu().numpy() if hasattr(result, 'boxes') else None
                    
                    if bbox is not None:
                        # Extract the actual image region within the bounding box
                        cropped_image_base64 = self._extract_masked_region(image_path, mask, bbox)
                    else:
                        cropped_image_base64 = None
                    
                    # Create segmented object
                    obj = SegmentedObject(
                        name=f"Object_{time.time()}",
                        source_image_path=image_path,
                        mask=mask,
                        bounding_box=BoundingBox(
                            x1=float(bbox[0]), 
                            y1=float(bbox[1]), 
                            x2=float(bbox[2]), 
                            y2=float(bbox[3])
                        ) if bbox is not None else None,
                        cropped_image_base64=cropped_image_base64
                    )
                    
                    # Convert mask to base64 for frontend
                    obj.mask_base64 = self._mask_to_base64(mask)
                    
                    # Create a red RGBA preview mask for frontend (cropped to bbox for consistency)
                    obj.preview_mask_base64 = self._create_red_mask_preview(mask, bbox)
                    
                    logger.info(f"Segmentation successful with {len(points)} points")
                    return obj
            
            logger.warning("No masks generated from segmentation")
            return None
            
        except Exception as e:
            logger.error(f"Failed to segment with points: {e}")
            return None
    
    def segment_with_box(
        self, 
        image_path: str, 
        bbox: BoundingBox,
        use_cached_embeddings: bool = True
    ) -> Optional[SegmentedObject]:
        """
        Segment an image using a bounding box prompt.
        
        Args:
            image_path: Path to the image file
            bbox: Bounding box coordinates
            use_cached_embeddings: Whether to use cached embeddings
            
        Returns:
            SegmentedObject containing the mask and metadata, or None if failed
        """
        if not self.is_available():
            logger.error("SAM3 model not available")
            return None
        
        try:
            # Convert bbox to format expected by SAM
            sam_bbox = bbox.to_list()
            
            # Use the main model for prediction
            # Ultralytics SAM3 handles everything internally
            results = self.model.predict(
                source=image_path,
                bboxes=[sam_bbox],
                conf=self.settings.SEGMENTATION_CONFIDENCE,
            )
            
            # Process results
            if results and len(results) > 0:
                result = results[0]
                
                # Extract mask
                masks = result.masks.data if hasattr(result, 'masks') else None
                if masks is not None and len(masks) > 0:
                    mask = masks[0].cpu().numpy()
                    mask = (mask > 0).astype(np.uint8) * 255
                    
                    # Get bounding box (refine from input)
                    result_bbox = result.boxes.xyxy[0].cpu().numpy() if hasattr(result, 'boxes') else sam_bbox
                    
                    # Create segmented object
                    obj = SegmentedObject(
                        name=f"Object_{time.time()}",
                        source_image_path=image_path,
                        mask=mask,
                        bounding_box=BoundingBox(
                            x1=float(result_bbox[0]), 
                            y1=float(result_bbox[1]), 
                            x2=float(result_bbox[2]), 
                            y2=float(result_bbox[3])
                        ),
                    )
                    
                    # Convert mask to base64
                    obj.mask_base64 = self._mask_to_base64(mask)
                    
                    logger.info("Segmentation with bounding box successful")
                    return obj
            
            logger.warning("No masks generated from bounding box segmentation")
            return None
            
        except Exception as e:
            logger.error(f"Failed to segment with bounding box: {e}")
            return None
    
    def segment_with_text(
        self, 
        image_path: str, 
        text_prompt: str,
        use_cached_embeddings: bool = True
    ) -> List[SegmentedObject]:
        """
        Segment an image using a text prompt (concept segmentation).
        
        Args:
            image_path: Path to the image file
            text_prompt: Text description of the object to segment
            use_cached_embeddings: Whether to use cached embeddings
            
        Returns:
            List of SegmentedObject for all instances matching the prompt
        """
        if not self.is_available():
            logger.error("SAM3 model not available")
            return []
        
        try:
            # Use the semantic model if available
            if self.semantic_model is not None:
                predictor = self.semantic_model
            else:
                # Fallback to creating new semantic predictor
                from ultralytics.models.sam import SAM3SemanticPredictor
                
                overrides = dict(
                    conf=self.settings.SEGMENTATION_CONFIDENCE,
                    task="segment",
                    mode="predict",
                    model=self.settings.SAM3_MODEL_PATH,
                    half=self.half_precision,
                    device=self.device,
                )
                
                predictor = SAM3SemanticPredictor(overrides=overrides)
            
            # Perform segmentation with text prompt
            # For SAM3SemanticPredictor, pass source and text together
            results = predictor(source=image_path, text=[text_prompt])
            
            objects = []
            
            # Process results
            if results and hasattr(results, 'masks'):
                masks = results.masks.data
                boxes = results.boxes.xyxy
                
                for i in range(len(masks)):
                    mask = masks[i].cpu().numpy()
                    mask = (mask > 0).astype(np.uint8) * 255
                    
                    bbox = boxes[i].cpu().numpy()
                    
                    obj = SegmentedObject(
                        name=f"{text_prompt}_{i}",
                        source_image_path=image_path,
                        mask=mask,
                        bounding_box=BoundingBox(
                            x1=float(bbox[0]), 
                            y1=float(bbox[1]), 
                            x2=float(bbox[2]), 
                            y2=float(bbox[3])
                        ),
                    )
                    
                    obj.mask_base64 = self._mask_to_base64(mask)
                    objects.append(obj)
            
            logger.info(f"Text segmentation found {len(objects)} objects for prompt: {text_prompt}")
            return objects
            
        except Exception as e:
            logger.error(f"Failed to segment with text prompt: {e}")
            return []
    
    def _mask_to_base64(self, mask: np.ndarray) -> str:
        """Convert a binary mask to base64 string."""
        # Ensure mask is binary (0 or 255)
        mask = (mask > 0).astype(np.uint8) * 255
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', mask)
        mask_bytes = buffer.tobytes()
        
        # Convert to base64
        mask_base64 = base64.b64encode(mask_bytes).decode('utf-8')
        return f"data:image/png;base64,{mask_base64}"
    
    def _create_red_mask_preview(self, mask: np.ndarray, bbox: np.ndarray = None) -> str:
        """Create a red RGBA mask preview with transparency.
        
        Uses the same logic as _extract_masked_region: crops to bounding box
        and applies mask to alpha channel with full opacity.
        
        Returns a base64 PNG where mask regions are red with full opacity.
        """
        # Ensure mask is binary (0 or 255)
        mask = (mask > 0).astype(np.uint8) * 255
        
        # If bbox provided, crop mask to bounding box (same as _extract_masked_region)
        if bbox is not None:
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            mask = mask[y1:y2, x1:x2]
        
        # Create RGBA image: red with alpha from mask (full opacity)
        height, width = mask.shape
        rgba_mask = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Set red channel to 255 where mask is white
        rgba_mask[..., 0] = mask  # Red channel
        rgba_mask[..., 1] = 0     # Green channel
        rgba_mask[..., 2] = 0     # Blue channel
        rgba_mask[..., 3] = mask  # Alpha channel (full opacity, same as _extract_masked_region)
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', rgba_mask)
        mask_bytes = buffer.tobytes()
        
        # Convert to base64
        mask_base64 = base64.b64encode(mask_bytes).decode('utf-8')
        return f"data:image/png;base64,{mask_base64}"
    
    def _extract_masked_region(self, image_path: str, mask: np.ndarray, bbox: np.ndarray) -> Optional[str]:
        """Extract the image region within the bounding box and apply the mask.
        
        Returns the cropped and masked image as base64 PNG.
        """
        try:
            # Load the original image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert bbox to integers
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Crop the image to the bounding box
            cropped = image[y1:y2, x1:x2]
            if cropped.size == 0:
                return None
            
            # Resize mask to match cropped image if needed
            mask_cropped = mask[y1:y2, x1:x2]
            if mask_cropped.shape != cropped.shape[:2]:
                mask_cropped = cv2.resize(mask_cropped, (cropped.shape[1], cropped.shape[0]), interpolation=cv2.INTER_NEAREST)
            
            # Apply mask to the cropped image (only keep masked region, make rest transparent)
            if len(cropped.shape) == 3:
                # BGR image
                masked_image = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)
            else:
                # Grayscale image
                masked_image = cv2.cvtColor(cropped, cv2.COLOR_GRAY2BGRA)
            
            # Set alpha channel based on mask
            masked_image[:, :, 3] = mask_cropped
            
            # Encode as PNG
            _, buffer = cv2.imencode('.png', masked_image)
            image_bytes = buffer.tobytes()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Failed to extract masked region: {e}")
            return None
    
    def _base64_to_mask(self, mask_base64: str) -> Optional[np.ndarray]:
        """Convert base64 string to numpy array mask."""
        try:
            # Remove data URL prefix if present
            if ',' in mask_base64:
                mask_base64 = mask_base64.split(',')[1]
            
            # Decode base64
            mask_bytes = base64.b64decode(mask_base64)
            
            # Read as image
            mask = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
            
            # Convert to binary mask
            if mask is not None:
                mask = (mask > 0).astype(np.uint8)
            
            return mask
        except Exception as e:
            logger.error(f"Failed to decode mask from base64: {e}")
            return None
    
    def apply_mask_to_image(
        self, 
        image_path: str, 
        mask: np.ndarray,
        fill_color: Optional[Tuple[int, int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Apply a mask to an image, optionally filling the masked region.
        
        Args:
            image_path: Path to the source image
            mask: Binary mask (H, W)
            fill_color: Optional RGB color to fill the masked region
            
        Returns:
            Image with mask applied, or None if failed
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Resize mask to match image dimensions if needed
            if mask.shape != image.shape[:2]:
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]), 
                                interpolation=cv2.INTER_NEAREST)
            
            # Create a copy of the image
            result = image.copy()
            
            if fill_color is not None:
                # Fill the masked region with the specified color
                result[mask > 0] = fill_color
            else:
                # Apply transparency effect (for visualization)
                # Create a semi-transparent overlay
                overlay = result.copy()
                result[mask > 0] = [0, 0, 255]  # Red overlay by default
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to apply mask to image: {e}")
            return None
    
    def extract_object_with_mask(
        self, 
        image_path: str, 
        mask: np.ndarray,
        background_color: Optional[Tuple[int, int, int]] = (255, 255, 255)
    ) -> Optional[np.ndarray]:
        """
        Extract an object from an image using a mask.
        
        Args:
            image_path: Path to the source image
            mask: Binary mask (H, W)
            background_color: Background color for transparent areas
            
        Returns:
            Extracted object as RGBA image, or None if failed
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert to RGBA
            if image.shape[2] == 3:
                image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            else:
                image_rgba = image.copy()
            
            # Resize mask to match image dimensions
            if mask.shape != image.shape[:2]:
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]), 
                                interpolation=cv2.INTER_NEAREST)
            
            # Apply mask to alpha channel
            alpha = (mask > 0).astype(np.uint8) * 255
            image_rgba[:, :, 3] = alpha
            
            # If background color is provided, fill the transparent areas
            if background_color is not None:
                bg_image = np.full_like(image_rgba, background_color)
                image_rgba = cv2.bitwise_or(
                    cv2.bitwise_and(image_rgba, image_rgba),
                    cv2.bitwise_and(bg_image, bg_image, mask=cv2.bitwise_not(alpha))
                )
            
            return image_rgba
            
        except Exception as e:
            logger.error(f"Failed to extract object with mask: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_available():
            return {"available": False, "error": "Model not loaded"}
        
        try:
            model_info = {
                "available": True,
                "model_type": "SAM3",
                "device": self.device,
                "half_precision": self.half_precision,
                "embedding_cache_size": len(self.embedding_cache),
                "semantic_model_available": self.semantic_model is not None,
                "visual_model_available": self.model is not None,
            }
            
            # Try to get model parameters for both models
            for model_name, model in [("semantic", self.semantic_model), ("visual", self.model)]:
                if model:
                    try:
                        if hasattr(model, 'model') and hasattr(model.model, 'parameters'):
                            total_params = sum(p.numel() for p in model.model.parameters())
                            model_info[f"{model_name}_parameters"] = total_params
                        elif hasattr(model, 'parameters'):
                            total_params = sum(p.numel() for p in model.parameters())
                            model_info[f"{model_name}_parameters"] = total_params
                    except:
                        pass
            
            return model_info
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def cut_from_image(
        self, 
        image_path: str, 
        mask: np.ndarray,
        fill_color: Optional[Tuple[int, int, int]] = None
    ) -> Optional[str]:
        """
        Cut a region from an image using a mask.
        Removes the masked region from the image and returns the updated image as base64.
        
        Args:
            image_path: Path to the source image file
            mask: Binary mask (H, W) where 255 = region to cut
            fill_color: Optional RGB color to fill the cut region (default: transparent for PNG)
            
        Returns:
            Updated image as base64 PNG, or None if failed
        """
        try:
            # Load the original image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            
            logger.info(f"Cut: Original image shape: {image.shape}, path: {image_path}")
            
            # Ensure mask is binary
            mask = (mask > 0).astype(np.uint8)
            logger.info(f"Cut: Mask shape: {mask.shape}, unique values: {np.unique(mask)}")
            
            # Resize mask to match image if needed
            if mask.shape != image.shape[:2]:
                logger.info(f"Cut: Resizing mask from {mask.shape} to {image.shape[:2]}")
                mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
            
            # Convert to BGRA to support transparency
            if len(image.shape) == 3:
                image_rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            else:
                image_rgba = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
            
            # Apply mask: set alpha to 0 (transparent) where mask is 255
            image_rgba[:, :, 3] = np.where(mask > 0, 0, image_rgba[:, :, 3])
            logger.info(f"Cut: Applied mask - transparent pixels: {np.sum(mask > 0)}, total pixels: {mask.size}")
            
            # If fill color is provided, fill the region with that color
            if fill_color is not None:
                # Fill with the specified color where mask is 255
                for c in range(3):  # B, G, R channels
                    image_rgba[:, :, c] = np.where(mask > 0, fill_color[2 - c], image_rgba[:, :, c])
                # Set alpha to 255 (opaque) for filled region
                image_rgba[:, :, 3] = np.where(mask > 0, 255, image_rgba[:, :, 3])
            
            # Save the updated image as PNG to preserve transparency
            # Change the extension to .png if it's not already
            # Ensure we're working with absolute paths
            if not os.path.isabs(image_path):
                image_path = os.path.abspath(image_path)
            
            save_path = image_path
            if not image_path.lower().endswith('.png'):
                save_path = image_path.rsplit('.', 1)[0] + '.png'
            
            # Save the new image first before deleting the original
            try:
                cv2.imwrite(save_path, image_rgba)
                logger.info(f"Cut: Saved cut image to {save_path}")
                # Verify the file was actually saved
                if not os.path.exists(save_path):
                    logger.error(f"Cut: File not found after save: {save_path}")
                    return None
            except Exception as e:
                logger.error(f"Cut: Failed to save image to {save_path}: {e}")
                return None
            
            # If we changed the extension, delete the original file
            if save_path != image_path:
                try:
                    os.remove(image_path)
                    logger.info(f"Cut: Removed original file: {image_path}")
                    # Clear embedding cache for the old path
                    old_cache_key_prefix = f"embeddings_{image_path}"
                    keys_to_remove = [k for k in self.embedding_cache.keys() if k.startswith(old_cache_key_prefix)]
                    for key in keys_to_remove:
                        del self.embedding_cache[key]
                    logger.info(f"Cut: Cleared {len(keys_to_remove)} cache entries for old path")
                except Exception as e:
                    logger.warning(f"Cut: Failed to remove original file {image_path}: {e}")
                    # Even if we can't delete the original, the new file is saved, so continue
            
            # Also return as base64 PNG
            _, buffer = cv2.imencode('.png', image_rgba)
            image_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            logger.info(f"Cut: Returning base64 image of shape {image_rgba.shape}")
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Failed to cut from image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def segment_with_multiple_text_prompts(
        self, 
        image_path: str, 
        text_prompts: List[str],
        use_cached_embeddings: bool = True
    ) -> Dict[str, List[SegmentedObject]]:
        """
        Segment an image using multiple text prompts.
        
        This uses SAM3's concept segmentation to find ALL instances of EACH concept.
        
        Args:
            image_path: Path to the image file
            text_prompts: List of text descriptions (e.g., ["person", "car", "dog"])
            use_cached_embeddings: Whether to use cached embeddings
            
        Returns:
            Dictionary mapping each prompt to its list of segmented objects
        """
        if not self.is_available() or self.semantic_model is None:
            logger.error("SAM3 semantic model not available")
            return {}
        
        try:
            # Use the semantic model
            predictor = self.semantic_model
            
            # Perform segmentation with all text prompts at once
            results = predictor(source=image_path, text=text_prompts)
            
            # Organize results by prompt
            objects_by_prompt = {}
            
            # Process results
            if results and hasattr(results, 'masks') and hasattr(results, 'boxes'):
                masks = results.masks.data
                boxes = results.boxes.xyxy
                
                # Get the class names/labels if available
                class_names = getattr(results, 'names', None)
                
                for i in range(len(masks)):
                    mask = masks[i].cpu().numpy()
                    mask = (mask > 0).astype(np.uint8) * 255
                    
                    bbox = boxes[i].cpu().numpy()
                    
                    # Determine which prompt this mask belongs to
                    # If we have class names, use them; otherwise distribute evenly
                    if class_names is not None and i < len(class_names):
                        prompt = class_names[i]
                    else:
                        # Distribute masks to prompts (SAM3 returns all instances of all prompts)
                        prompt_idx = i % len(text_prompts)
                        prompt = text_prompts[prompt_idx]
                    
                    obj = SegmentedObject(
                        name=f"{prompt}_{len(objects_by_prompt.get(prompt, []))}",
                        source_image_path=image_path,
                        mask=mask,
                        bounding_box=BoundingBox(
                            x1=float(bbox[0]), 
                            y1=float(bbox[1]), 
                            x2=float(bbox[2]), 
                            y2=float(bbox[3])
                        ),
                    )
                    
                    obj.mask_base64 = self._mask_to_base64(mask)
                    
                    if prompt not in objects_by_prompt:
                        objects_by_prompt[prompt] = []
                    objects_by_prompt[prompt].append(obj)
            
            logger.info(f"Multi-prompt segmentation found {sum(len(v) for v in objects_by_prompt.values())} objects for {len(text_prompts)} prompts")
            return objects_by_prompt
            
        except Exception as e:
            logger.error(f"Failed to segment with multiple text prompts: {e}")
            return {}


# Global instance
segmentation_service = None


def get_segmentation_service() -> SAM3SegmentationService:
    """Get the global segmentation service instance."""
    global segmentation_service
    if segmentation_service is None:
        segmentation_service = SAM3SegmentationService()
    return segmentation_service


def reset_segmentation_service():
    """Reset the global segmentation service."""
    global segmentation_service
    if segmentation_service is not None:
        segmentation_service.clear_cache()
    segmentation_service = SAM3SegmentationService()
