#!/usr/bin/env python3
"""
Test script to verify uvicorn can properly import and run the app.
"""

import sys
import os

# Add the imageslime package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_uvicorn_import():
    """Test that uvicorn can import the app using the string format."""
    print("Testing uvicorn import string...")
    
    try:
        # This is what uvicorn does internally when you pass "imageslime.main:app"
        module_path, app_name = "imageslime.main:app".split(":")
        
        # Import the module
        import importlib
        module = importlib.import_module(module_path)
        
        # Get the app
        app = getattr(module, app_name)
        
        print(f"✓ Successfully imported: {module_path}.{app_name}")
        print(f"✓ App type: {type(app)}")
        print(f"✓ App title: {app.title}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except AttributeError as e:
        print(f"✗ App attribute not found: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_direct_import():
    """Test direct import of the app."""
    print("\nTesting direct import...")
    
    try:
        from imageslime.main import app
        print(f"✓ Successfully imported app directly")
        print(f"✓ App type: {type(app)}")
        print(f"✓ App title: {app.title}")
        return True
    except Exception as e:
        print(f"✗ Direct import failed: {e}")
        return False


def test_get_app():
    """Test the get_app function."""
    print("\nTesting get_app function...")
    
    try:
        from imageslime.main import get_app
        app = get_app()
        print(f"✓ get_app() successful")
        print(f"✓ App type: {type(app)}")
        print(f"✓ App title: {app.title}")
        return True
    except Exception as e:
        print(f"✗ get_app() failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Uvicorn Import Tests")
    print("=" * 60)
    
    tests = [
        test_uvicorn_import,
        test_direct_import,
        test_get_app,
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
        print("\n✓ All uvicorn import tests passed! 🎉")
        print("\nYou can now run:")
        print("  uv run uvicorn imageslime.main:app --reload")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
