import os
import subprocess
import tempfile
from colour import Color
import numpy as np
import shutil
from os.path import expanduser
import sys

class pyb(object):
    """ An object to save commands for blender 3d plotting and render

        The ``pyb`` class is your blender scene, and I've coded in a limited
        set of commands for some simplified bldnder plotting.  Right now, it
        automatically saves to "brender_01.blend/.png" in the current
        directory, if you can't find the files.
    """
    def __init__(self):
        self.file_string = ''
        #self.file = tempfile.NamedTemporaryFile(suffix=".py", prefix="brender_")
        self.filename = "brender_01"
        self.has_run = False
        self.proj_matrix = None
        self.scene_setup()

    def scene_setup(self):
        """ deletes the default cube and sets up a scene to be used to render

            ``pyb.scene_setup`` is a convenience class that creates a new
            scene and deletes the default cube, leaving you with a clean slate
            to render on.  It is called automatically during initialization,
            so there's no real reason that the user should ever call this.

            :returns: None
        """
        self.file_string += 'import bpy\n'
        home = expanduser("~")
        self.file_string += open(home + '/code/pyb/blender_mats_utils.py', 'r').read()
        self.file_string += 'scene = bpy.context.scene\n'
        self.file_string += '# First, delete the default cube\n'
        self.file_string += 'bpy.ops.object.delete()\n'

    def sun(self, strength=1.0):
        """ creates a blender sun lamp

            ``pyb.sun`` creates a blender sun lamp and places it.  Location is
            non-sensical in this context, as blender places its sun lamps
            infinitely far away.  Strength, however, should be set, and set
            much lower than the strength for a point lamp.

            :param float strength: the strength of the sun lamp
            :returns: ``pyb`` object with ``sun`` lamp added
        """
        self.file_string += '# Now add a sun\n'
        self.file_string += 'lamp_data = bpy.data.lamps.new(name="Sun", type="SUN")\n'
        self.file_string += 'lamp_data.use_nodes = True\n'
        self.file_string += 'lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = %15.10e\n' % strength
        self.file_string += 'lamp_object = bpy.data.objects.new(name="Sun", object_data=lamp_data)\n'
        self.file_string += 'bpy.context.scene.objects.link(lamp_object)\n'
        self.file_string += 'lamp_object.select = True\n'
        self.file_string += 'bpy.context.scene.objects.active = lamp_object\n'
        return self

    def point(self, location=(0., 0., 0.), strength=1.0, name="Point",
           color='#555555', alpha=1.0):
        self.file_string += 'lamp_data = bpy.data.lamps.new(name=name, type="POINT")\n'
        self.file_string += 'lamp_data.use_nodes = True\n'
        self.file_string += 'lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = %15.10e\n' % strength
        self.file_string += 'lamp_object = bpy.data.objects.new(name=%s, object_data=lamp_data)\n' % name
        self.file_string += 'bpy.context.scene.objects.link(lamp_object)\n'
        self.file_string += 'lamp_object.location = (%15.10e, %15.10e, %15.10e)\n' % (location[0], location[1], location[2])
        rgb = Color(color).rgb
        self.file_string += 'lamp_object.color = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2], alpha)
        self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'
        self.file_string += 'lamp_object.select = True\n'
        self.file_string += 'bpy.context.scene.objects.active = lamp_object\n'

    def rpp(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None, c=None,
            l=None, name="rpp", color=None, alpha=1.0, verts=None):
        self.name = name
        if c is not None and l is not None:
            self.file_string += 'bpy.ops.mesh.primitive_cube_add()\n'
            self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
            self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
            self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
            self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
            self.file_string += '%s = bpy.context.object\n' % (name)
        elif verts is not None:
            self.file_string += 'mesh = bpy.data.meshes.new("%s")\n' % (name)
            self.file_string += '%s = bpy.data.objects.new("%s", mesh)\n' % (name, name)
            self.file_string += 'bpy.context.object.name = "%s"\n' % name
            self.file_string += 'bpy.context.scene.objects.link(%s)\n' % name
            self.file_string += 'verts = %s\n' % repr(verts)
            self.file_string += 'faces = [(0,1,3,2), (4,5,7,6), (0,1,5,4), (2,3,7,6), (1,3,7,5), (0,2,6,4)]\n'
            self.file_string += 'mesh.from_pydata(verts, [], faces)\n'
            self.file_string += 'mesh.update(calc_edges=True)\n'
        if color is not None:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)

    def plane(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None, c=None,
            l=None, name="rpp", color=None, alpha=1.0, verts=None):
        self.name = name
        if c is not None and l is not None:
            self.file_string += 'bpy.ops.mesh.primitive_plane_add()\n'
            self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
            self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
            self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
            self.file_string += 'bpy.context.object.rotation = (%15.10e, %15.10e, %15.10e)\n' % (r[0]/2., r[1]/2., r[2]/2.)
            self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
            self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)

    def sph(self, c=None, r=None, name="sph", color=None, alpha=1.0,
            emis=False):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4)\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (r, r, r)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color)
            self.set_matl(obj=name, matl="%s_color" % name)

    def gq(self, A=0.0, B=0.0, C=0.0, D=0.0, E=0.0, F=0.0, G=0.0, H=0.0, J=0.0,
           K=0.0, name="gq", color=None, alpha=1.0, emis=False):
        r""" ``gq`` adds a generalized quadratic surface using the mesh.

        ``gq`` adds a generalized quadratic surface using the mesh operators.
        The surface itself is defined by the function

        .. math::

            Ax^{2}+By^{2}+Cz^{2}+Dxy+Eyz\\+Fzx+Gx+Hy+Jz+K=0

        and takes inputs of :math:`A`, :math:`B`, :math:`C`, :math:`D`,
        :math:`E`, :math:`F`, :math:`G`, :math:`H`, :math:`J`, and :math:`K`.

        Note that this object is not necessarily closed, so it may need to be
        added to or subtracted from other surfaces or it will look unrealistic.

        :param float A: the coefficient :math:`A`
        :param float B: the coefficient :math:`B`
        :param float C: the coefficient :math:`C`
        :param float D: the coefficient :math:`D`
        :param float E: the coefficient :math:`E`
        :param float F: the coefficient :math:`F`
        :param float G: the coefficient :math:`G`
        :param float H: the coefficient :math:`H`
        :param float J: the coefficient :math:`J`
        :param float K: the coefficient :math:`K`
        """
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_xyz_function_surface(x_eq="u", y_eq="v", z_eq="")\n'
        self.file_string += 'obj = bpy.data.objects.new("%s", mesh_data)\n' % (name)
        self.file_string += 'scene = bpy.context.scene\n'
        self.file_string += 'scene.objects.link(obj)\n'
        self.file_string += 'obj.select = True\n'
        self.file_string += 'scene.objects.active = obj\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color)
            self.set_matl(obj=name, matl="%s_color" % name)

    def rcc(self, c=None, r=None, h=None, name="rcc", color=None, direction='z',
            alpha=1.0, emis=False):
        """ makes a cylinder with center point ``c``, radius ``r``, and height ``h``

            .. todo:: Make sure rotation works here
        """
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_cylinder_add(vertices=128)\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
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
            if direction == 0:
                rotdir = 1
            elif direction == 1:
                rotdir = 0
            else:
                rotdir = 2
        rotation[rotdir] = np.pi/2.
        axis = [r, r, r]
        c = list(c)
        axis[direction] = h/2.
        c[direction] += h/2.
        self.file_string += 'bpy.context.object.rotation_euler = (%15.10e, %15.10e, %15.10e)\n' % (rotation[0], rotation[1], rotation[2])
        self.file_string += 'bpy.ops.object.transform_apply(rotation=True)\n'
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (axis[0], axis[1], axis[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color)
            self.set_matl(obj=name, matl="%s_color" % name)

    def cone(self, c=(0., 0., 0.), r1=None, r2=None, h=None, name="cone",
             color=None, direction='z', alpha=1.0, emis=False):
        """ ``cone`` makes a truncated cone with height ``h`` and radii ``r1``
            and ``r2``.

            ``cone`` creates a truncated cone with the center of the cone at
            point ``c``, a tuple of three dimensions.  Then, the base has radius
            ``r1``, the tip has radius ``r2``, and the base and tip are
            separated by ``h``.

            .. todo:: Make sure rotation works here

            :param tuple c: the centerpoint of the cone
            :param float r1: radius of the base
            :param float r2: radius of the tip
            :param float h: distance between ``r1`` and ``r2``
            :param string direction: axis which coincides with the rotational
                axis of the cone, either ``'x'``, ``'y'``, or ``'z'``. The
                direction can be changed by reversing ``r1`` and ``r2``, so
                ``'+z'`` won't work.
        """
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_cone_add('
        self.file_string += 'radius1=%15.10e, radius2=%15.10e,' % (r1, r2)
        self.file_string += ' depth=%15.10e)\n' % (h)
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
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
            if direction == 0:
                rotdir = 1
            elif direction == 1:
                rotdir = 0
            else:
                rotdir = 2
        rotation[rotdir] = np.pi/2.
        # axis = [r, r, r]
        c = list(c)
        # axis[direction] = h/2.
        c[direction] += h/2.
        self.file_string += 'bpy.context.object.rotation_euler = '
        self.file_string += '(%15.10e, %15.10e, %15.10e)\n' % \
            (rotation[0], rotation[1], rotation[2])
        self.file_string += 'bpy.ops.object.transform_apply(rotation=True)\n'
        self.file_string += 'bpy.context.object.location = '
        self.file_string += '(%15.10e, %15.10e, %15.10e)\n' % \
            (c[0], c[1], c[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color)
            self.set_matl(obj=name, matl="%s_color" % name)

    def subtract(self, left, right):
        self.boolean(left=left, right=right, operation="DIFFERENCE")

    def union(self, left, right):
        self.boolean(left=left, right=right, operation="UNION")

    def boolean(self, left, right, operation):
        if operation == "DIFFERENCE":
            op = 'less'
        elif operation == "UNION":
            op = 'plus'
        name = left + "_" + operation.lower() + "_" + right
        self.file_string += 'bpy.context.scene.objects.active = %s\n' % (left)
        self.file_string += '%s = bpy.context.object.modifiers.new(type="BOOLEAN", name="%s")\n' % (name, left + "_" + operation.lower() + "_" + right)
        self.file_string += '%s.operation = "%s"\n' % (name, operation)
        self.file_string += '%s.object = %s\n' % (name, right)
        self.file_string += '%s.double_threshold = 0.1\n' % name
        self.file_string += 'bpy.ops.object.modifier_apply(apply_as="DATA", modifier="%s")\n' % (left + "_" + operation.lower() + "_" + right)
        self.file_string += 'bpy.context.scene.objects.unlink(%s)\n' % right
        self.file_string += 'bpy.context.scene.objects.active = bpy.context.object\n'
        self.file_string += '%s = bpy.context.object\n' % (left + "_" + op + "_" + right)

    def flat(self, name="Flat", color='#555555', alpha=1.0):
        self.file_string += '%s = bpy.data.materials.new("%s")\n' % (name, name)
        rgb = Color(color).rgb
        self.file_string += '%s.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (name, rgb[0], rgb[1], rgb[2])
        if alpha < 1.0:
            self.file_string += '%s.use_nodes = True\n' % name
            self.file_string += 'nodes = %s.node_tree.nodes\n' % name
            self.file_string += 'for key in nodes.values():\n'
            self.file_string += '    nodes.remove(key)\n'
            self.file_string += 'links = %s.node_tree.links\n' % name
            self.file_string += '%s_bsdf = nodes.new("ShaderNodeBsdfDiffuse")\n' % name
            self.file_string += '%s_bsdf.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (name, rgb[0], rgb[1], rgb[2], alpha)
            self.file_string += '%s_glass = nodes.new("ShaderNodeBsdfTransparent")\n' % name
            self.file_string += '%s_mix = nodes.new("ShaderNodeMixShader")\n' % name
            self.file_string += 'links.new(%s_bsdf.outputs[0], %s_mix.inputs[1])\n' % (name, name)
            self.file_string += 'links.new(%s_glass.outputs[0], %s_mix.inputs[2])\n' % (name, name)
            self.file_string += '%s_mix.inputs[0].default_value = %6.4f\n' % (name, 1.0 - alpha)
            self.file_string += '%s_material_output = nodes.new("ShaderNodeOutputMaterial")\n' % name
            self.file_string += 'links.new(%s_mix.outputs[0], %s_material_output.inputs[0])\n' % (name, name)
            self.file_string += 'for node in nodes:\n'
            self.file_string += '    node.update()\n'
        #self.file_string += '%s = flat\n' % name

    def emis(self, name="Source", color="#555555", alpha=1.0, volume=False):
        rgb = Color(color).rgb
        self.file_string += 'source = bpy.data.materials.new("%s")\n' % name
        self.file_string += 'source.use_nodes = True\n'
        self.file_string += 'nodes = source.node_tree.nodes\n'
        self.file_string += 'for key in nodes.values():\n'
        self.file_string += '    nodes.remove(key)\n'
        self.file_string += 'links = source.node_tree.links\n'
        self.file_string += 'e = nodes.new(type="ShaderNodeEmission")\n'
        self.file_string += 'e.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2], alpha)
        self.file_string += 'e.inputs[1].default_value = 5.0\n'
        self.file_string += '# Make a material output\n'
        self.file_string += 'material_output = nodes.new("ShaderNodeOutputMaterial")\n'
        self.file_string += '# link from the shader and displacement groups to the outputs\n'
        if volume:
            self.file_string += 'links.new(e.outputs[0], material_output.inputs[1])\n'
        else:
            self.file_string += 'links.new(e.outputs[0], material_output.inputs[0])\n'
        self.file_string += 'for node in nodes:\n'
        self.file_string += '    node.update()\n'
        self.file_string += '%s = source\n' % name

    def trans(self, name="Trans", color="#555555"):
        self.file_string += 'trans = bpy.data.materials.new("%s")\n' % name
        rgb = Color(color).rgb
        self.file_string += 'trans.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2])
        self.file_string += '%s = trans\n' % name

    def image(self, name="Image", fname=None, alpha=1.0, volume=False):
        rgb = Color(color).rgb
        self.file_string += 'source = bpy.data.materials.new("%s")\n' % name
        self.file_string += 'source.use_nodes = True\n'
        self.file_string += 'nodes = source.node_tree.nodes\n'
        self.file_string += 'for key in nodes.values():\n'
        self.file_string += '    nodes.remove(key)\n'
        self.file_string += 'links = source.node_tree.links\n'
        self.file_string += 'e = nodes.new(type="ShaderNodeEmission")\n'
        self.file_string += 'e.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2], alpha)
        self.file_string += 'e.inputs[1].default_value = 5.0\n'
        self.file_string += '# Make a material output\n'
        self.file_string += 'material_output = nodes.new("ShaderNodeOutputMaterial")\n'
        self.file_string += '# link from the shader and displacement groups to the outputs\n'
        if volume:
            self.file_string += 'links.new(e.outputs[0], material_output.inputs[1])\n'
        else:
            self.file_string += 'links.new(e.outputs[0], material_output.inputs[0])\n'
        self.file_string += 'for node in nodes:\n'
        self.file_string += '    node.update()\n'
        self.file_string += '%s = source\n' % name

    def set_matl(self, obj=None, matl=None):
        # self.file_string += 'obj = bpy.context.scene.objects.get("%s")\n' % obj
        # self.file_string += 'bpy.context.scene.objects.active = obj\n'
        self.file_string += '%s.active_material = %s\n' % (obj, matl)

    def cutaway(self, points=None):
        # first, create an extrude that will cutaway
        pass
        # then, select all objects
        # then subtract the extrude object

    def look_at(self, target=None):
        self.file_string += 'camera_track.target = (bpy.data.objects["%s"])\n' % target

    def render(self, camera_location=(500, 500, 300), c=(0., 0., 0.),
               l=(250., 250., 250.), render=True, fit=True, samples=20, res=[1920, 1080]):
        resw = res[0]
        resh = res[1]
        self.file_string += 'bpy.context.scene.objects.active.select = False\n'
        self.file_string += 'bpy.ops.object.visual_transform_apply()\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.engine = "CYCLES"\n'
        self.file_string += 'render = bpy.data.scenes["Scene"].render\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_x = %d * 2.\n' % resw
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_y = %d * 2.\n' % resh
        self.file_string += 'world = bpy.data.worlds["World"]\n'
        self.file_string += 'world.use_nodes = True\n'
        self.file_string += 'empty = bpy.data.objects.new("Empty", None)\n'
        self.file_string += 'bpy.context.scene.objects.link(empty)\n'
        self.file_string += 'empty.empty_draw_size = 1\n'
        self.file_string += 'empty.empty_draw_type = "CUBE"\n'
        self.file_string += 'bpy.data.objects["Empty"].location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.data.objects["Empty"].scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'empty = bpy.data.objects["Empty"]\n'
        self.file_string += 'camera = bpy.data.objects["Camera"]\n'
        self.file_string += 'camera.location = (%6.4f, %6.4f, %6.4f)\n' % \
            (camera_location[0], camera_location[1], camera_location[2])
        self.file_string += 'bpy.data.cameras[camera.name].clip_end = 10000.0\n'
        self.file_string += 'bpy.data.cameras[camera.name].clip_start = 0.0\n'
        self.file_string += 'camera_track = camera.constraints.new("TRACK_TO")\n'
        self.file_string += 'camera_track.track_axis = "TRACK_NEGATIVE_Z"\n'
        self.file_string += 'camera_track.up_axis = "UP_Y"\n'
        self.look_at(target="Empty")
        self.file_string += '# changing these values does affect the render.\n'
        self.file_string += 'bg = world.node_tree.nodes["Background"]\n'
        self.file_string += 'bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)\n'
        self.file_string += 'bg.inputs[1].default_value = 1.0\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.filepath = "%s" + ".png"\n' % self.filename
        self.file_string += 'bpy.context.scene.render.use_freestyle = True\n'
        self.file_string += 'bpy.context.scene.cycles.samples = %d\n' % samples
        self.file_string += 'bpy.context.scene.cycles.max_bounces = 32\n'
        self.file_string += 'bpy.context.scene.cycles.min_bounces = 3\n'
        self.file_string += 'bpy.context.scene.cycles.glossy_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.transmission_bounces = 32\n'
        self.file_string += 'bpy.context.scene.cycles.volume_bounces = 4\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_max_bounces = 32\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_min_bounces = 8\n'
        self.file_string += 'bpy.data.scenes["Scene"].cycles.film_transparent = True\n'
        self.file_string += 'bpy.context.scene.cycles.filter_glossy = 0.05\n'
        self.file_string += 'bpy.ops.wm.save_as_mainfile(filepath="%s.blend")\n' % self.filename
        if render:
            self.file_string += 'bpy.ops.render.render( write_still=True )\n'
        self.file_string += 'modelview_matrix = camera.matrix_world.inverted()\n'
        self.file_string += 'projection_matrix = camera.calc_matrix_camera(\n'
        self.file_string += '        render.resolution_x,\n'
        self.file_string += '        render.resolution_y,\n'
        self.file_string += '        render.pixel_aspect_x,\n'
        self.file_string += '        render.pixel_aspect_y,\n'
        self.file_string += '        )\n'
        self.file_string += 'P, K, RT = get_3x4_P_matrix_from_blender(camera)\n'
        self.file_string += 'import os\n'
        self.file_string += 'proj_matrix = "[[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e]]" % (P[0][0], P[0][1], P[0][2], P[0][3], P[1][0], P[1][1], P[1][2], P[1][3], P[2][0], P[2][1], P[2][2], P[2][3])\n'
        if render:
            self.file_string += 'os.system("convert %s.png -set proj_matrix \'%%s\' %s.png" %% proj_matrix)\n' % (self.filename, self.filename)

    def run(self, filename=None, **kwargs):
        """ Opens a blender instance and runs the generated model rendering
        """
        self.render(**kwargs)
        if sys.platform == "darwin":
            blender_path = '/Applications/blender.app/Contents/MacOS/blender'
        else:
            blender_path = 'blender'
        with open(self.filename + '.py', 'w') as f:
            f.write(self.file_string)
            cmd = "{bpath} --background --python {fname}.py".format(bpath=blender_path, fname=self.filename)
            #print cmd
            #print os.popen('cat %s' % self.filename + '.py').read()
        render = subprocess.Popen(cmd, shell=True)
        render.communicate()
        if 'render' in kwargs:
            rendered = kwargs['render']
        else:
            rendered = True
        if filename is not None and rendered:
            shutil.copy(self.filename + ".png", filename)
            proj_matrix = os.popen("identify -verbose %s | grep proj_matrix" % filename).read()
            exec(proj_matrix.replace(" ", "").replace(":", "="))
            self.proj_matrix = proj_matrix
        self.has_run = True

    def show(self):
        """ Opens the image if it has been rendered
        """
        if self.has_run:
            cmd = "eog %s.png" % self.filename
            subprocess.Popen(cmd, shell=True)
