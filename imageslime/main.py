"""
Main application file for ImageSlime.

This module sets up the FastAPI application and all its dependencies.
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

from .config import get_settings, Settings
from .api import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global app instance
_app: Optional[FastAPI] = None


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Optional settings instance. If None, uses global settings.
        
    Returns:
        Configured FastAPI application instance.
    """
    global _app
    
    if settings is None:
        settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="ImageSlime API",
        description="Interactive image segmentation and editing tool using SAM3",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # Store settings in app state
    app.state.settings = settings
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(api_router)
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint that serves the main HTML page."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ImageSlime - Interactive Image Segmentation</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    margin: 0;
                    padding: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    padding: 40px;
                    max-width: 800px;
                    width: 90%;
                    text-align: center;
                }
                h1 {
                    color: #333;
                    font-size: 2.5em;
                    margin-bottom: 20px;
                }
                .subtitle {
                    color: #666;
                    font-size: 1.1em;
                    margin-bottom: 30px;
                }
                .features {
                    text-align: left;
                    margin: 30px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                .features h3 {
                    color: #333;
                    margin-bottom: 15px;
                }
                .features ul {
                    padding-left: 20px;
                }
                .features li {
                    margin-bottom: 8px;
                    color: #555;
                }
                .btn {
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 8px;
                    font-size: 1.1em;
                    cursor: pointer;
                    text-decoration: none;
                    margin: 10px;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                }
                .btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .btn-secondary {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                }
                .status {
                    margin-top: 30px;
                    padding: 15px;
                    background: #e3f2fd;
                    border-radius: 8px;
                    color: #1976d2;
                }
                .loading {
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border: 3px solid rgba(255,255,255,.3);
                    border-radius: 50%;
                    border-top-color: #fff;
                    animation: spin 1s ease-in-out infinite;
                    margin-right: 10px;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎨 ImageSlime</h1>
                <p class="subtitle">Interactive Image Segmentation & Editing with SAM3</p>
                
                <div class="features">
                    <h3>✨ Features</h3>
                    <ul>
                        <li>🖼️ Upload and manage multiple images</li>
                        <li>🎯 Click to select objects with SAM3 segmentation</li>
                        <li>📦 Extract and manipulate segmented objects</li>
                        <li>🔄 Layer-based composition with drag-and-drop</li>
                        <li>🎨 Rotate, scale, and reposition objects</li>
                        <li>💾 Save and export your creations</li>
                    </ul>
                </div>
                
                <div>
                    <a href="/app" class="btn btn-primary">Launch ImageSlime</a>
                    <a href="/api/docs" class="btn btn-secondary">API Documentation</a>
                </div>
                
                <div class="status" id="status">
                    <span class="loading"></span>
                    <span>Checking SAM3 model...</span>
                </div>
            </div>
            
            <script>
                // Check if SAM3 model is available
                fetch('/api/v1/segmentation/model-info')
                    .then(response => response.json())
                    .then(data => {
                        const statusEl = document.getElementById('status');
                        if (data.model_info && data.model_info.available) {
                            statusEl.innerHTML = '✅ SAM3 model is ready!';
                            statusEl.style.background = '#c8e6c9';
                            statusEl.style.color = '#2e7d32';
                        } else {
                            statusEl.innerHTML = '⚠️ SAM3 model not available. Please install sam3.pt';
                            statusEl.style.background = '#ffcdd2';
                            statusEl.style.color = '#c62828';
                        }
                    })
                    .catch(error => {
                        document.getElementById('status').innerHTML = 
                            '❌ Failed to check model status: ' + error.message;
                    });
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
    # App endpoint that serves the main application
    @app.get("/app", response_class=HTMLResponse)
    async def app_page():
        """Serve the main application page."""
        # This will be replaced with the actual frontend
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ImageSlime - Editor</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #1a1a2e;
                    color: #eee;
                    min-height: 100vh;
                    overflow: hidden;
                }
                
                #app-container {
                    display: flex;
                    height: 100vh;
                    width: 100vw;
                }
                
                #sidebar {
                    width: 250px;
                    background: #16213e;
                    padding: 20px;
                    border-right: 1px solid #0f3460;
                    display: flex;
                    flex-direction: column;
                }
                
                #canvas-container {
                    flex: 1;
                    position: relative;
                    overflow: hidden;
                }
                
                #main-canvas {
                    position: absolute;
                    top: 0;
                    left: 0;
                    cursor: crosshair;
                }
                
                .section-title {
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    color: #0f3460;
                    margin-bottom: 10px;
                    padding: 10px;
                    border-bottom: 1px solid #0f3460;
                }
                
                .layer-item {
                    padding: 10px;
                    margin: 5px 0;
                    background: #0f3460;
                    border-radius: 6px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    transition: background 0.2s;
                }
                
                .layer-item:hover {
                    background: #1a4a7a;
                }
                
                .layer-item.active {
                    background: #2a6a9a;
                    border: 1px solid #4a8ac2;
                }
                
                .layer-thumbnail {
                    width: 40px;
                    height: 40px;
                    background: #333;
                    border-radius: 4px;
                    margin-right: 10px;
                    object-fit: cover;
                }
                
                .layer-name {
                    flex: 1;
                    font-size: 0.9em;
                }
                
                .layer-controls {
                    display: flex;
                    gap: 5px;
                }
                
                .layer-controls button {
                    background: transparent;
                    border: none;
                    color: #ccc;
                    cursor: pointer;
                    padding: 5px;
                    border-radius: 3px;
                    font-size: 0.8em;
                }
                
                .layer-controls button:hover {
                    background: rgba(255,255,255,0.1);
                    color: #fff;
                }
                
                #toolbar {
                    height: 50px;
                    background: #0f3460;
                    padding: 0 20px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    border-bottom: 1px solid #1a4a7a;
                }
                
                .tool-btn {
                    background: transparent;
                    border: none;
                    color: #ccc;
                    padding: 10px 15px;
                    cursor: pointer;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    transition: all 0.2s;
                }
                
                .tool-btn:hover {
                    background: rgba(255,255,255,0.1);
                    color: #fff;
                }
                
                .tool-btn.active {
                    background: rgba(255,255,255,0.2);
                    color: #fff;
                }
                
                #upload-btn {
                    position: relative;
                    overflow: hidden;
                }
                
                #upload-input {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    opacity: 0;
                    cursor: pointer;
                }
                
                #status-bar {
                    height: 30px;
                    background: #16213e;
                    padding: 0 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    font-size: 0.85em;
                    color: #888;
                    border-top: 1px solid #0f3460;
                }
                
                .coords {
                    color: #4a8ac2;
                }
                
                /* Context menu */
                .context-menu {
                    position: absolute;
                    background: #16213e;
                    border: 1px solid #0f3460;
                    border-radius: 6px;
                    padding: 5px 0;
                    z-index: 1000;
                    display: none;
                    min-width: 150px;
                }
                
                .context-menu.show {
                    display: block;
                }
                
                .context-menu-item {
                    padding: 8px 15px;
                    color: #ccc;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .context-menu-item:hover {
                    background: #0f3460;
                    color: #fff;
                }
                
                /* Modal */
                .modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.8);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                
                .modal.show {
                    display: flex;
                }
                
                .modal-content {
                    background: #16213e;
                    padding: 30px;
                    border-radius: 8px;
                    max-width: 500px;
                    width: 90%;
                }
                
                .modal h3 {
                    margin-bottom: 20px;
                    color: #fff;
                }
                
                .form-group {
                    margin-bottom: 15px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    color: #888;
                    font-size: 0.9em;
                }
                
                .form-group input {
                    width: 100%;
                    padding: 10px;
                    background: #0f3460;
                    border: 1px solid #1a4a7a;
                    border-radius: 4px;
                    color: #fff;
                    font-size: 1em;
                }
                
                .form-group input:focus {
                    outline: none;
                    border-color: #4a8ac2;
                }
                
                .modal-buttons {
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                    margin-top: 20px;
                }
                
                .btn {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.95em;
                    transition: all 0.2s;
                }
                
                .btn-primary {
                    background: #4a8ac2;
                    color: #fff;
                }
                
                .btn-primary:hover {
                    background: #5a9bd2;
                }
                
                .btn-secondary {
                    background: #0f3460;
                    color: #ccc;
                }
                
                .btn-secondary:hover {
                    background: #1a4a7a;
                    color: #fff;
                }
                
                /* Loading spinner */
                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid rgba(255,255,255,0.1);
                    border-top-color: #4a8ac2;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                /* Selection rectangle */
                .selection-rect {
                    position: absolute;
                    border: 2px dashed #4a8ac2;
                    background: rgba(74, 138, 194, 0.1);
                    pointer-events: none;
                    z-index: 100;
                }
                
                /* Segmented object overlay */
                .object-overlay {
                    position: absolute;
                    border: 2px solid #ff6b6b;
                    background: rgba(255, 107, 107, 0.1);
                    pointer-events: none;
                    z-index: 50;
                }
                
                /* Resize handles */
                .resize-handle {
                    position: absolute;
                    width: 10px;
                    height: 10px;
                    background: #4a8ac2;
                    border-radius: 50%;
                    cursor: nwse-resize;
                    z-index: 200;
                }
            </style>
        </head>
        <body>
            <div id="app-container">
                <div id="sidebar">
                    <div class="section-title">Layers</div>
                    <div id="layers-list"></div>
                    
                    <div class="section-title">Objects</div>
                    <div id="objects-list"></div>
                    
                    <div class="section-title">Tools</div>
                    <div id="tools-list">
                        <button class="tool-btn" onclick="setTool('select')" id="tool-select">
                            🖱️ Select
                        </button>
                        <button class="tool-btn" onclick="setTool('segment')" id="tool-segment">
                            ✂️ Segment
                        </button>
                        <button class="tool-btn" onclick="setTool('move')" id="tool-move">
                            🪃 Move
                        </button>
                        <button class="tool-btn" onclick="setTool('rotate')" id="tool-rotate">
                            🔄 Rotate
                        </button>
                        <button class="tool-btn" onclick="setTool('scale')" id="tool-scale">
                            📐 Scale
                        </button>
                    </div>
                </div>
                
                <div id="canvas-container">
                    <canvas id="main-canvas"></canvas>
                    <div id="selection-rect" class="selection-rect"></div>
                    <div id="context-menu" class="context-menu"></div>
                </div>
            </div>
            
            <div id="toolbar">
                <button class="tool-btn" id="upload-btn">
                    📁 Upload
                    <input type="file" id="upload-input" accept="image/*" multiple>
                </button>
                <button class="tool-btn" onclick="exportProject()">
                    💾 Export
                </button>
                <button class="tool-btn" onclick="clearCanvas()">
                    🗑️ Clear
                </button>
                <button class="tool-btn" onclick="undo()">
                    ⬅️ Undo
                </button>
                <button class="tool-btn" onclick="redo()">
                    ➡️ Redo
                </button>
            </div>
            
            <div id="status-bar">
                <span class="coords" id="mouse-coords">X: 0, Y: 0</span>
                <span id="status-message">Ready</span>
            </div>
            
            <div id="modal" class="modal">
                <div class="modal-content">
                    <h3 id="modal-title">Title</h3>
                    <div id="modal-body"></div>
                    <div class="modal-buttons">
                        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                        <button class="btn btn-primary" onclick="confirmModal()" id="modal-confirm">OK</button>
                    </div>
                </div>
            </div>
            
            <script>
                // Application state
                const state = {
                    canvas: null,
                    ctx: null,
                    images: [],
                    layers: [],
                    objects: [],
                    activeTool: 'select',
                    activeLayer: null,
                    activeObject: null,
                    isDragging: false,
                    dragStart: { x: 0, y: 0 },
                    selectionRect: { start: null, end: null },
                    scale: 1,
                    offset: { x: 0, y: 0 },
                    mousePos: { x: 0, y: 0 },
                    history: [],
                    historyIndex: -1,
                };
                
                // Initialize application
                function init() {
                    state.canvas = document.getElementById('main-canvas');
                    state.ctx = state.canvas.getContext('2d');
                    
                    // Set canvas size
                    resizeCanvas();
                    window.addEventListener('resize', resizeCanvas);
                    
                    // Setup event listeners
                    setupEventListeners();
                    
                    // Setup upload
                    document.getElementById('upload-input').addEventListener('change', handleUpload);
                    
                    // Load any existing project
                    loadProject();
                    
                    // Check SAM3 status
                    checkSAM3Status();
                    
                    // Start render loop
                    requestAnimationFrame(render);
                }
                
                function resizeCanvas() {
                    const container = document.getElementById('canvas-container');
                    state.canvas.width = container.clientWidth;
                    state.canvas.height = container.clientHeight;
                    render();
                }
                
                function setupEventListeners() {
                    // Mouse events
                    state.canvas.addEventListener('mousedown', onMouseDown);
                    state.canvas.addEventListener('mousemove', onMouseMove);
                    state.canvas.addEventListener('mouseup', onMouseUp);
                    state.canvas.addEventListener('mouseleave', onMouseLeave);
                    state.canvas.addEventListener('wheel', onWheel);
                    
                    // Keyboard events
                    document.addEventListener('keydown', onKeyDown);
                    
                    // Context menu
                    state.canvas.addEventListener('contextmenu', onContextMenu);
                }
                
                function onMouseDown(e) {
                    const pos = getMousePos(e);
                    state.mousePos = pos;
                    updateMouseCoords(pos);
                    
                    switch (state.activeTool) {
                        case 'select':
                            // Start selection rectangle
                            state.selectionRect.start = pos;
                            state.selectionRect.end = pos;
                            updateSelectionRect();
                            break;
                            
                        case 'segment':
                            // Send segmentation request
                            segmentAtPoint(pos);
                            break;
                            
                        case 'move':
                            // Start dragging
                            state.isDragging = true;
                            state.dragStart = pos;
                            break;
                            
                        default:
                            // Try to select object at this position
                            const obj = getObjectAtPosition(pos);
                            if (obj) {
                                state.activeObject = obj;
                                render();
                            }
                    }
                }
                
                function onMouseMove(e) {
                    const pos = getMousePos(e);
                    state.mousePos = pos;
                    updateMouseCoords(pos);
                    
                    if (state.isDragging) {
                        // Handle dragging
                        const dx = pos.x - state.dragStart.x;
                        const dy = pos.y - state.dragStart.y;
                        
                        if (state.activeObject) {
                            state.activeObject.position[0] += dx;
                            state.activeObject.position[1] += dy;
                            state.dragStart = pos;
                            render();
                        }
                    } else if (state.selectionRect.start && state.activeTool === 'select') {
                        // Update selection rectangle
                        state.selectionRect.end = pos;
                        updateSelectionRect();
                    }
                }
                
                function onMouseUp(e) {
                    const pos = getMousePos(e);
                    
                    if (state.isDragging) {
                        state.isDragging = false;
                        saveHistory();
                    }
                    
                    if (state.selectionRect.start && state.activeTool === 'select') {
                        // Complete selection
                        state.selectionRect.end = pos;
                        updateSelectionRect();
                        
                        // Check if we selected any objects
                        const selected = getObjectsInRect(state.selectionRect);
                        if (selected.length > 0) {
                            // For now, just select the first one
                            state.activeObject = selected[0];
                        }
                        
                        // Clear selection rectangle
                        state.selectionRect.start = null;
                        state.selectionRect.end = null;
                        updateSelectionRect();
                    }
                }
                
                function onMouseLeave(e) {
                    // Clear selection rectangle if we leave the canvas
                    if (state.selectionRect.start) {
                        state.selectionRect.start = null;
                        state.selectionRect.end = null;
                        updateSelectionRect();
                    }
                }
                
                function onWheel(e) {
                    e.preventDefault();
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    state.scale *= delta;
                    render();
                }
                
                function onKeyDown(e) {
                    // Handle keyboard shortcuts
                    switch (e.key) {
                        case 'Escape':
                            state.activeObject = null;
                            state.activeTool = 'select';
                            updateToolButtons();
                            render();
                            break;
                            
                        case 'Delete':
                        case 'Backspace':
                            if (state.activeObject) {
                                removeObject(state.activeObject);
                            }
                            break;
                            
                        case '1':
                            setTool('select');
                            break;
                        case '2':
                            setTool('segment');
                            break;
                        case '3':
                            setTool('move');
                            break;
                        case '4':
                            setTool('rotate');
                            break;
                        case '5':
                            setTool('scale');
                            break;
                    }
                }
                
                function onContextMenu(e) {
                    e.preventDefault();
                    const pos = getMousePos(e);
                    
                    // Check if we clicked on an object
                    const obj = getObjectAtPosition(pos);
                    if (obj) {
                        state.activeObject = obj;
                        showContextMenu(e.clientX, e.clientY, obj);
                    }
                }
                
                function getMousePos(e) {
                    const rect = state.canvas.getBoundingClientRect();
                    return {
                        x: (e.clientX - rect.left - state.offset.x) / state.scale,
                        y: (e.clientY - rect.top - state.offset.y) / state.scale
                    };
                }
                
                function updateMouseCoords(pos) {
                    document.getElementById('mouse-coords').textContent = 
                        `X: ${Math.round(pos.x)}, Y: ${Math.round(pos.y)}`;
                }
                
                function updateSelectionRect() {
                    const rectEl = document.getElementById('selection-rect');
                    if (state.selectionRect.start && state.selectionRect.end) {
                        const start = state.selectionRect.start;
                        const end = state.selectionRect.end;
                        
                        rectEl.style.left = `${Math.min(start.x, end.x) * state.scale + state.offset.x}px`;
                        rectEl.style.top = `${Math.min(start.y, end.y) * state.scale + state.offset.y}px`;
                        rectEl.style.width = `${Math.abs(end.x - start.x) * state.scale}px`;
                        rectEl.style.height = `${Math.abs(end.y - start.y) * state.scale}px`;
                        rectEl.style.display = 'block';
                    } else {
                        rectEl.style.display = 'none';
                    }
                }
                
                function setTool(tool) {
                    state.activeTool = tool;
                    updateToolButtons();
                    document.getElementById('status-message').textContent = 
                        `Tool: ${tool.charAt(0).toUpperCase() + tool.slice(1)}`;
                }
                
                function updateToolButtons() {
                    document.querySelectorAll('.tool-btn').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    document.getElementById(`tool-${state.activeTool}`).classList.add('active');
                }
                
                function segmentAtPoint(pos) {
                    // Find which image we clicked on
                    const layer = getLayerAtPosition(pos);
                    if (!layer) {
                        showStatus('No image at this position', true);
                        return;
                    }
                    
                    showStatus('Segmenting...');
                    
                    // Send request to backend
                    fetch('/api/v1/segmentation/points', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_id: layer.id,
                            points: [{ x: pos.x - layer.position[0], y: pos.y - layer.position[1] }],
                            labels: [1]
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.mask_base64) {
                            // Create new object from the mask
                            const obj = {
                                id: data.object_id || `obj_${Date.now()}`,
                                name: `Object ${state.objects.length + 1}`,
                                source_image_id: layer.id,
                                mask_base64: data.mask_base64,
                                bounding_box: data.bounding_box,
                                position: [pos.x, pos.y],
                                rotation: 0,
                                scale: [1, 1],
                                opacity: 1,
                                border_color: '#FF0000',
                                border_width: 2,
                                z_index: state.objects.length
                            };
                            
                            state.objects.push(obj);
                            state.activeObject = obj;
                            saveHistory();
                            render();
                            showStatus('Segmentation complete!');
                        } else {
                            showStatus('Segmentation failed: ' + (data.message || 'Unknown error'), true);
                        }
                    })
                    .catch(error => {
                        showStatus('Segmentation error: ' + error.message, true);
                    });
                }
                
                function getLayerAtPosition(pos) {
                    // Check layers in reverse order (top to bottom)
                    for (let i = state.layers.length - 1; i >= 0; i--) {
                        const layer = state.layers[i];
                        if (layer.visible && isPointInLayer(pos, layer)) {
                            return layer;
                        }
                    }
                    return null;
                }
                
                function isPointInLayer(pos, layer) {
                    // Simple check - point is within layer bounds
                    return pos.x >= layer.position[0] && 
                           pos.x <= layer.position[0] + layer.width &&
                           pos.y >= layer.position[1] && 
                           pos.y <= layer.position[1] + layer.height;
                }
                
                function getObjectAtPosition(pos) {
                    // Check objects in reverse order (top to bottom)
                    for (let i = state.objects.length - 1; i >= 0; i--) {
                        const obj = state.objects[i];
                        if (obj.bounding_box && isPointInBox(pos, obj)) {
                            return obj;
                        }
                    }
                    return null;
                }
                
                function isPointInBox(pos, obj) {
                    const bbox = obj.bounding_box;
                    return pos.x >= bbox.x1 && pos.x <= bbox.x2 && 
                           pos.y >= bbox.y1 && pos.y <= bbox.y2;
                }
                
                function getObjectsInRect(rect) {
                    const minX = Math.min(rect.start.x, rect.end.x);
                    const maxX = Math.max(rect.start.x, rect.end.x);
                    const minY = Math.min(rect.start.y, rect.end.y);
                    const maxY = Math.max(rect.start.y, rect.end.y);
                    
                    return state.objects.filter(obj => {
                        if (!obj.bounding_box) return false;
                        const bbox = obj.bounding_box;
                        return !(bbox.x2 < minX || bbox.x1 > maxX || 
                                 bbox.y2 < minY || bbox.y1 > maxY);
                    });
                }
                
                function removeObject(obj) {
                    const index = state.objects.indexOf(obj);
                    if (index > -1) {
                        state.objects.splice(index, 1);
                        if (state.activeObject === obj) {
                            state.activeObject = null;
                        }
                        saveHistory();
                        render();
                    }
                }
                
                function showContextMenu(x, y, obj) {
                    const menu = document.getElementById('context-menu');
                    menu.innerHTML = `
                        <div class="context-menu-item" onclick="bringToFront('${obj.id}')">Bring to Front</div>
                        <div class="context-menu-item" onclick="sendToBack('${obj.id}')">Send to Back</div>
                        <div class="context-menu-item" onclick="deleteObject('${obj.id}')">Delete</div>
                        <div class="context-menu-item" onclick="copyObject('${obj.id}')">Copy</div>
                    `;
                    menu.style.left = `${x}px`;
                    menu.style.top = `${y}px`;
                    menu.classList.add('show');
                }
                
                function hideContextMenu() {
                    document.getElementById('context-menu').classList.remove('show');
                }
                
                function bringToFront(objId) {
                    const obj = state.objects.find(o => o.id === objId);
                    if (obj) {
                        const maxZ = Math.max(...state.objects.map(o => o.z_index), 0);
                        obj.z_index = maxZ + 1;
                        state.objects.sort((a, b) => a.z_index - b.z_index);
                        render();
                        saveHistory();
                    }
                    hideContextMenu();
                }
                
                function sendToBack(objId) {
                    const obj = state.objects.find(o => o.id === objId);
                    if (obj) {
                        const minZ = Math.min(...state.objects.map(o => o.z_index), 0);
                        obj.z_index = minZ - 1;
                        state.objects.sort((a, b) => a.z_index - b.z_index);
                        render();
                        saveHistory();
                    }
                    hideContextMenu();
                }
                
                function deleteObject(objId) {
                    const obj = state.objects.find(o => o.id === objId);
                    if (obj) {
                        removeObject(obj);
                    }
                    hideContextMenu();
                }
                
                function copyObject(objId) {
                    const obj = state.objects.find(o => o.id === objId);
                    if (obj) {
                        const copy = JSON.parse(JSON.stringify(obj));
                        copy.id = `copy_${obj.id}_${Date.now()}`;
                        copy.position = [obj.position[0] + 20, obj.position[1] + 20];
                        copy.z_index = Math.max(...state.objects.map(o => o.z_index), 0) + 1;
                        state.objects.push(copy);
                        state.activeObject = copy;
                        saveHistory();
                        render();
                    }
                    hideContextMenu();
                }
                
                function handleUpload(e) {
                    const files = e.target.files;
                    if (!files || files.length === 0) return;
                    
                    showStatus(`Uploading ${files.length} file(s)...`);
                    
                    for (let i = 0; i < files.length; i++) {
                        uploadFile(files[i]);
                    }
                    
                    // Reset input
                    e.target.value = '';
                }
                
                function uploadFile(file) {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    fetch('/api/v1/images/upload', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Create layer from uploaded image
                            const layer = {
                                id: data.image_id,
                                name: file.name,
                                image_path: data.image_path,
                                image_base64: data.thumbnail_base64,
                                width: data.width,
                                height: data.height,
                                original_width: data.width,
                                original_height: data.height,
                                position: [100 + state.layers.length * 50, 100 + state.layers.length * 50],
                                rotation: 0,
                                scale: [1, 1],
                                opacity: 1,
                                visible: true,
                                z_index: state.layers.length
                            };
                            
                            state.layers.push(layer);
                            updateLayersList();
                            saveHistory();
                            render();
                            showStatus(`Image uploaded: ${file.name}`);
                            
                            // Pre-compute embeddings
                            computeEmbeddings(data.image_id);
                        } else {
                            showStatus(`Upload failed: ${data.message || 'Unknown error'}`, true);
                        }
                    })
                    .catch(error => {
                        showStatus(`Upload error: ${error.message}`, true);
                    });
                }
                
                function computeEmbeddings(imageId) {
                    fetch(`/api/v1/images/${imageId}/compute-embeddings`, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showStatus(`Embeddings computed for image: ${imageId}`);
                        }
                    })
                    .catch(error => {
                        console.error('Failed to compute embeddings:', error);
                    });
                }
                
                function updateLayersList() {
                    const listEl = document.getElementById('layers-list');
                    listEl.innerHTML = state.layers.map(layer => `
                        <div class="layer-item ${state.activeLayer === layer ? 'active' : ''}" 
                             onclick="selectLayer('${layer.id}')">
                            <img src="${layer.image_base64 || '/static/placeholder.png'}" 
                                 class="layer-thumbnail" alt="${layer.name}">
                            <span class="layer-name">${layer.name}</span>
                            <div class="layer-controls">
                                <button onclick="toggleLayerVisibility('${layer.id}')">
                                    ${layer.visible ? '👁️' : '👁️‍🗨'}
                                </button>
                                <button onclick="deleteLayer('${layer.id}')">🗑️</button>
                            </div>
                        </div>
                    `).join('');
                }
                
                function selectLayer(layerId) {
                    state.activeLayer = state.layers.find(l => l.id === layerId);
                    updateLayersList();
                    render();
                }
                
                function toggleLayerVisibility(layerId) {
                    const layer = state.layers.find(l => l.id === layerId);
                    if (layer) {
                        layer.visible = !layer.visible;
                        updateLayersList();
                        render();
                    }
                }
                
                function deleteLayer(layerId) {
                    const index = state.layers.findIndex(l => l.id === layerId);
                    if (index > -1) {
                        state.layers.splice(index, 1);
                        if (state.activeLayer && state.activeLayer.id === layerId) {
                            state.activeLayer = null;
                        }
                        updateLayersList();
                        saveHistory();
                        render();
                    }
                }
                
                function render() {
                    // Clear canvas
                    state.ctx.fillStyle = '#1a1a2e';
                    state.ctx.fillRect(0, 0, state.canvas.width, state.canvas.height);
                    
                    // Apply scale and offset
                    state.ctx.save();
                    state.ctx.scale(state.scale, state.scale);
                    state.ctx.translate(state.offset.x / state.scale, state.offset.y / state.scale);
                    
                    // Draw layers
                    for (const layer of state.layers) {
                        if (!layer.visible) continue;
                        drawLayer(layer);
                    }
                    
                    // Draw objects
                    for (const obj of state.objects) {
                        drawObject(obj);
                    }
                    
                    // Draw active object highlight
                    if (state.activeObject) {
                        drawObjectHighlight(state.activeObject);
                    }
                    
                    state.ctx.restore();
                }
                
                function drawLayer(layer) {
                    // For now, just draw a placeholder
                    state.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                    state.ctx.fillRect(
                        layer.position[0], 
                        layer.position[1], 
                        layer.width, 
                        layer.height
                    );
                    
                    // Draw border
                    state.ctx.strokeStyle = '#4a8ac2';
                    state.ctx.lineWidth = 2;
                    state.ctx.strokeRect(
                        layer.position[0], 
                        layer.position[1], 
                        layer.width, 
                        layer.height
                    );
                    
                    // Draw layer name
                    state.ctx.fillStyle = '#4a8ac2';
                    state.ctx.font = '12px Arial';
                    state.ctx.fillText(layer.name, layer.position[0] + 5, layer.position[1] + 15);
                }
                
                function drawObject(obj) {
                    if (!obj.mask_base64) return;
                    
                    // For now, draw the bounding box
                    if (obj.bounding_box) {
                        const bbox = obj.bounding_box;
                        
                        // Apply object transformations
                        state.ctx.save();
                        state.ctx.translate(obj.position[0], obj.position[1]);
                        state.ctx.rotate(obj.rotation * Math.PI / 180);
                        state.ctx.scale(obj.scale[0], obj.scale[1]);
                        
                        // Draw mask overlay
                        state.ctx.fillStyle = 'rgba(255, 107, 107, 0.3)';
                        state.ctx.fillRect(
                            bbox.x1, bbox.y1, 
                            bbox.x2 - bbox.x1, 
                            bbox.y2 - bbox.y1
                        );
                        
                        // Draw border
                        state.ctx.strokeStyle = obj.border_color || '#FF0000';
                        state.ctx.lineWidth = obj.border_width || 2;
                        state.ctx.strokeRect(
                            bbox.x1, bbox.y1, 
                            bbox.x2 - bbox.x1, 
                            bbox.y2 - bbox.y1
                        );
                        
                        state.ctx.restore();
                    }
                }
                
                function drawObjectHighlight(obj) {
                    if (!obj.bounding_box) return;
                    
                    const bbox = obj.bounding_box;
                    
                    state.ctx.save();
                    state.ctx.translate(obj.position[0], obj.position[1]);
                    state.ctx.rotate(obj.rotation * Math.PI / 180);
                    state.ctx.scale(obj.scale[0], obj.scale[1]);
                    
                    // Draw highlight
                    state.ctx.strokeStyle = '#ffff00';
                    state.ctx.lineWidth = 3;
                    state.ctx.setLineDash([5, 5]);
                    state.ctx.strokeRect(
                        bbox.x1 - 5, bbox.y1 - 5, 
                        bbox.x2 - bbox.x1 + 10, 
                        bbox.y2 - bbox.y1 + 10
                    );
                    state.ctx.setLineDash([]);
                    
                    state.ctx.restore();
                }
                
                function saveHistory() {
                    // Save current state to history
                    const currentState = {
                        layers: JSON.parse(JSON.stringify(state.layers)),
                        objects: JSON.parse(JSON.stringify(state.objects))
                    };
                    
                    // If we're not at the end of history, truncate
                    if (state.historyIndex < state.history.length - 1) {
                        state.history = state.history.slice(0, state.historyIndex + 1);
                    }
                    
                    state.history.push(currentState);
                    state.historyIndex = state.history.length - 1;
                    
                    // Limit history size
                    if (state.history.length > 50) {
                        state.history.shift();
                        state.historyIndex--;
                    }
                }
                
                function undo() {
                    if (state.historyIndex > 0) {
                        state.historyIndex--;
                        const prevState = state.history[state.historyIndex];
                        state.layers = JSON.parse(JSON.stringify(prevState.layers));
                        state.objects = JSON.parse(JSON.stringify(prevState.objects));
                        state.activeObject = null;
                        updateLayersList();
                        render();
                    }
                }
                
                function redo() {
                    if (state.historyIndex < state.history.length - 1) {
                        state.historyIndex++;
                        const nextState = state.history[state.historyIndex];
                        state.layers = JSON.parse(JSON.stringify(nextState.layers));
                        state.objects = JSON.parse(JSON.stringify(nextState.objects));
                        state.activeObject = null;
                        updateLayersList();
                        render();
                    }
                }
                
                function clearCanvas() {
                    if (confirm('Are you sure you want to clear the canvas?')) {
                        state.layers = [];
                        state.objects = [];
                        state.activeLayer = null;
                        state.activeObject = null;
                        state.history = [];
                        state.historyIndex = -1;
                        updateLayersList();
                        render();
                        showStatus('Canvas cleared');
                    }
                }
                
                function exportProject() {
                    showStatus('Exporting...');
                    
                    // Send request to export
                    fetch('/api/v1/project/export/default', {
                        method: 'GET'
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.blob();
                        }
                        throw new Error('Export failed');
                    })
                    .then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `imageslime_export_${Date.now()}.png`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        showStatus('Export complete!');
                    })
                    .catch(error => {
                        showStatus(`Export error: ${error.message}`, true);
                    });
                }
                
                function checkSAM3Status() {
                    fetch('/api/v1/segmentation/model-info')
                        .then(response => response.json())
                        .then(data => {
                            if (data.model_info && data.model_info.available) {
                                showStatus('SAM3 model ready!');
                            } else {
                                showStatus('SAM3 model not available', true);
                            }
                        })
                        .catch(error => {
                            showStatus('Failed to check SAM3 status', true);
                        });
                }
                
                function showStatus(message, isError = false) {
                    const statusEl = document.getElementById('status-message');
                    statusEl.textContent = message;
                    statusEl.style.color = isError ? '#ff6b6b' : '#4a8ac2';
                }
                
                function loadProject() {
                    // Try to load the last saved project
                    fetch('/api/v1/project/list')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.projects && data.projects.length > 0) {
                                // Load the most recent project
                                const latest = data.projects.reduce((a, b) => 
                                    new Date(a.updated_at) > new Date(b.updated_at) ? a : b);
                                
                                return fetch(`/api/v1/project/load?filepath=${encodeURIComponent(latest.filepath)}`);
                            }
                            return Promise.resolve({});
                        })
                        .then(response => {
                            if (response && response.ok) {
                                return response.json();
                            }
                            return {};
                        })
                        .then(data => {
                            if (data.success && data.project) {
                                // Load project data
                                state.layers = data.project.image_layers || [];
                                state.objects = data.project.segmented_objects || [];
                                updateLayersList();
                                render();
                                showStatus(`Project loaded: ${data.project.name}`);
                            }
                        })
                        .catch(error => {
                            console.error('Failed to load project:', error);
                        });
                }
                
                function saveProject() {
                    const projectData = {
                        name: `Project ${Date.now()}`,
                        canvas_width: state.canvas.width,
                        canvas_height: state.canvas.height,
                        image_layers: state.layers,
                        segmented_objects: state.objects
                    };
                    
                    fetch('/api/v1/project/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ project_data: projectData })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showStatus('Project saved!');
                        } else {
                            showStatus('Failed to save project', true);
                        }
                    })
                    .catch(error => {
                        showStatus(`Save error: ${error.message}`, true);
                    });
                }
                
                // Modal functions
                function showModal(title, content, confirmText = 'OK') {
                    document.getElementById('modal-title').textContent = title;
                    document.getElementById('modal-body').innerHTML = content;
                    document.getElementById('modal-confirm').textContent = confirmText;
                    document.getElementById('modal').classList.add('show');
                }
                
                function closeModal() {
                    document.getElementById('modal').classList.remove('show');
                }
                
                function confirmModal() {
                    // To be implemented based on context
                    closeModal();
                }
                
                // Initialize when DOM is loaded
                document.addEventListener('DOMContentLoaded', init);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    return app


def get_app() -> FastAPI:
    """Get or create the global application instance."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


# Export app for uvicorn to import
app = get_app()


# For running with uvicorn directly
if __name__ == "__main__":
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=settings.DEBUG,
    )
