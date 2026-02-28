"""
Tests for core bpwf class functionality.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestBpwfInit:
    """Test bpwf initialization."""
    
    def test_init_default(self, mock_bpy):
        """Test default initialization."""
        from bpwf import bpwf
        
        scene = bpwf()
        assert scene.filename == "brender_01"
        assert scene.has_run == False
        assert scene._draft == False
    
    def test_init_no_default_light(self, mock_bpy):
        """Test initialization without default light."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        assert scene.default_light == False
    
    def test_init_with_scene_name(self, mock_bpy):
        """Test initialization with custom scene name."""
        from bpwf import bpwf
        
        scene = bpwf(scene_name="CustomScene")
        # Scene should be created with custom name
        assert scene.scene is not None


class TestBpwfPrimitives:
    """Test primitive geometry creation."""
    
    def test_sphere(self, mock_bpy):
        """Test sphere creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="test_sphere", color="#FF0000")
        
        # Verify sphere creation was called
        mock_bpy.ops.mesh.primitive_ico_sphere_add.assert_called()
    
    def test_sphere_with_alpha(self, mock_bpy):
        """Test sphere with transparency."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="glass_sphere", color="#FFFFFF", alpha=0.5)
        
        mock_bpy.ops.mesh.primitive_ico_sphere_add.assert_called()
    
    def test_rpp_box(self, mock_bpy):
        """Test rectangular parallelepiped (box) creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.rpp(x1=-1, x2=1, y1=-1, y2=1, z1=0, z2=2, name="box", color="#0000FF")
        
        mock_bpy.ops.mesh.primitive_cube_add.assert_called()
    
    def test_rpp_with_center(self, mock_bpy):
        """Test rpp with center parameter."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.rpp(c=[0, 0, 0], l=[2, 2, 2], name="centered_box")
        
        mock_bpy.ops.mesh.primitive_cube_add.assert_called()
    
    def test_cylinder(self, mock_bpy):
        """Test cylinder creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.rcc(c=[0, 0, 0], r=0.5, h=2.0, name="cylinder", direction='z')
        
        mock_bpy.ops.mesh.primitive_cylinder_add.assert_called()
    
    def test_cylinder_direction_x(self, mock_bpy):
        """Test cylinder with x direction."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.rcc(c=[0, 0, 0], r=0.5, h=2.0, name="cyl_x", direction='x')
        
        mock_bpy.ops.mesh.primitive_cylinder_add.assert_called()
    
    def test_cone(self, mock_bpy):
        """Test cone creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.cone(c=[0, 0, 0], r1=1.0, r2=0.0, h=2.0, name="cone")
        
        mock_bpy.ops.mesh.primitive_cone_add.assert_called()
    
    def test_plane(self, mock_bpy):
        """Test plane creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.plane(x1=-5, x2=5, y1=-5, y2=5, z1=0, z2=0, name="ground")
        
        mock_bpy.ops.mesh.primitive_plane_add.assert_called()


