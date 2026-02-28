"""
Integration tests for pyb - tests actual rendering with Docker.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.mark.integration
@pytest.mark.docker
class TestDockerIntegration:
    """Integration tests using Docker."""
    
    def test_simple_sphere_render(self, skip_if_no_docker):
        """Test rendering a simple sphere scene with Docker."""
        from pyb import pyb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scene = pyb(default_light=False)
            scene.sph(c=[0, 0, 0], r=1.0, name="sphere", color="#FF5733")
            scene.sun(strength=1.0)
            
            output_file = os.path.join(tmpdir, "test_sphere.png")
            
            # This should use Docker if Blender not installed
            scene.run(
                filename=output_file,
                camera_location=[4, -4, 3],
                c=[0, 0, 0],
                samples=10,  # Low samples for speed
                res=[640, 480],
                block=True
            )
            
            # Check if output file was created
            assert os.path.exists(output_file), "Rendered image not created"
            assert os.path.getsize(output_file) > 0, "Rendered image is empty"
    
    def test_boolean_operation_render(self, skip_if_no_docker):
        """Test rendering with boolean operations."""
        from pyb import pyb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scene = pyb(default_light=False)
            scene.sph(c=[0, 0, 0], r=1.0, name="sphere1", color="#3498DB")
            scene.sph(c=[0.5, 0, 0], r=1.0, name="sphere2", color="#E74C3C")
            scene.subtract("sphere1", "sphere2")
            scene.sun(strength=1.0)
            
            output_file = os.path.join(tmpdir, "test_boolean.png")
            
            scene.run(
                filename=output_file,
                camera_location=[4, -4, 3],
                c=[0, 0, 0],
                samples=10,
                res=[640, 480],
                block=True
            )
            
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0
    
    def test_multiple_primitives_render(self, skip_if_no_docker):
        """Test rendering multiple primitives."""
        from pyb import pyb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scene = pyb(default_light=False)
            
            # Add various primitives
            scene.sph(c=[0, 0, 0], r=0.5, name="sphere", color="#FF0000")
            scene.rpp(x1=-1, x2=-0.5, y1=-0.5, y2=0.5, z1=-0.5, z2=0.5, 
                     name="cube", color="#00FF00")
            scene.rcc(c=[1, 0, 0], r=0.3, h=1.0, name="cylinder", 
                     direction='z', color="#0000FF")
            
            scene.point(location=[5, 5, 5], strength=1000.0)
            
            output_file = os.path.join(tmpdir, "test_multi.png")
            
            scene.run(
                filename=output_file,
                camera_location=[4, -4, 3],
                c=[0, 0, 0],
                samples=10,
                res=[640, 480],
                block=True
            )
            
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0


@pytest.mark.integration
class TestScriptGeneration:
    """Test script generation without actual rendering."""
    
    def test_script_contains_imports(self):
        """Test that generated script has required imports."""
        from pyb import pyb
        
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="sphere")
        
        script = str(scene)
        
        assert "import bpy" in script
        assert "scene = bpy.context.scene" in script
    
    def test_script_contains_geometry(self):
        """Test that script contains geometry commands."""
        from pyb import pyb
        
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="test_sphere")
        scene.rpp(x1=-1, x2=1, y1=-1, y2=1, z1=0, z2=2, name="test_box")
        
        script = str(scene)
        
        assert "primitive_ico_sphere_add" in script
        assert "primitive_cube_add" in script
        assert "test_sphere" in script
        assert "test_box" in script
    
    def test_script_contains_materials(self):
        """Test that script contains material definitions."""
        from pyb import pyb
        
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="sphere", color="#FF0000")
        
        script = str(scene)
        
        assert "material" in script.lower()
        assert "diffuse_color" in script or "base_color" in script.lower()
    
    def test_script_contains_camera_setup(self):
        """Test that script contains camera setup."""
        from pyb import pyb
        
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="sphere")
        scene.look_at(target=[0, 0, 0])
        
        script = str(scene)
        
        assert "camera" in script.lower()
    
    def test_script_contains_render_settings(self):
        """Test that render method adds render settings."""
        from pyb import pyb
        
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="sphere")
        scene.render(
            camera_location=[4, -4, 3],
            c=[0, 0, 0],
            samples=128,
            res=[1920, 1080]
        )
        
        script = str(scene)
        
        assert "render" in script.lower()
        assert "cycles" in script.lower() or "samples" in script.lower()


@pytest.mark.integration
class TestBlenderDetection:
    """Test Blender detection in real environment."""
    
    def test_blender_executor_available(self):
        """Test that BlenderExecutor can be initialized."""
        from pyb.blender_detection import get_blender_executor
        
        executor = get_blender_executor()
        status = executor.get_status()
        
        assert status["available"] is True
        assert status["blender_path"] is not None or status["use_docker"] is True
    
    def test_check_blender_available(self):
        """Test check_blender_available function."""
        from pyb import check_blender_available
        
        # Should return True since we have Docker
        assert check_blender_available() is True


@pytest.mark.integration
class TestFileOperations:
    """Test file I/O operations."""
    
    def test_script_write_to_file(self):
        """Test writing script to file."""
        from pyb import pyb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scene = pyb(default_light=False)
            scene.sph(c=[0, 0, 0], r=1.0, name="sphere")
            
            script_file = os.path.join(tmpdir, "test_script.py")
            
            with open(script_file, "w") as f:
                f.write(str(scene))
            
            assert os.path.exists(script_file)
            
            # Read back and verify
            with open(script_file, "r") as f:
                content = f.read()
            
            assert "import bpy" in content
            assert "sphere" in content
    
    def test_output_directory_creation(self):
        """Test that output directories are created."""
        from pyb import pyb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "renders", "test")
            os.makedirs(output_dir, exist_ok=True)
            
            assert os.path.exists(output_dir)
            assert os.path.isdir(output_dir)
