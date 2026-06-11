# ImageSlime - Technical Architecture

## Overview
This document describes the technical architecture for implementing ImageSlime's one-click segmentation and layer-based compositing system.

## System Architecture

### High-Level Components
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Canvas    │  │   UI/UX     │  │   Layer Manager     │  │
│  │  Rendering  │  │   Controls  │  │  (State Management) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  API        │  │  Upload      │  │  Segmentation        │  │
│  │  Endpoints  │  │  Handler     │  │  Service (SAM3)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Storage                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Uploads    │  │  Temp Files │  │  Embedding Cache    │  │
│  │  Directory  │  │  Directory  │  │  (In-Memory)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### 1. Canvas & Rendering System

#### Layer Rendering Pipeline
```
Input: List of Layers (sorted by z-index)
       └── For each layer:
           ├── Apply transformations (position, rotation, scale)
           ├── Draw image or cropped object
           └── Apply opacity
Output: Composite image on canvas
```

#### Layer Data Structure
```javascript
{
  id: string,                    // Unique identifier
  type: 'image' | 'object',      // Layer type
  name: string,                  // Display name
  
  // Position & Transform
  position: [x, y],             // Canvas position
  rotation: number,              // Degrees
  scale: [x, y],                // Scale factors
  opacity: number,              // 0.0 to 1.0
  z_index: number,              // Layer ordering
  
  // Content
  image_path: string,           // For image layers
  image_base64: string,         // For display
  cropped_image_base64: string, // For object layers
  mask_base64: string,          // Segmentation mask
  
  // Source
  source_image_id: string,      // Reference to source
  bounding_box: {x1, y1, x2, y2} // Mask bounds
}
```

### 2. Input Handling System

#### Event Flow
```
Mouse Event → Check Active Tool → Determine Action
  │
  ├── Select Tool
  │   ├── Click: Select layer at position
  │   └── Drag: Selection rectangle
  │
  ├── Segment Tool
  │   └── Click: Create segmentation at position
  │
  ├── Move Tool
  │   └── Drag: Move selected layer
  │
  ├── Rotate Tool
  │   └── Drag: Rotate selected layer
  │
  └── Scale Tool
      └── Drag: Scale selected layer
```

#### One-Click Segmentation Flow
```
1. User clicks on canvas with Segment tool active
2. Get position relative to canvas
3. Find layer at that position
4. If layer found:
   a. Calculate position relative to layer
   b. Send to backend: {image_id, points: [{x, y}], labels: [1]}
   c. Receive: {mask_base64, cropped_image_base64, bounding_box}
   d. Create new object layer with cropped image
   e. Add to layer list (highest z-index)
   f. Render
```

#### Multi-Point Refinement Flow
```
1. User clicks on canvas with Segment tool
2. Start timer (500ms)
3. If another click within 500ms:
   a. Add point to current segmentation
   b. Send all points to backend
   c. Update preview mask
   d. Reset timer
4. If no click for 500ms:
   a. Finalize segmentation
   b. Create object layer
   c. Clear temporary state
```

### 3. Layer Management System

#### Layer Operations
```javascript
// Adding a layer
function addLayer(layer) {
  layers.push(layer);
  sortLayersByZIndex();
  render();
}

// Removing a layer
function removeLayer(layerId) {
  layers = layers.filter(l => l.id !== layerId);
  render();
}

// Reordering layers
function bringToFront(layer) {
  const maxZ = Math.max(...layers.map(l => l.z_index));
  layer.z_index = maxZ + 1;
  sortLayersByZIndex();
  render();
}

// Moving layer
function moveLayer(layer, dx, dy) {
  layer.position[0] += dx;
  layer.position[1] += dy;
  render();
}
```

#### Layer Sorting
```javascript
// Always render from back to front
function sortLayersByZIndex() {
  layers.sort((a, b) => a.z_index - b.z_index);
}

// Render loop
function render() {
  clearCanvas();
  for (const layer of layers) {
    if (layer.visible) {
      drawLayer(layer);
    }
  }
}
```

### 4. UI State Management