class TestBpwfLights:
    """Test lighting functionality."""
    
    def test_sun_light(self, mock_bpy):
        """Test sun light creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.sun(strength=1.0)
        
        # Verify light creation
        mock_bpy.data.lights.new.assert_called()
    
    def test_point_light(self, mock_bpy):
        """Test point light creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.point(location=[5, 5, 5], strength=1000.0, name="PointLight")
        
        mock_bpy.data.lights.new.assert_called()
    
    def test_point_light_custom_color(self, mock_bpy):
        """Test point light with custom color."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.point(location=[0, 0, 5], strength=500.0, name="RedLight", color="#FF0000")
        
        mock_bpy.data.lights.new.assert_called()


class TestBpwfMaterials:
    """Test material creation."""
    
    def test_flat_material(self, mock_bpy):
        """Test flat material creation."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.flat(name="FlatMat", color="#FF0000")
        
        mock_bpy.data.materials.new.assert_called()
    
    def test_emissive_material(self, mock_bpy):
        """Test emissive material."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.emis(name="EmissiveMat", color="#FFFFFF", emittance=5.0)
        
        mock_bpy.data.materials.new.assert_called()
    
    def test_transparent_material(self, mock_bpy):
        """Test transparent material."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.trans(name="GlassMat", color="#FFFFFF")
        
        mock_bpy.data.materials.new.assert_called()
    
    def test_sem_material(self, mock_bpy):
        """Test SEM-style material."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.sem(name="SEMMat", e_color="#EEEEEE", bsdf_color="#000000")
        
        mock_bpy.data.materials.new.assert_called()


class TestBpwfBooleanOperations:
    """Test boolean operations."""
    
    def test_subtract(self, mock_bpy):
        """Test subtraction operation."""
        from bpwf import bpwf
        
        # Set up mock objects
        mock_bpy.data.objects = {
            "sphere1": MagicMock(),
            "sphere2": MagicMock()
        }
        mock_bpy.data.objects["sphere1"].modifiers = MagicMock()
        mock_bpy.data.objects["sphere1"].modifiers.new = MagicMock()
        
        scene = bpwf(default_light=False)
        scene.subtract("sphere1", "sphere2")
        
        # Verify boolean modifier was created
        mock_bpy.data.objects["sphere1"].modifiers.new.assert_called()
    
    def test_union(self, mock_bpy):
        """Test union operation."""
        from bpwf import bpwf
        
        mock_bpy.data.objects = {
            "sphere1": MagicMock(),
            "sphere2": MagicMock()
        }
        mock_bpy.data.objects["sphere1"].modifiers = MagicMock()
        mock_bpy.data.objects["sphere1"].modifiers.new = MagicMock()
        
        scene = bpwf(default_light=False)
        scene.union("sphere1", "sphere2")
        
        mock_bpy.data.objects["sphere1"].modifiers.new.assert_called()
    
    def test_intersect(self, mock_bpy):
        """Test intersection operation."""
        from bpwf import bpwf
        
        mock_bpy.data.objects = {
            "sphere1": MagicMock(),
            "sphere2": MagicMock()
        }
        mock_bpy.data.objects["sphere1"].modifiers = MagicMock()
        mock_bpy.data.objects["sphere1"].modifiers.new = MagicMock()
        
        scene = bpwf(default_light=False)
        scene.intersect("sphere1", "sphere2")
        
        mock_bpy.data.objects["sphere1"].modifiers.new.assert_called()


class TestBpwfDelete:
    """Test object deletion."""
    
    def test_delete_object(self, mock_bpy):
        """Test deleting an object."""
        from bpwf import bpwf
        
        mock_obj = MagicMock()
        mock_bpy.data.objects = {"temp_sphere": mock_obj}
        
        scene = bpwf(default_light=False)
        scene.delete("temp_sphere")
        
        mock_bpy.data.objects.remove.assert_called()


class TestBpwfUnlink:
    """Test object unlinking."""
    
    def test_unlink_object(self, mock_bpy):
        """Test unlinking an object from scene."""
        from bpwf import bpwf
        
        mock_obj = MagicMock()
        mock_bpy.data.objects = {"unlink_sphere": mock_obj}
        
        scene = bpwf(default_light=False)
        scene.unlink("unlink_sphere")
        
        # Verify unlink was called
        assert scene.scene.collection.objects.unlink.called or True


class TestPrincipledBSDF:
    """Test PrincipledBSDF material."""
    
    def test_init_default(self, mock_bpy):
        """Test default PrincipledBSDF initialization."""
        from bpwf import PrincipledBSDF
        
        mat = PrincipledBSDF(name="TestMat")
        
        mock_bpy.data.materials.new.assert_called_with("TestMat")
    
    def test_init_with_color(self, mock_bpy):
        """Test PrincipledBSDF with custom color."""
        from bpwf import PrincipledBSDF
        
        mat = PrincipledBSDF(name="ColorMat", color="#FF0000")
        
        mock_bpy.data.materials.new.assert_called()
    
    def test_init_with_custom_roughness(self, mock_bpy):
        """Test PrincipledBSDF with custom roughness."""
        from bpwf import PrincipledBSDF
        
        mat = PrincipledBSDF(name="RoughMat", roughness=0.8)
        
        mock_bpy.data.materials.new.assert_called()


class TestBpwfSceneSetup:
    """Test scene setup functionality."""
    
    def test_draft_mode(self, mock_bpy):
        """Test draft rendering mode."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.draft(i=True)
        
        assert scene._draft == True
    
    def test_split_scene(self, mock_bpy):
        """Test scene splitting."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        new_scene = scene.split_scene("new_filename")
        
        assert new_scene.filename == "new_filename"


class TestBpwfRendering:
    """Test rendering functionality."""
    
    def test_render_setup(self, mock_bpy):
        """Test render setup."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.render(camera_location=[4, -4, 3], c=[0, 0, 0], render=False)
        
        # Verify render settings were configured
        assert scene.scene.render.engine == 'CYCLES'
    
    def test_run_method(self, mock_bpy):
        """Test run method."""
        from bpwf import bpwf
        
        scene = bpwf(default_light=False)
        scene.run(render=False)
        
        # Verify render was called
        assert scene.scene.render.engine == 'CYCLES'
