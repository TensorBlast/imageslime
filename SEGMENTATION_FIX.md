# Segmentation Preview and Multi-Point Fix

## Problem
1. **Preview showed yellow bounding box** instead of red mask
2. **Additional points did nothing** - clicking more points didn't update the mask

## Root Cause

### Issue 1: Preview Style
The `drawSegmentationPreview()` function was drawing:
- A semi-transparent preview image
- A yellow dashed border box

This made it look like a bounding box rather than a mask.

### Issue 2: Multi-Point Format
The segmentation service was sending points to Ultralytics SAM in the wrong format:
```python
# WRONG - treats as separate objects
sam_points = [(x1, y1), (x2, y2)]  # List of tuples
sam_labels = [1, 1]
```

According to [Ultralytics SAM documentation](https://docs.ultralytics.com/models/sam):

```python
# Multiple points as separate objects
model(points=[[400, 370], [900, 370]], labels=[1, 1])

# Multiple points for SAME object (nested list)
model(points=[[[400, 370], [900, 370]]], labels=[[1, 1]])
```

The key difference:
- **`[[400, 370], [900, 370]]`** → Two separate objects
- **`[[[400, 370], [900, 370]]]`** → One object with two points

## Solution

### 1. Fixed Preview Drawing (`imageslime/static/app.html`)
```javascript
function drawSegmentationPreview() {
    // Draw red semi-transparent overlay on the segmented area
    state.ctx.globalAlpha = 0.3;
    state.ctx.fillStyle = '#ff0000';
    state.ctx.fillRect(bbox.x1, bbox.y1, bbox.x2 - bbox.x1, bbox.y2 - bbox.y1);
    state.ctx.globalAlpha = 1.0;
    
    // Draw the preview image (already has transparency from mask)
    state.ctx.drawImage(
        state.segmentationPreviewImg,
        bbox.x1, bbox.y1,
        bbox.x2 - bbox.x1,
        bbox.y2 - bbox.y1
    );
}
```

**Result**: Preview now shows as a red-tinted mask without a border box.

### 2. Fixed Multi-Point Format (`imageslime/services/segmentation.py`)
```python
# Convert points to format expected by Ultralytics SAM
if len(points) == 1:
    # Single point - use simple format
    sam_points = [[points[0].x, points[0].y]]
    sam_labels = [1] if labels is None else [labels[0]]
else:
    # Multiple points - nest them to indicate they're for the same object
    sam_points = [[[p.x, p.y] for p in points]]
    sam_labels = [[1] * len(points)] if labels is None else [labels]

# Use the main model for prediction
results = self.model.predict(
    source=image_path,
    points=sam_points,
    labels=sam_labels,
    conf=self.settings.SEGMENTATION_CONFIDENCE,
)

# Process results - combine masks if multiple were returned
if len(masks) > 1:
    # Combine all masks using logical OR
    combined_mask = np.zeros_like(masks[0].cpu().numpy())
    for m in masks:
        combined_mask = np.logical_or(combined_mask, m.cpu().numpy() > 0)
    mask = combined_mask.astype(np.uint8) * 255
else:
    mask = masks[0].cpu().numpy()
    mask = (mask > 0).astype(np.uint8) * 255
```

**Result**: All points are now treated as belonging to the same object, and the mask expands with each additional click.

## Testing

### Before Fix
1. Click on shirt → Preview shows yellow box
2. Click on face → Nothing happens (mask doesn't update)
3. Press Enter → Only shirt is segmented

### After Fix
1. Click on shirt → Preview shows red mask over shirt
2. Click on face → Preview expands to include face
3. Click on pants → Preview expands to include full person
4. Press Enter → Full person is segmented as one object

## Technical Details

### Point Format Evolution
```
Version 1 (Broken):
  points = [(x1, y1), (x2, y2)]
  labels = [1, 1]
  Result: SAM treats as 2 separate objects → returns 2 masks

Version 2 (Fixed):
  points = [[[x1, y1], [x2, y2]]]
  labels = [[1, 1]]
  Result: SAM treats as 1 object with 2 points → returns 1 mask
```

### Mask Combination
In case SAM still returns multiple masks (edge case), we combine them:
```python
combined_mask = np.zeros_like(masks[0].cpu().numpy())
for m in masks:
    combined_mask = np.logical_or(combined_mask, m.cpu().numpy() > 0)
```

This ensures all mask regions are included in the final result.

## References
- [Ultralytics SAM Documentation](https://docs.ultralytics.com/models/sam)
- [GitHub Issue #15716 - Multiple points in SAM](https://github.com/ultralytics/ultralytics/issues/15716)