#### Application State
```javascript
{
  // Canvas
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  
  // Layers
  layers: Layer[],           // All image layers
  objects: Layer[],          // All segmented objects (also layers)
  activeLayer: Layer|null,  // Currently selected
  
  // Tools
  activeTool: string,        // 'select' | 'segment' | 'move' | 'rotate' | 'scale'
  
  // Segmentation
  isSegmenting: boolean,
  segmentationPoints: Point[],
  segmentationTimer: number|null,
  
  // Drag & Drop
  isDragging: boolean,
  dragStart: Point,
  dragLayer: Layer|null,
  
  // Mouse
  mousePos: Point,
  hoverLayer: Layer|null
}
```

## Backend Architecture

### 1. API Endpoints

#### Image Upload
```
POST /api/v1/images/upload
- Input: FormData with image file
- Output: {image_id, image_path, thumbnail_base64, width, height}
- Process: Save to uploads/, create thumbnail
```

#### Segmentation
```
POST /api/v1/segmentation/points
- Input: {image_id, points: [{x, y}], labels: [1]}
- Output: {mask_base64, cropped_image_base64, bounding_box}
- Process: 
  1. Load image
  2. Run SAM3 segmentation
  3. Extract mask
  4. Crop and apply mask to image
  5. Return both mask and cropped image
```

#### Layer Management
```
GET /api/v1/project/load
POST /api/v1/project/save
GET /api/v1/project/export
```

### 2. Segmentation Service

#### SAM3 Integration
```python
class SAM3SegmentationService:
    def __init__(self):
        self.model = SAM("sam3.pt")  # Ultralytics SAM3
        
    def segment_with_points(self, image_path, points, labels):
        # Run segmentation
        results = self.model.predict(
            source=image_path,
            points=points,
            labels=labels
        )
        
        # Extract mask
        mask = results[0].masks.data[0].cpu().numpy()
        bbox = results[0].boxes.xyxy[0].cpu().numpy()
        
        # Extract cropped image with transparency
        cropped_img = self._extract_masked_region(image_path, mask, bbox)
        
        return {
            'mask': mask,
            'mask_base64': self._mask_to_base64(mask),
            'cropped_image_base64': self._image_to_base64(cropped_img),
            'bounding_box': bbox
        }
```

#### Image Extraction
```python
def _extract_masked_region(self, image_path, mask, bbox):
    # Load image
    img = cv2.imread(image_path)
    
    # Crop to bounding box
    x1, y1, x2, y2 = map(int, bbox)
    cropped = img[y1:y2, x1:x2]
    
    # Crop mask to same region
    mask_cropped = mask[y1:y2, x1:x2]
    
    # Convert to BGRA
    if len(cropped.shape) == 3:
        rgba = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)
    else:
        rgba = cv2.cvtColor(cropped, cv2.COLOR_GRAY2BGRA)
    
    # Apply mask to alpha channel
    rgba[:, :, 3] = mask_cropped
    
    return rgba
```

### 3. Data Models

#### Layer Model (Backend)
```python
@dataclass
class Layer:
    id: str
    name: str
    layer_type: str  # 'image' | 'object'
    
    # Position
    position_x: float
    position_y: float
    rotation: float
    scale_x: float
    scale_y: float
    z_index: int
    
    # Content
    image_path: Optional[str]
    mask_path: Optional[str]
    cropped_image_path: Optional[str]
    
    # Metadata
    source_image_id: Optional[str]
    bounding_box: Optional[Dict]
```

#### Project Model
```python
@dataclass
class Project:
    id: str
    name: str
    layers: List[Layer]
    created_at: datetime
    updated_at: datetime
```

## Implementation Strategy

### Phase 1: Core Segmentation
1. ✅ Image upload working
2. ✅ SAM3 segmentation working
3. ✅ Mask extraction working
4. ⏳ **Cropped image extraction** - Return actual cut-out with transparency
5. ⏳ **One-click segmentation** - Remove Enter key requirement

### Phase 2: Layer System
1. ⏳ **Unified layer system** - Treat images and objects the same
2. ⏳ **Layer ordering** - z-index management
3. ⏳ **Layer rendering** - Draw all layers in order
4. ⏳ **Layer selection** - Click to select any layer

### Phase 3: Interaction
1. ⏳ **Direct dragging** - Left-click and drag any layer
2. ⏳ **Context menu** - Right-click for layer operations
3. ⏳ **Multi-point segmentation** - Accumulate points within timeout
4. ⏳ **Tool integration** - Make tools work with layers

