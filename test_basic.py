#!/usr/bin/env python3
"""
Basic tests for ImageSlime.

Run with: python test_basic.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the imageslime package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from imageslime import __version__, Settings
        from imageslime.models import (
            ImageLayer, SegmentedObject, ProjectState,
            Point, BoundingBox, LayerType, ObjectStatus
        )
        from imageslime.config import get_settings
        from imageslime.services.segmentation import SAM3SegmentationService, get_segmentation_service
        from imageslime.main import create_app, get_app
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_settings():
    """Test that settings can be loaded."""
    print("\nTesting settings...")
    
    try:
        from imageslime.config import get_settings, Settings
        
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.DEBUG is True
        
        print("✓ Settings loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("\nTesting data models...")
    
    try:
        from imageslime.models import (
            ImageLayer, SegmentedObject, ProjectState,
            Point, BoundingBox, LayerType, ObjectStatus
        )
        
        # Test Point
        point = Point(x=100, y=200)
        assert point.x == 100
        assert point.y == 200
        assert point.to_tuple() == (100, 200)
        
        # Test BoundingBox
        bbox = BoundingBox(x1=10, y1=20, x2=100, y2=200)
        assert bbox.width() == 90
        assert bbox.height() == 180
        assert bbox.to_list() == [10, 20, 100, 200]
        
        # Test ImageLayer
        layer = ImageLayer(
            name="Test Layer",
            width=800,
            height=600,
            position=(100, 100),
            z_index=0
        )
        assert layer.name == "Test Layer"
        assert layer.width == 800
        layer_dict = layer.to_dict()
        assert "name" in layer_dict
        assert "width" in layer_dict
        
        # Test SegmentedObject
        obj = SegmentedObject(
            name="Test Object",
            source_image_path="/path/to/image.jpg",
            position=(50, 50),
            rotation=45.0,
            z_index=1
        )
        assert obj.name == "Test Object"
        assert obj.rotation == 45.0
        obj_dict = obj.to_dict()
        assert "name" in obj_dict
        assert "position" in obj_dict
        
        # Test ProjectState
        project = ProjectState(
            name="Test Project",
            canvas_width=1920,
            canvas_height=1080
        )
        assert project.name == "Test Project"
        assert project.canvas_width == 1920
        
        # Test adding layers and objects
        project.add_layer(layer)
        project.add_object(obj)
        assert len(project.image_layers) == 1
        assert len(project.segmented_objects) == 1
        
        print("✓ All model tests passed")
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_creation():
    """Test that the FastAPI app can be created."""
    print("\nTesting app creation...")
    
    try:
        from imageslime.main import create_app
        from fastapi import FastAPI
        
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "ImageSlime API"
        
        print("✓ App creation successful")
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_segmentation_service():
    """Test the segmentation service initialization."""
    print("\nTesting segmentation service...")
    
    try:
        from imageslime.services.segmentation import SAM3SegmentationService, get_segmentation_service
        
        # Test service creation
        service = SAM3SegmentationService()
        assert service is not None
        
        # Test global service
        global_service = get_segmentation_service()
        assert global_service is not None
        
        # Check if model is available (it might not be if sam3.pt is missing)
        model_info = service.get_model_info()
        print(f"  Model available: {model_info.get('available', False)}")
        
        print("✓ Segmentation service initialized")
        return True
    except Exception as e:
        print(f"✗ Segmentation service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Test that the file structure is correct."""
    print("\nTesting file structure...")
    
    required_files = [
        "imageslime/__init__.py",
        "imageslime/config.py",
        "imageslime/models.py",
        "imageslime/main.py",
        "imageslime/api/__init__.py",
        "imageslime/api/images.py",
        "imageslime/api/segmentation.py",
        "imageslime/api/layers.py",
        "imageslime/api/project.py",
        "imageslime/services/__init__.py",
        "imageslime/services/segmentation.py",
        "imageslime/static/style.css",
        "main.py",
        "pyproject.toml",
        "README.md",
        "requirements.txt",
        "setup.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✓ All required files present")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("ImageSlime - Basic Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_settings,
        test_models,
        test_app_creation,
        test_segmentation_service,
        test_file_structure,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! 🎉")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
