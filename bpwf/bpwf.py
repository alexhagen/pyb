"""
bpwf - Blender for Publication-Worthy Figures
Core scene management and rendering using bpy directly.
"""

from __future__ import print_function
import os
import copy
import random
import numpy as np
from colour import Color

try:
    import bpy
except ImportError:
    # Allow import without bpy for testing
    bpy = None

np.set_printoptions(threshold=np.inf)


class FileStringStream:
    """Helper class for building script strings (kept for compatibility)."""
    
    def __init__(self):
        self.file_string = ''

    def copy(self):
        return copy.deepcopy(self)

    def add_line(self, string):
        self.file_string += str(string) + "\n"
        return self

    def a(self, *args, **kwargs):
        return self.add_line(*args, **kwargs)

    def __str__(self):
        return self.file_string


class PrincipledBSDF:
    """Principled BSDF material using direct bpy calls."""
    
    def __init__(self, name='pbsdf', color='#ffffff', specular=0.01, roughness=0.5):
        if bpy is None:
            raise RuntimeError("bpy module not available. Install with: pip install bpy")
        
        if isinstance(color, str):
            rgb = Color(color).rgb
        else:
            rgb = color
        
        # Create material
        self.material = bpy.data.materials.new(name)
        self.material.use_nodes = True
        nodes = self.material.node_tree.nodes
        
        # Clear default nodes
        nodes.clear()
        
        links = self.material.node_tree.links
        
        # Create Principled BSDF
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1.0)  # Base Color
        bsdf.inputs['Specular IOR Level'].default_value = specular  # Specular
        bsdf.inputs['Roughness'].default_value = roughness  # Roughness
        
        # Create Material Output
        material_output = nodes.new("ShaderNodeOutputMaterial")
        links.new(bsdf.outputs[0], material_output.inputs[0])