### Phase 4: Polish
1. ⏳ **Visual feedback** - Highlights, previews
2. ⏳ **Export** - Download composition
3. ⏳ **Performance** - Optimize rendering
4. ⏳ **Error handling** - Graceful degradation

## Current Implementation Status

### What's Working
- ✅ Image upload to `/api/v1/images/upload`
- ✅ SAM3 model loading and segmentation
- ✅ Mask generation and base64 encoding
- ✅ Basic layer rendering
- ✅ Object creation from segmentation

### What Needs Fixing
1. **Cropped image extraction** - Currently returns mask only, need to return actual image cutout
2. **One-click segmentation** - Currently requires Enter key, should be automatic
3. **Layer dragging** - Currently only works with Move tool, should work with direct click
4. **Layer selection** - Hit detection needs to account for transformations
5. **Context menu** - Needs to work with layers
6. **Multi-point accumulation** - Needs timeout logic

### Key Technical Decisions

#### 1. Unified Layer System
```javascript
// Instead of separate arrays for images and objects
state.layers = [
  {type: 'image', ...},
  {type: 'object', ...}
]
```

#### 2. Direct Manipulation
```javascript
// Click on any layer to select it
canvas.addEventListener('mousedown', (e) => {
  const layer = getLayerAtPosition(pos);
  if (layer) {
    state.activeLayer = layer;
    state.dragStart = pos;
    state.isDragging = true;
  }
});

// Drag to move
canvas.addEventListener('mousemove', (e) => {
  if (state.isDragging && state.activeLayer) {
    const dx = pos.x - state.dragStart.x;
    const dy = pos.y - state.dragStart.y;
    state.activeLayer.position[0] += dx;
    state.activeLayer.position[1] += dy;
    state.dragStart = pos;
    render();
  }
});
```

#### 3. One-Click Segmentation with Timeout
```javascript
let segmentationTimeout = null;

function handleSegmentClick(pos, layer) {
  // Add point
  state.segmentationPoints.push(pos);
  
  // Clear existing timeout
  if (segmentationTimeout) {
    clearTimeout(segmentationTimeout);
  }
  
  // Send segmentation request
  sendSegmentationRequest(layer);
  
  // Set new timeout
  segmentationTimeout = setTimeout(() => {
    // Finalize - create object layer
    createObjectFromSegmentation(layer);
    state.segmentationPoints = [];
  }, 500); // 500ms timeout
}
```

#### 4. Cropped Image Extraction
```python
# In segmentation service
def segment_with_points(self, image_path, points, labels):
    results = self.model.predict(source=image_path, points=points, labels=labels)
    
    mask = results[0].masks.data[0].cpu().numpy()
    bbox = results[0].boxes.xyxy[0].cpu().numpy()
    
    # Extract the actual image region with transparency
    cropped_img = self._extract_masked_region(image_path, mask, bbox)
    
    return {
        'mask_base64': self._mask_to_base64(mask),
        'cropped_image_base64': self._image_to_base64(cropped_img),
        'bounding_box': bbox.tolist()
    }
```

## File Structure

```
imageslime/
├── static/
│   ├── app.html          # Main frontend (needs refactoring)
│   └── style.css         # Styles
├── api/
│   ├── __init__.py       # API router
│   ├── images.py         # Image upload endpoint
│   ├── segmentation.py   # Segmentation endpoints
│   └── project.py        # Project save/load/export
├── services/
│   └── segmentation.py   # SAM3 service (needs cropped image extraction)
├── models.py             # Data models (needs updating)
└── main.py               # FastAPI app
```

## Next Steps

### Immediate (This Session)
1. Implement cropped image extraction in `services/segmentation.py`
2. Update frontend to use cropped images instead of masks
3. Remove Enter key requirement for segmentation
4. Implement direct layer dragging (no tool selection needed)

### Short Term
1. Implement unified layer system
2. Add context menu for layer operations
3. Implement multi-point segmentation with timeout
4. Fix layer selection hit detection

### Long Term
1. Add layer reordering (front/back)
2. Implement export functionality
3. Add visual feedback (highlights, previews)
4. Optimize rendering performance
