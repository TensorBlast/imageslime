#!/usr/bin/env python3
"""
Setup script for ImageSlime.

This script helps with initial setup, including:
- Creating necessary directories
- Checking dependencies
- Downloading required models (if available)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(text: str):
    """Print a step with a checkmark."""
    print(f"  ✓ {text}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"  ⚠ {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"  ✗ {text}")


def check_python_version() -> bool:
    """Check if Python version is sufficient."""
    print_step("Checking Python version...")
    
    required_version = (3, 10)
    current_version = sys.version_info
    
    if current_version >= required_version:
        print_step(f"Python {current_version.major}.{current_version.minor}.{current_version.micro} detected")
        return True
    else:
        print_error(f"Python {required_version[0]}.{required_version[1]}+ required")
        print_error(f"Current version: {current_version.major}.{current_version.minor}.{current_version.micro}")
        return False


def create_directories() -> bool:
    """Create necessary directories."""
    print_step("Creating directories...")
    
    directories = ["uploads", "temp"]
    success = True
    
    for dir_name in directories:
        try:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
            print_step(f"Created directory: {dir_name}")
        except Exception as e:
            print_error(f"Failed to create directory {dir_name}: {e}")
            success = False
    
    return success


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print_step("Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "opencv-python-headless",
        "Pillow",
        "numpy",
        "ultralytics",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_step(f"Found: {package}")
        except ImportError:
            missing_packages.append(package)
            print_warning(f"Missing: {package}")
    
    if missing_packages:
        print_warning(f"\nMissing {len(missing_packages)} package(s): {', '.join(missing_packages)}")
        print_warning("Run: pip install -e .")
        return False
    
    return True


def check_sam3_model() -> bool:
    """Check if SAM3 model is available."""
    print_step("Checking SAM3 model...")
    
    model_paths = [
        "sam3.pt",
        "./sam3.pt",
        "models/sam3.pt",
        "/usr/local/share/sam3.pt",
    ]
    
    for path in model_paths:
        if Path(path).exists():
            print_step(f"Found SAM3 model: {path}")
            return True
    
    print_warning("SAM3 model (sam3.pt) not found in common locations")
    print_warning("\nTo use SAM3:")
    print_warning("1. Request access at: https://huggingface.co/facebook/sam3")
    print_warning("2. Download sam3.pt from the model page")
    print_warning("3. Place it in your project directory")
    print_warning("4. Or set SAM3_MODEL_PATH in .env file")
    
    return False


def check_cuda() -> bool:
    """Check if CUDA is available."""
    print_step("Checking CUDA availability...")
    
    try:
        import torch
        if torch.cuda.is_available():
            print_step(f"CUDA available: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print_warning("CUDA not available, will use CPU (slower)")
            return False
    except ImportError:
        print_warning("PyTorch not installed, CUDA check skipped")
        return False


def install_dependencies() -> bool:
    """Install required dependencies."""
    print_step("Installing dependencies...")
    
    try:
        # Install the package in development mode
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_step("Dependencies installed successfully")
            return True
        else:
            print_error("Failed to install dependencies")
            print(result.stderr)
            return False
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        return False


def create_env_file() -> bool:
    """Create a sample .env file."""
    print_step("Creating .env file...")
    
    env_content = """# ImageSlime Configuration
# ======================

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# SAM3 model settings
SAM3_MODEL_PATH=sam3.pt
SAM3_DEVICE=cuda
SAM3_HALF_PRECISION=True

# Storage settings
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# Performance settings
MAX_IMAGE_SIZE=4096
MAX_UPLOAD_SIZE=10485760  # 10MB
EMBEDDING_CACHE_SIZE=10
SEGMENTATION_CONFIDENCE=0.25

# WebSocket settings
SOCKETIO_CORS_ALLOW_ALL=True
"""
    
    try:
        with open(".env.example", "w") as f:
            f.write(env_content)
        print_step("Created .env.example file")
        print_warning("Copy .env.example to .env and customize as needed")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def main():
    """Main setup function."""
    print_header("ImageSlime Setup")
    
    # Check Python version
    if not check_python_version():
        print_error("\nPlease install Python 3.10 or higher")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check dependencies
    has_dependencies = check_dependencies()
    
    # Check CUDA
    check_cuda()
    
    # Check SAM3 model
    check_sam3_model()
    
    # Create .env file
    create_env_file()
    
    # Summary
    print_header("Setup Summary")
    
    if has_dependencies:
        print_step("All dependencies are installed")
    else:
        print_warning("Some dependencies are missing")
        print_warning("Run 'uv sync' or 'pip install -e .' to install them")
    
    print_step("\nNext steps:")
    print_step("1. Download SAM3 model (sam3.pt) from Hugging Face")
    print_step("2. Place sam3.pt in your project directory")
    print_step("3. Run: uv run python main.py")
    print_step("4. Open: http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("Setup complete! 🎉")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