class bpwf:
    """Main class for creating and rendering Blender scenes using bpy directly.
    
    This class provides a high-level interface for creating 3D scenes with
    primitives, materials, lights, and rendering capabilities.
    """
    
    def __init__(self, default_light=True, scene_name=None):
        """Initialize a new bpwf scene.
        
        Args:
            default_light: Whether to delete the default light
            scene_name: Optional name for a new scene (for multi-scene support)
        """
        if bpy is None:
            raise RuntimeError("bpy module not available. Install with: pip install bpy")
        
        self.filename = "brender_01"
        self.has_run = False
        self.proj_matrix = None
        self._draft = False
        self.path = os.getcwd()
        self.default_light = default_light
        self.particles = []
        
        # Support multiple scenes
        if scene_name:
            self.scene = bpy.data.scenes.new(scene_name)
            bpy.context.window.scene = self.scene
        else:
            self.scene = bpy.context.scene
        
        self.scene_setup()
    
    def scene_setup(self):
        """Set up the scene by removing default objects."""
        # Delete default cube if it exists
        if "Cube" in bpy.data.objects:
            cube = bpy.data.objects["Cube"]
            # Check if cube is in the current scene
            if cube.name in self.scene.objects:
                bpy.data.objects.remove(cube, do_unlink=True)
        
        # Delete default light if requested
        if self.default_light and "Light" in bpy.data.objects:
            light = bpy.data.objects["Light"]
            # Check if light is in the current scene
            if light.name in self.scene.objects:
                bpy.data.objects.remove(light, do_unlink=True)
        
        # Create collections for organization
        if "freestyle_group" not in bpy.data.collections:
            self.fg = bpy.data.collections.new("freestyle_group")
        else:
            self.fg = bpy.data.collections["freestyle_group"]
        
        if "transparent_group" not in bpy.data.collections:
            self.tg = bpy.data.collections.new("transparent_group")
        else:
            self.tg = bpy.data.collections["transparent_group"]
    
    def delete(self, name):
        """Delete an object by name."""
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            bpy.data.objects.remove(obj, do_unlink=True)
    
    def sun(self, strength=1.0):
        """Create a sun lamp.
        
        Args:
            strength: Light strength
        
        Returns:
            self for method chaining
        """
        light_data = bpy.data.lights.new(name="Sun", type='SUN')
        light_data.use_nodes = True
        light_data.node_tree.nodes["Emission"].inputs[1].default_value = strength
        
        light_object = bpy.data.objects.new(name="Sun", object_data=light_data)
        self.scene.collection.objects.link(light_object)
        
        return self
    
    def point(self, location=(0., 0., 0.), strength=1.0, name="Point",
              color='#555555', alpha=1.0, layer='render'):
        """Create a point light.
        
        Args:
            location: Light position (x, y, z)
            strength: Light strength
            name: Light name
            color: Light color
            alpha: Transparency
            layer: Layer assignment
        """
        light_data = bpy.data.lights.new(name=name, type='POINT')
        light_data.use_nodes = True
        light_data.node_tree.nodes["Emission"].inputs[1].default_value = strength
        
        light_object = bpy.data.objects.new(name=name, object_data=light_data)
        self.scene.collection.objects.link(light_object)
        light_object.location = location
        
        rgb = Color(color).rgb
        light_data.color = (rgb[0], rgb[1], rgb[2])
        
        if layer == 'render':
            self.fg.objects.link(light_object)
        elif layer == 'trans':
            self.tg.objects.link(light_object)
    
    def sph(self, c=None, r=None, name="sph", color=None, alpha=1.0,
            emis=False, layer='render', subd=4, **kwargs):
        """Create a sphere.
        
        Args:
            c: Center position [x, y, z]
            r: Radius
            name: Object name
            color: Material color
            alpha: Transparency
            emis: Whether to use emissive material
            layer: Layer assignment
            subd: Subdivision level
        """
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subd, location=c)
        obj = bpy.context.object
        obj.name = name
        obj.scale = (r, r, r)
        bpy.ops.object.transform_apply(location=True, scale=True)
        
        if layer == 'render':
            self.fg.objects.link(obj)
        elif layer == 'trans':
            self.tg.objects.link(obj)
        
        if color == 'sem':
            self.sem(name=f'{name}_sem')
            self.set_matl(obj=name, matl=f'{name}_sem')
        elif color is not None and not emis:
            self.flat(name=f"{name}_color", color=color, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif color is not None and emis:
            self.emis(name=f"{name}_color", alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl=f"{name}_color")
    
    def rpp(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None, c=None,
            l=None, name="rpp", color=None, alpha=1.0, verts=None,
            emis=False, layer='render', r=None, matl=None, **kwargs):
        """Create a rectangular parallelepiped (box).
        
        Args:
            x1, x2, y1, y2, z1, z2: Box bounds
            c: Center position [x, y, z]
            l: Dimensions [lx, ly, lz]
            name: Object name
            color: Material color
            alpha: Transparency
            verts: Custom vertices
            emis: Whether to use emissive material
            layer: Layer assignment
            r: Rotation [rx, ry, rz]
            matl: Custom material
        """
        if (x1 is not None) and (x2 is not None) and (y1 is not None) and \
           (y2 is not None) and (z1 is not None) and (z2 is not None):
            c = [np.mean([x1, x2]), np.mean([y1, y2]), np.mean([z1, z2])]
            l = [x2 - x1, y2 - y1, z2 - z1]
        
        if c is not None and l is not None:
            bpy.ops.mesh.primitive_cube_add(location=c)
            obj = bpy.context.object
            obj.name = name
            obj.scale = (l[0]/2., l[1]/2., l[2]/2.)
            bpy.ops.object.transform_apply(location=True, scale=True)
            
            if r is not None:
                obj.rotation_euler = r
                bpy.ops.object.transform_apply(rotation=True)
        
        elif verts is not None:
            mesh = bpy.data.meshes.new(name)
            obj = bpy.data.objects.new(name, mesh)
            self.scene.collection.objects.link(obj)
            faces = [(0,1,3,2), (4,5,7,6), (0,1,5,4), (2,3,7,6), (1,3,7,5), (0,2,6,4)]
            mesh.from_pydata(verts, [], faces)
            mesh.update(calc_edges=True)
        
        if layer == 'render':
            self.fg.objects.link(obj)
        elif layer == 'trans':
            self.tg.objects.link(obj)
        
        if color is not None and not emis:
            self.flat(name=f"{name}_color", color=color, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif color is not None and emis:
            self.emis(name=f"{name}_color", alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl=f"{name}_color")
        
        if matl is not None:
            if hasattr(matl, 'material'):
                self.set_matl(obj=name, matl=matl.material.name)
            else:
                # Assume it's a material name string
                self.set_matl(obj=name, matl=matl)
    
    def rcc(self, c=None, r=None, h=None, name="rcc", color=None, direction='z',
            alpha=1.0, emis=False, layer='render', **kwargs):
        """Create a cylinder.
        
        Args:
            c: Center position [x, y, z]
            r: Radius
            h: Height
            name: Object name
            color: Material color
            direction: Axis direction ('x', 'y', or 'z')
            alpha: Transparency
            emis: Whether to use emissive material
            layer: Layer assignment
        """
        rotation = [0., 0., 0.]
        if direction == 'z':
            direction = 2
            rotdir = 2
        elif direction == 'y':
            direction = 1
            rotdir = 0
        elif direction == 'x':
            direction = 0
            rotdir = 1
        else:
            direction = int(direction)
            rotdir = 1 if direction == 0 else (0 if direction == 1 else 2)
        
        rotation[rotdir] = np.pi/2.
        c = list(c)
        c[direction] += h/2.
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=128, location=c)
        obj = bpy.context.object
        obj.name = name
        obj.rotation_euler = rotation
        bpy.ops.object.transform_apply(rotation=True)
        
        axis = [r, r, r]
        axis[direction] = h/2.
        obj.scale = axis
        bpy.ops.object.transform_apply(location=True, scale=True)
        
        if layer == 'render':
            self.fg.objects.link(obj)
        elif layer == 'trans':
            self.tg.objects.link(obj)
        
        if color is not None and not emis:
            self.flat(name=f"{name}_color", color=color, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif color is not None and emis:
            self.emis(name=f"{name}_color", color=color, **kwargs)
            self.set_matl(obj=name, matl=f"{name}_color")
    
    def cone(self, c=(0., 0., 0.), r1=None, r2=None, h=None, name="cone",
             color=None, direction='z', alpha=1.0, emis=False, layer='render',
             rotation=None, **kwargs):
        """Create a cone.
        
        Args:
            c: Center position [x, y, z]
            r1: Base radius
            r2: Top radius
            h: Height
            name: Object name
            color: Material color
            direction: Axis direction
            alpha: Transparency
            emis: Whether to use emissive material
            layer: Layer assignment
            rotation: Custom rotation
        """
        if rotation is None:
            rotation = [0., 0., 0.]
            if direction == 'z':
                direction = 2
                rotdir = 2
            elif direction == 'y':
                direction = 1
                rotdir = 0
            elif direction == 'x':
                direction = 0
                rotdir = 1
            else:
                direction = int(direction)
                rotdir = 1 if direction == 0 else (0 if direction == 1 else 2)
            rotation[rotdir] = np.pi/2.
        
        c = list(c)
        c[direction] += h/2.
        
        bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=c)
        obj = bpy.context.object
        obj.name = name
        obj.rotation_euler = rotation
        bpy.ops.object.transform_apply(rotation=True, location=True)
        
        if layer == 'render':
            self.fg.objects.link(obj)
        elif layer == 'trans':
            self.tg.objects.link(obj)
        
        if color is not None and not emis:
            self.flat(name=f"{name}_color", color=color, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif color is not None and emis:
            self.emis(name=f"{name}_color", color=color, **kwargs)
            self.set_matl(obj=name, matl=f"{name}_color")
    
    def plane(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None,
              c=None, l=None, name="plane", color=None, alpha=1.0, verts=None,
              emis=False, image=None, layer='render', **kwargs):
        """Create a plane.
        
        Args:
            x1, x2, y1, y2, z1, z2: Plane bounds
            c: Center position
            l: Dimensions
            name: Object name
            color: Material color
            alpha: Transparency
            verts: Custom vertices
            emis: Whether to use emissive material
            image: Image texture path
            layer: Layer assignment
        """
        if c is None and l is None:
            c = [(x1 + x2)/2., (y1 + y2)/2., (z1 + z2)/2.]
            l = [x2 - x1, y2 - y1, z2 - z1]
        
        if c is not None and l is not None:
            r = [0.0, 0.0, 0.0]
            if l[0] == 0.0:
                rotdir = 0
            elif l[1] == 0.0:
                rotdir = 1
            elif l[2] == 0.0:
                rotdir = 2
            r[rotdir] = np.pi/2.
            
            bpy.ops.mesh.primitive_plane_add(location=c)
            obj = bpy.context.object
            obj.name = name
            obj.scale = (l[0]/2., l[1]/2., l[2]/2.)
            bpy.ops.object.transform_apply(scale=True)
            obj.rotation_euler = r
            bpy.ops.object.transform_apply(rotation=True, location=True)
            
            if layer == 'render':
                self.fg.objects.link(obj)
            elif layer == 'trans':
                self.tg.objects.link(obj)
        
        if color is not None and not emis:
            self.flat(name=f"{name}_color", color=color, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif color is not None and emis:
            self.emis(name=f"{name}_color", alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl=f"{name}_color")
        elif image is not None:
            self.image(name=f"{name}_color", fname=image, alpha=alpha)
            self.set_matl(obj=name, matl=f"{name}_color")
    
    def subtract(self, left, right, unlink=True):
        """Boolean subtraction operation."""
        self.boolean(left=left, right=right, operation="DIFFERENCE", unlink=unlink)
    
    def union(self, left, right, unlink=True):
        """Boolean union operation."""
        self.boolean(left=left, right=right, operation="UNION", unlink=unlink)
    
    def intersect(self, left, right, unlink=True):
        """Boolean intersection operation."""
        self.boolean(left=left, right=right, operation="INTERSECT", unlink=unlink)
    
    def boolean(self, left, right, operation, unlink=True):
        """Perform boolean operation between two objects.
        
        Args:
            left: Left operand object name
            right: Right operand object name
            operation: Boolean operation type
            unlink: Whether to unlink the right object after operation
        """
        left_obj = bpy.data.objects[left]
        right_obj = bpy.data.objects[right]
        
        modifier = left_obj.modifiers.new(type="BOOLEAN", name=f"{left}_{operation.lower()}_{right}")
        modifier.operation = operation
        modifier.object = right_obj
        modifier.solver = 'EXACT'
        
        # Apply modifier
        bpy.context.view_layer.objects.active = left_obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        if unlink:
            bpy.data.objects.remove(right_obj, do_unlink=True)
    
    def unlink(self, name):
        """Unlink an object from the scene."""
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            self.scene.collection.objects.unlink(obj)
    
    def flat(self, name="Flat", color='#555555', alpha=1.0):
        """Create a flat diffuse material.
        
        Args:
            name: Material name
            color: Material color
            alpha: Transparency
        """
        mat = bpy.data.materials.new(name)
        rgb = Color(color).rgb
        mat.diffuse_color = (rgb[0], rgb[1], rgb[2], alpha)
        
        if alpha < 1.0:
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()
            links = mat.node_tree.links
            
            bsdf = nodes.new("ShaderNodeBsdfDiffuse")
            bsdf.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], alpha)
            
            transparent = nodes.new("ShaderNodeBsdfTransparent")
            mix = nodes.new("ShaderNodeMixShader")
            mix.inputs[0].default_value = 1.0 - alpha
            
            links.new(bsdf.outputs[0], mix.inputs[1])
            links.new(transparent.outputs[0], mix.inputs[2])
            
            material_output = nodes.new("ShaderNodeOutputMaterial")
            links.new(mix.outputs[0], material_output.inputs[0])
    
    def emis(self, name="Source", color="#555555", alpha=1.0, volume=False,
             emittance=1.0, **kwargs):
        """Create an emissive material.
        
        Args:
            name: Material name
            color: Emission color
            alpha: Transparency
            volume: Whether to use volume output
            emittance: Emission strength
        """
        if isinstance(color, str):
            rgb = Color(color).rgb
        else:
            rgb = color
        
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        links = mat.node_tree.links
        
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], alpha)
        emission.inputs[1].default_value = emittance
        
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 1.0 - alpha
        
        links.new(emission.outputs[0], mix.inputs[1])
        links.new(transparent.outputs[0], mix.inputs[2])
        
        material_output = nodes.new("ShaderNodeOutputMaterial")
        links.new(mix.outputs[0], material_output.inputs[0])
    
    def trans(self, name="Trans", color="#555555"):
        """Create a transparent material.
        
        Args:
            name: Material name
            color: Material color
        """
        mat = bpy.data.materials.new(name)
        rgb = Color(color).rgb
        mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    
    def sem(self, name="Sem", e_color="#EEEEEE", bsdf_color='#000000',
            lw_value=0.3, **kwargs):
        """Create a SEM-style material.
        
        Args:
            name: Material name
            e_color: Emission color
            bsdf_color: Base color
            lw_value: Layer weight blend value
        """
        if isinstance(e_color, str):
            e_rgb = Color(e_color).rgb
        else:
            e_rgb = e_color
        
        if isinstance(bsdf_color, str):
            bsdf_rgb = Color(bsdf_color).rgb
        else:
            bsdf_rgb = bsdf_color
        
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        links = mat.node_tree.links
        
        # Layer weight
        layer_weight = nodes.new(type="ShaderNodeLayerWeight")
        layer_weight.inputs[0].default_value = lw_value
        
        # Principled BSDF
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.inputs[0].default_value = (bsdf_rgb[0], bsdf_rgb[1], bsdf_rgb[2], 1.0)
        bsdf.inputs[7].default_value = 1.0  # Roughness
        
        # Emission
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs[0].default_value = (e_rgb[0], e_rgb[1], e_rgb[2], 1.0)
        emission.inputs[1].default_value = 100.0
        
        # Mix shader
        mix = nodes.new("ShaderNodeMixShader")
        links.new(layer_weight.outputs[0], mix.inputs[0])
        links.new(bsdf.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        
        material_output = nodes.new("ShaderNodeOutputMaterial")
        links.new(mix.outputs[0], material_output.inputs[0])
    
    def image(self, name="Image", fname=None, alpha=1.0, volume=False,
              color="#ffffff", layer='render'):
        """Create an image texture material.
        
        Args:
            name: Material name
            fname: Image file path
            alpha: Transparency
            volume: Whether to use volume output
            color: Tint color
            layer: Layer assignment
        """
        rgb = Color(color).rgb
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        links = mat.node_tree.links
        
        emission = nodes.new(type="ShaderNodeEmission")
        emission.inputs[0].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        emission.inputs[1].default_value = 5.0
        
        image = bpy.data.images.load(fname)
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = image
        
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 1.0 - alpha
        
        links.new(tex_node.outputs[0], mix.inputs[1])
        links.new(transparent.outputs[0], mix.inputs[2])
        
        material_output = nodes.new("ShaderNodeOutputMaterial")
        output_slot = 1 if volume else 0
        links.new(mix.outputs[0], material_output.inputs[output_slot])
    
    def set_matl(self, obj=None, matl=None):
        """Assign a material to an object.
        
        Args:
            obj: Object name
            matl: Material name
        """
        if obj in bpy.data.objects:
            obj_ref = bpy.data.objects[obj]
            if matl in bpy.data.materials:
                obj_ref.active_material = bpy.data.materials[matl]
    
    def draft(self, i=True):
        """Enable draft mode for faster rendering.
        
        Args:
            i: Whether to enable draft mode
        
        Returns:
            self for method chaining
        """
        self._draft = i
        return self
    
    def look_at(self, target=None):
        """Point camera at a target object.
        
        Args:
            target: Target object name
        """
        if "Camera" in bpy.data.objects and target in bpy.data.objects:
            camera = bpy.data.objects["Camera"]
            # This would need the camera_track constraint to be set up
            pass
    
    def render(self, camera_location=(500, 500, 300), c=(0., 0., 0.),
               l=(250., 250., 250.), render=True, fit=True, samples=20,
               res=[1920, 1080], draft=False, freestyle=True,
               perspective=True, pscale=350, bg_lum=1.0, bg_color=(1.0, 1.0, 1.0),
               transparent=True, **kwargs):
        """Set up and execute rendering.
        
        Args:
            camera_location: Camera position
            c: Scene center
            l: Scene extents
            render: Whether to actually render
            fit: Whether to fit scene
            samples: Render samples
            res: Resolution [width, height]
            draft: Draft mode
            freestyle: Enable freestyle
            perspective: Use perspective camera
            pscale: Orthographic scale
            bg_lum: Background luminance
            bg_color: Background color
            transparent: Transparent background
        """
        if self._draft or draft:
            res = [640, 480]
            samples = 10
        
        # Set render engine
        self.scene.render.engine = 'CYCLES'
        self.scene.render.resolution_x = res[0]
        self.scene.render.resolution_y = res[1]
        
        # Set up camera - create unique camera for each scene
        camera_name = f"Camera_{self.scene.name}" if self.scene.name != "Scene" else "Camera"
        
        if camera_name not in bpy.data.objects:
            camera_data = bpy.data.cameras.new(camera_name)
            camera = bpy.data.objects.new(camera_name, camera_data)
            self.scene.collection.objects.link(camera)
            self.scene.camera = camera
        else:
            camera = bpy.data.objects[camera_name]
            # Make sure camera is in this scene
            if camera.name not in self.scene.objects:
                self.scene.collection.objects.link(camera)
            self.scene.camera = camera
        
        camera.location = camera_location
        camera.data.clip_end = 10000.0
        camera.data.clip_start = 0.0
        
        if not perspective:
            camera.data.type = 'ORTHO'
            camera.data.ortho_scale = pscale
        
        # Set up world
        world = bpy.data.worlds.get("World")
        if world:
            world.use_nodes = True
            bg_node = world.node_tree.nodes.get("Background")
            if bg_node:
                bg_node.inputs[0].default_value = (*bg_color, 1.0)
                bg_node.inputs[1].default_value = bg_lum
        
        # Set render settings
        self.scene.cycles.samples = samples
        self.scene.cycles.max_bounces = 32
        self.scene.cycles.transparent_max_bounces = 32
        self.scene.render.film_transparent = transparent
        self.scene.render.use_freestyle = freestyle
        
        # Set output path with absolute path
        output_path = os.path.join(self.path, f"{self.filename}.png")
        self.scene.render.filepath = output_path
        
        # Save blend file
        blend_path = os.path.join(self.path, f"{self.filename}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        
        # Render - switch to the correct scene context
        if render:
            # Make sure we're rendering the correct scene
            bpy.context.window.scene = self.scene
            bpy.ops.render.render(write_still=True)
            self.has_run = True
    
    def run(self, filename=None, block=True, **kwargs):
        """Execute rendering (compatibility method).
        
        Args:
            filename: Output filename
            block: Whether to block until complete
            **kwargs: Additional render arguments
        """
        self.render(**kwargs)
        
        if filename is not None and self.has_run:
            import shutil
            shutil.copy(f"{self.filename}.png", filename)
    
    def show(self):
        """Display the rendered image (for Jupyter notebooks)."""
        if self.has_run:
            try:
                from IPython.display import display, Image
                return display(Image(filename=f"{self.filename}.png"))
            except ImportError:
                print(f"Rendered image saved to: {self.filename}.png")
    
    def split_scene(self, filename):
        """Create a copy of the scene with a new filename.
        
        Args:
            filename: New filename
        
        Returns:
            New bpwf instance
        """
        newscene = copy.deepcopy(self)
        newscene.filename = filename
        return newscene
