# ImageSlime - Functional Requirements

## Overview
ImageSlime is an interactive image editing tool that allows users to segment objects from images and composite them together, inspired by DingBoard's one-click segmentation workflow.

## Core Concept: One-Click Segmentation

### Single Click = One Segmented Object
- **No Enter key required** - Segmentation happens instantly on click
- **No confirmation needed** - Mask appears immediately where user clicks
- **Each click creates a new separate cut-out** - Users can click multiple times to extract multiple objects
- **No mode switching** - Just click, get a mask, it becomes a draggable layer

### Segmentation Behavior
1. User uploads an image
2. User clicks anywhere on the image
3. System automatically:
   - Runs segmentation with that single point
   - Returns a mask
   - Extracts the object with transparency
   - Creates a new layer with the cut-out
4. User can immediately:
   - Click again to extract another object (new layer)
   - Click on a different area of the same image
   - Click on a different image

### Multi-Point Refinement
- If user clicks **multiple times rapidly** (within ~2000ms) on the same general area:
  - System accumulates points
  - Sends all points together for more accurate segmentation
  - Creates one refined mask when clicking stops
- If user clicks **slowly** or **far from previous points**:
  - Each click creates a separate object/layer

## Layer System

### Layer Types
- **Uploaded images** = Base layers (can be moved, reordered, deleted)
- **Segmented objects** = Cut-out layers with transparency (can be moved, reordered, deleted)

### Layer Operations
- **All layers are draggable by default** - No tool selection needed for basic dragging
- **Right-click any layer** for advanced options:
  - Bring to Front
  - Send to Back
  - Move Forward (one layer up)
  - Move Backward (one layer down)
  - Delete
  - Copy

## Interaction Model

### Mouse Interactions
- **Left-click and drag** = Move layer (works on both images and segmented objects)
- **Right-click** = Show context menu for layer operations
- **No tool switching required** for basic operations

### Tool Bar (Advanced Options)
- **Select** (🖱️) - For precise selection
- **Segment** (✂️) - For one-click extraction
- **Move** (🪃) - Explicit move mode
- **Rotate** (🔄) - Explicit rotate mode
- **Scale** (📐) - Explicit scale mode

## Visual Feedback

### Layer States
- **Hover effect** - Layers highlight slightly when hovered
- **Active layer** - Clearly outlined/highlighted
- **Segmentation preview** - Mask appears briefly before becoming a layer
- **Drag preview** - Outline shows during drag operations

## Composition & Export

### Rendering
- All layers composite in order (back to front)
- Transparency preserved
- Real-time rendering as layers are moved/reordered

### Export Options
- Download final composition as PNG
- Option to download individual layers
- Preserve transparency in output

## User Experience Flow

### Basic Workflow
1. Upload image → appears as layer
2. Click on image → creates segmented object layer
3. Drag object → moves independently
4. Click again → creates another object
5. Right-click → reorder or delete
6. Download → get final composition

### Advanced Workflow
1. Upload multiple images
2. Segment objects from each
3. Drag objects between images
4. Reorder layers (front/back)
5. Delete source images if no longer needed
6. Composite all together
7. Download final result

## Technical Notes

### Backend Requirements
- Fast segmentation (SAM3 or similar)
- Support for single-point and multi-point segmentation
- Return both mask and cropped image with transparency
- Handle multiple concurrent segmentation requests

### Frontend Requirements
- Real-time rendering of layers
- Smooth drag-and-drop
- Layer ordering system
- Context menu for layer operations
- Visual feedback for all interactions
