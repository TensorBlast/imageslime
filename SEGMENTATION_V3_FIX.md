# Segmentation Multi-Point Fix (v3) - Final

## Problem
1. Preview showed bounding box instead of actual mask
2. Additional points didn't update the mask properly
3. Wrong point format caused SAM to return multiple masks

## Solution

### 1. Correct Point Format (Double-Nested)

Based on the Google example you provided:

```python
input_points = [[[500, 375], [1125, 625]]]  # Double-nested: one object, two points
input_labels = [[[1, 0]]]                  # Double-nested: labels for those points
```

**For Ultralytics SAM3:**
```python
# ONE object with multiple points:
sam_points = [[[x1, y1], [x2, y2], [x3, y3]]]  # Double-nested list
sam_labels = [[1, 1, 1]]                   # Double-nested list

# This tells SAM: "All these points belong to ONE object"
```

### 2. Implementation (`imageslime/services/segmentation.py`)

```python
def segment_with_points(self, image_path, points, labels=None, ...):
    # Convert to double-nested format for one object
    sam_points = [[[p.x, p.y] for p in points]]  # [[[x1,y1], [x2,y2], ...]]
    
    if labels is None:
        sam_labels = [[1] * len(points)]  # [[1, 1, ...]]
    else:
        sam_labels = [labels]  # Wrap in outer list
    
    results = self.model.predict(
        source=image_path,
        points=sam_points,
        labels=sam_labels,
        conf=self.settings.SEGMENTATION_CONFIDENCE,
    )
    
    # Process results - assume SAM returns one mask
    if results and len(results) > 0:
        result = results[0]
        masks = result.masks.data
        if masks is not None and len(masks) > 0:
            # Just take the first mask (SAM should return one mask for all points)
            mask = masks[0].cpu().numpy()
            mask = (mask > 0).astype(np.uint8) * 255
```

**Key Points:**
- Double-nesting: `[[[x1,y1], [x2,y2]]]` not `[[x1,y1], [x2,y2]]`
- Labels also double-nested: `[[1,1]]` not `[1,1]`
- **Assume one mask** - don't try to combine masks

### 3. Preview Drawing (`imageslime/static/app.html`)

```javascript
function drawSegmentationPreview() {
    if (!state.segmentationPreviewMaskImg || !state.segmentationPreviewBbox || !state.segmentationLayer) 
        return;
    
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

This uses the actual mask shape (from `mask_base64`) to clip a red overlay, showing the true mask shape.

## Why Double-Nesting?

The nesting levels have meaning:

```python
# Level 0: Batch dimension (usually 1 for single image)
# Level 1: Object dimension (one per object)
# Level 2: Point dimension (points for that object)

# One object with 3 points:
points = [           # Batch (level 0)
    [               # Objects (level 1) - one object
        [x1, y1],   # Point 1 (level 2)
        [x2, y2],   # Point 2
        [x3, y3]    # Point 3
    ]
]

# Two objects, first has 2 points, second has 1 point:
points = [           # Batch
    [               # Object 1
        [x1, y1],
        [x2, y2]
    ],
    [               # Object 2
        [x3, y3]
    ]
]
```

For our use case (one object, multiple points), we use **one object at level 1** with **multiple points at level 2**.

## Testing

### Expected Behavior
1. Click on shirt → Red mask appears over shirt (actual mask shape)
2. Click on face → Mask expands to include face (one continuous mask)
3. Click on pants → Mask expands to full person
4. Press Enter → One object created with full person

### Debugging Tips
If it's not working:
1. Check what `masks` contains in the backend - should be length 1
2. Check the shape of `masks[0]` - should match image dimensions
3. Verify `mask_base64` is being returned to frontend
4. Check `state.segmentationPreviewMaskImg` is loaded in frontend

## References
- Google example (provided by user): Double-nested points format
- Meta SAM: Uses similar nested structure for batch/object/point dimensions
