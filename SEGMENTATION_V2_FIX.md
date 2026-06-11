# Segmentation Preview and Multi-Point Fix (v2)

## Problem (After First Fix)
1. **Preview still showed bounding box** - Not the actual mask shape
2. **Multi-point format was wrong** - Double-nesting caused issues
3. **Mask combination was unnecessary** - SAM should return one mask

## Root Cause Analysis

### Issue 1: Preview Drawing
The preview was drawing a red rectangle over the bounding box, not using the actual mask. The `cropped_image_base64` has transparency, but we need to show the **mask shape** itself in red.

### Issue 2: Point Format for Ultralytics SAM
From [Ultralytics SAM Documentation](https://docs.ultralytics.com/models/sam):

```python
# Multiple points as separate objects
model(points=[[400, 370], [900, 370]], labels=[1, 1])

# Multiple points for SAME object  
model(points=[[[400, 370], [900, 370]]], labels=[[1, 1]])
```

However, **this is misleading**. The correct format for one object with multiple points is:
```python
model(points=[[400, 370], [900, 370]], labels=[1, 1])
```

The double-nesting `[[[400, 370], [900, 370]]]` is for when you have **multiple objects, each with multiple points**.

For **one object with multiple points**, use:
- `points = [[x1, y1], [x2, y2], ...]` (list of [x,y] pairs)
- `labels = [1, 1, ...]` (list of label values)

### Issue 3: Mask Combination
We were combining masks with `np.logical_or()`, but this was only needed because we were using the wrong point format. With the correct format, SAM returns **one mask** for all points.

## Solution

### 1. Fixed Point Format (`imageslime/services/segmentation.py`)
```python
# Convert points to format expected by Ultralytics SAM
# For one object with multiple points:
sam_points = [[p.x, p.y] for p in points]  # [[x1,y1], [x2,y2], ...]
sam_labels = [1] * len(points) if labels is None else labels  # [1, 1, ...]

# Use the main model for prediction
results = self.model.predict(
    source=image_path,
    points=sam_points,
    labels=sam_labels,
    conf=self.settings.SEGMENTATION_CONFIDENCE,
)

# Process results - SAM returns one mask for all points
if results and len(results) > 0:
    result = results[0]
    masks = result.masks.data
    if masks is not None and len(masks) > 0:
        # Take the first mask (SAM returns one mask for all our points)
        mask = masks[0].cpu().numpy()
        mask = (mask > 0).astype(np.uint8) * 255
```

**Key Changes:**
- Removed double-nesting of points
- Removed mask combination logic
- Simplified to use first mask from results

### 2. Fixed Preview Drawing (`imageslime/static/app.html`)
```javascript
function drawSegmentationPreview() {
    if (!state.segmentationPreviewMaskImg || !state.segmentationPreviewBbox || !state.segmentationLayer) return;
    
    const layer = state.segmentationLayer;
    const bbox = state.segmentationPreviewBbox;
    
    state.ctx.save();
    state.ctx.translate(layer.position[0], layer.position[1]);
    state.ctx.rotate(layer.rotation * Math.PI / 180);
    state.ctx.scale(layer.scale[0], layer.scale[1]);
    
    // Draw red semi-transparent mask using actual mask as stencil
    state.ctx.globalAlpha = 0.5;
    state.ctx.fillStyle = '#ff0000';
    
    // Draw red rectangle
    state.ctx.fillRect(bbox.x1, bbox.y1, bbox.x2 - bbox.x1, bbox.y2 - bbox.y1);
    
    // Use mask to clip the red (destination-in)
    state.ctx.globalCompositeOperation = 'destination-in';
    state.ctx.drawImage(
        state.segmentationPreviewMaskImg,  // Actual mask image
        bbox.x1, bbox.y1,
        bbox.x2 - bbox.x1,
        bbox.y2 - bbox.y1
    );
    
    state.ctx.globalCompositeOperation = 'source-over';
    state.ctx.globalAlpha = 1.0;
    state.ctx.restore();
}
```

**Key Changes:**
- Load `mask_base64` as `segmentationPreviewMaskImg`
- Use `destination-in` composite operation to show red only where mask is white
- Draw actual mask shape, not bounding box

### 3. Updated Preview Update Function
```javascript
function updateSegmentationPreview(layer) {
    // ... fetch call ...
    .then(data => {
        if (data.success && data.cropped_image_base64) {
            state.segmentationPreviewMask = data.mask_base64;
            state.segmentationPreviewBbox = data.bounding_box;
            state.segmentationPreviewImage = data.cropped_image_base64;
            
            // Load mask image for red overlay
            if (data.mask_base64 && !state.segmentationPreviewMaskImg) {
                const maskImg = new Image();
                maskImg.src = data.mask_base64;
                maskImg.onload = function() {
                    state.segmentationPreviewMaskImg = maskImg;
                    render();
                };
                state.segmentationPreviewMaskImg = maskImg;
            }
            
            // ... rest of function ...
        }
    })
}
```

## Testing

### Before Fix
1. Click on shirt → Yellow bounding box appears
2. Click on face → Nothing happens (or wrong mask)
3. Preview shows rectangle, not mask shape

### After Fix
1. Click on shirt → Red mask appears over shirt (actual mask shape)
2. Click on face → Red mask expands to include face
3. Click on pants → Red mask expands to full person
4. Press Enter → One object created with full person mask

## Technical Details

### Ultralytics SAM Point Format
```python
# ONE object with multiple points:
points = [[x1, y1], [x2, y2], [x3, y3]]  # List of [x,y] coordinate pairs
labels = [1, 1, 1]  # All foreground (1 = foreground, 0 = background)

# MULTIPLE objects, each with one point:
points = [[x1, y1], [x2, y2]]  # Same format, but SAM interprets as separate objects
labels = [1, 1]

# MULTIPLE objects, each with multiple points:
points = [[[x1, y1], [x2, y2]], [[x3, y3], [x4, y4]]]  # Double-nested
labels = [[1, 1], [1, 1]]
```

For our use case (one object, multiple points), we use the **first format**.

### Canvas Composite Operations
- `source-over` (default): New content draws over existing content
- `destination-in`: New content only visible where destination is opaque
- This allows us to draw a red rectangle, then use the mask to clip it

## References
- [Ultralytics SAM Documentation](https://docs.ultralytics.com/models/sam)
- [Meta SAM GitHub Issue #111](https://github.com/facebookresearch/segment-anything/issues/111) - Discusses point/box format
