# Export Button Fix

## Problem
The Export button was saving a black image with text "Project 1" instead of the actual canvas content.

## Root Cause
The frontend was calling `/api/v1/project/export/default` which returned a placeholder image from the backend. The backend didn't have access to the frontend's layer/object state.

## Solution
Implemented **client-side export** that:
1. Creates a temporary canvas matching the viewport size
2. Draws all visible layers and objects sorted by z-index
3. Applies all transformations (position, rotation, scale, opacity)
4. Downloads as PNG file

## Implementation Details

### Frontend (`imageslime/static/app.html`)
```javascript
function exportProject() {
    // Create temporary canvas
    const exportCanvas = document.createElement('canvas');
    const exportCtx = exportCanvas.getContext('2d');
    
    // Set size to match viewport
    exportCanvas.width = state.canvas.width;
    exportCanvas.height = state.canvas.height;
    
    // Fill with background
    exportCtx.fillStyle = '#1a1a2e';
    exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    
    // Draw all items sorted by z-index
    const allItems = [...state.layers, ...state.objects].sort((a, b) => a.z_index - b.z_index);
    
    for (const item of allItems) {
        if (!item.visible) continue;
        
        // Apply transformations
        exportCtx.save();
        exportCtx.translate(item.position[0], item.position[1]);
        exportCtx.rotate(item.rotation * Math.PI / 180);
        exportCtx.scale(item.scale[0], item.scale[1]);
        exportCtx.globalAlpha = item.opacity;
        
        // Draw object or layer
        if (item.type === 'object' || item.cropped_image_base64) {
            if (item.cropped_image && item.cropped_image.complete && item.bounding_box) {
                const bbox = item.bounding_box;
                exportCtx.drawImage(
                    item.cropped_image,
                    bbox.x1, bbox.y1,
                    bbox.x2 - bbox.x1,
                    bbox.y2 - bbox.y1
                );
            }
        } else if (item.image_obj && item.image_obj.complete) {
            exportCtx.drawImage(
                item.image_obj,
                0, 0, item.width, item.height
            );
        }
        
        exportCtx.globalAlpha = 1.0;
        exportCtx.restore();
    }
    
    // Download as PNG
    exportCanvas.toBlob(function(blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `imageslime_export_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showStatus('Export complete!');
    }, 'image/png');
}
```

### Backend (`imageslime/api/project.py`)
The backend export endpoint is kept for backward compatibility but is no longer used by the frontend. It returns a placeholder image.

## Testing
1. Upload an image
2. Create some segmented objects
3. Click "Export" button
4. Verify the downloaded PNG contains all visible layers and objects

## Future Improvements
- Add option to export as JPEG
- Add option to set export resolution
- Add option to export with transparent background
- Add option to export only selected items
