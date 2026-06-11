#!/usr/bin/env python3
"""
ImageSlime - Main entry point

Run this file to start the ImageSlime server.

Usage:
    uv run python main.py
    # or
    uvicorn imageslime.main:app --reload
"""

import sys
import os

# Add the imageslime package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from imageslime.main import get_app
import uvicorn

if __name__ == "__main__":
    app = get_app()
    
    # Get settings
    from imageslime.config import get_settings
    settings = get_settings()
    
    print("=" * 60)
    print("🎨 ImageSlime - Interactive Image Segmentation & Editing")
    print("=" * 60)
    print(f"📍 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"🔗 API Docs: http://{settings.HOST}:{settings.PORT}/api/docs")
    print(f"🚀 App: http://{settings.HOST}:{settings.PORT}/app")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")
    
    # Use the import string format for proper reload support
    uvicorn.run(
        "imageslime.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=settings.DEBUG,
    )
