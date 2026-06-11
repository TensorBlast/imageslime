# Multi-Point Segmentation Workflow

## Overview
Implemented a new segmentation workflow that allows users to click multiple points to build up a segmentation mask before finalizing.

## How It Works

### User Workflow
1. **Select the Segment tool** (🎯 button)
2. **Click on an image** → Starts segmentation, adds first point
3. **Click more points** → Each click adds a point and updates the preview mask
4. **Finalize** by either:
   - Pressing **Enter** key
   - **Clicking and dragging** the preview area
   - Clicking the "Finish Segmentation" button (if added)
5. **Cancel** by pressing **Escape**

### Visual Feedback
- **Preview Mask**: Semi-transparent (60% opacity) showing the current segmentation
- **Preview Border**: Yellow dashed border around the segmented area
- **Status Bar**: Shows "Segmenting... (N points - click more, drag to finish, or press Enter)"

## Implementation Details

### State Management
Added new state variables:
```javascript
state.isSegmenting = false;           // Whether segmentation is in progress
state.segmentationLayer = null;       // The layer being segmented
state.segmentationPoints = [];        // Array of {x, y} points
state.segmentationPreviewMask = null; // Base64 mask from backend
state.segmentationPreviewBbox = null; // Bounding box of preview
state.segmentationPreviewImage = null;// Base64 cropped image from backend
state.segmentationPreviewImg = null;  // Image object for preview
```

### Key Functions

#### `addSegmentationPoint(layer, relX, relY)`
- Called when user clicks on a layer with Segment tool
- If clicking a different layer, resets segmentation state
- Adds new point to `segmentationPoints`
- Calls `updateSegmentationPreview()` to update the preview

#### `updateSegmentationPreview(layer)`
- Sends all current points to backend via `/api/v1/segmentation/points`
- Receives updated mask and cropped image
- Stores preview data and triggers re-render

#### `finishSegmentation()`
- Creates final object from preview data
- Calculates center position from bounding box
- Creates object with:
  - Mask base64
  - Cropped image base64
  - Bounding box
  - Position at center of segmented area
  - Auto-incremented z-index
- Resets segmentation state
- Saves to history

#### `resetSegmentation()`
- Cancels current segmentation
- Clears all segmentation state
- Triggers re-render

#### `drawSegmentationPreview()`
- Draws the preview mask on the canvas
- Applies layer transformations (position, rotation, scale)
- Draws semi-transparent mask with yellow dashed border

### Backend Integration
The frontend sends all points to `/api/v1/segmentation/points` which:
1. Takes the image embeddings (pre-computed on upload)
2. Uses all points to generate a more accurate mask
3. Returns the mask and cropped image

## Merging Overlapping Selections

The current implementation sends **all points** to the backend for each update. The backend (SAM3) automatically handles merging overlapping selections because:

1. All points are labeled as "foreground" (label=1)
2. SAM3's mask decoder naturally connects nearby points
3. If points are in overlapping regions, they contribute to the same mask

### Example: Selecting a Person
1. Click on shirt → Point added, mask shows shirt area
2. Click on face → Point added, mask expands to include face
3. Click on pants → Point added, mask expands to full person
4. Press Enter → Final object created with full person mask

### Example: Separate Objects
1. Click on tree → Point added, mask shows tree
2. Click on car (far from tree) → Point added, mask shows tree + car
3. Press Enter → Single object created with both tree and car (if bounding boxes overlap)
   - If bounding boxes don't overlap, may create separate masks

## Keyboard Shortcuts
- **Enter**: Finalize current segmentation
- **Escape**: Cancel current segmentation

## Future Improvements

### 1. Bounding Box Overlap Detection
Currently, the backend handles merging. We could add client-side logic:
```javascript
function doBoundingBoxesOverlap(bbox1, bbox2) {
    return !(bbox1.x2 < bbox2.x1 || 
             bbox1.x1 > bbox2.x2 || 
             bbox1.y2 < bbox2.y1 || 
             bbox1.y1 > bbox2.y2);
}
```

### 2. Visual Preview of Multiple Masks
Show each individual point's contribution before merging.

### 3. Undo Last Point
Add ability to remove the last point before finalizing.

### 4. Minimum Points Requirement
Require at least 1 point before showing preview.

### 5. Auto-Finalize on Inactivity
Finalize segmentation if user hasn't clicked for N seconds.

## Testing
1. Upload an image
2. Select Segment tool
3. Click on different parts of an object
4. Verify preview updates with each click
5. Press Enter or drag to finalize
6. Verify object is created with merged mask
7. Press Escape to cancel and verify state is reset
