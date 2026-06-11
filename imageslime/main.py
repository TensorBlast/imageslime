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
    
    # Root endpoint - redirect to /app
    @app.get("/")
    async def root():
        """Root endpoint - redirect to the app."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app", status_code=302)
        return HTMLResponse(content=html_content)
    
    # App endpoint that serves the main application
    @app.get("/app", response_class=HTMLResponse)
    async def app_page():
        """Serve the main application page."""
        # Serve the static HTML file
        try:
            with open("imageslime/static/app.html", "r") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except FileNotFoundError:
            # Fallback to embedded HTML if file not found
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>ImageSlime - Loading...</title></head>
            <body>
                <h1>ImageSlime</h1>
                <p>Loading application... <a href="/">Go to home page</a></p>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}
    
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
        "imageslime.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=settings.DEBUG,
    )
