from __future__ import print_function
import os
import subprocess
import tempfile
from colour import Color
import numpy as np
import shutil
from os.path import expanduser
import sys
import copy
from IPython.display import display, HTML
import random
from psgv import psgv
import copy


np.set_printoptions(threshold=sys.maxsize)

cutawayid = psgv.psgv('__cutaway_id__')
cutawayid.val = 1

top_layer = [False] * 20
top_layer[0] = True
n_layer = [False] * 20
n_layer[1] = True

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
        self._draft = False
        self.path = os.getcwd()
        self.scene_setup()

    def copy(self):
        return copy.deepcopy(self)

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
        #self.file_string += 'fg = bpy.data.groups.new("freestyle_group")\n'
        #self.file_string += 'tg = bpy.data.groups.new("transparent_group")\n'
        #self.file_string += 'bpy.ops.scene.render_layer_add()\n'

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
        self.file_string += 'bpy.context.collection.objects.link(lamp_object)\n'
        self.file_string += 'lamp_object.select = True\n'
        self.file_string += 'bpy.context.collection.objects.active = lamp_object\n'
        return self

    def point(self, location=(0., 0., 0.), strength=1.0, name="Point",
           color='#555555', alpha=1.0, layer='render'):
        self.file_string += 'lamp_data = bpy.data.lamps.new(name="%s", type="POINT")\n' % name
        self.file_string += 'lamp_data.use_nodes = True\n'
        self.file_string += 'lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = %15.10e\n' % strength
        self.file_string += 'lamp_object = bpy.data.objects.new(name="%s", object_data=lamp_data)\n' % name
        self.file_string += 'bpy.context.collection.objects.link(lamp_object)\n'
        self.file_string += 'lamp_object.location = (%15.10e, %15.10e, %15.10e)\n' % (location[0], location[1], location[2])
        rgb = Color(color).rgb
        self.file_string += 'lamp_object.color = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2], alpha)
        self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'
        self.file_string += 'lamp_object.select = True\n'
        self.file_string += 'bpy.context.collection.objects.active = lamp_object\n'
        name = 'lamp_object'
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)

    def volume(self, matrix, c=[0., 0., 0.], name="volume", layer="render", cmap='gray', normalization='layer',
               density_ramp='exp', density_ramp_coeffs=[2.0,], density_multiplier=1.0, color=None, color_ramp=None,
               idx=None):
        import pyopenvdb as vdb
        import numpy as np
        import matplotlib.cm as cm
        from matplotlib.colors import Normalize, to_hex, hsv_to_rgb, rgb_to_hsv
        filename = f'{name}_vdb_data'
        if isinstance(cmap, str):
            cmap = cm.ScalarMappable(None, cmap)
            cmap = cmap.get_cmap()
        if normalization == 'layer':
            density = np.empty(matrix.shape)
            _color = np.empty((matrix.shape[0], matrix.shape[1], matrix.shape[2], 3))
            for i, layer in enumerate(matrix):
                _density = np.exp(2.0*layer)
                norm = Normalize(vmin=np.min(_density), vmax=np.max(_density))
                _density = norm(_density)
                _density[_density<0.5] = 0.0
                density[i, ...] = _density
                __color = layer
                norm = Normalize(vmin=np.min(__color), vmax=np.max(__color))
                __color = cmap(norm(__color))
                __color = __color[:, :, :3]
                _color[i, ...] = __color
        elif normalization == 'global':
            density = np.copy(matrix)
            norm = Normalize(vmin=np.nanmin(density), vmax=np.nanmax(density))
            density = norm(density)
            _color = cmap(norm(matrix))
            _color = _color[:, :, :, :3]
        if idx is not None:
            density = density[idx]
            _color = _color[idx]
        density_grid = vdb.FloatGrid()
        density_grid.copyFromArray(density)
        density_grid.name = 'density'
        color_grid = vdb.Vec3SGrid()
        color_grid.copyFromArray(_color)
        color_grid.name = 'color'
        vdb.write(f'{filename}.vdb', [density_grid, color_grid])
        #c[0] = c[0] - matrix.shape[0]/2.0
        #c[1] = c[1] - matrix.shape[1]/2.0
        #c[2] = c[2] - matrix.shape[2]/2.0
        self.file_string += f"bpy.ops.object.volume_import(filepath=\'{filename}.vdb\', location=({c[0]},{c[1]},{c[2]}))\n"
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += '%s = bpy.context.object\n' % (name)
        matl_name = f"{name}_color"
        if color is None:
            color_attribute = 'color'
        else:
            color_attribute = None
        if density_ramp != 'flat':
            density_attribute = density
        else:
            density_attribute = None
        density_multiplier = density_multiplier
        self.principled_volume(name=matl_name,
                               color=color, color_attribute=color_attribute, density_attribute=density_attribute,
                               density_multiplier=density_multiplier)
        self.set_matl(obj=name, matl=matl_name)


    def rpp(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None, c=None,
            l=None, name="rpp", color=None, alpha=1.0, verts=None,
                    emis=False, layer='render', **kwargs):
        self.name = name
        if (x1 is not None) and (x2 is not None) and (y1 is not None) and \
            (y2 is not None) and (z1 is not None) and (z2 is not None):
            c = [np.mean([x1, x2]), np.mean([y1, y2]), np.mean([z1, z2])]
            l = [x2 - x1, y2 - y1, z2 - z1]
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
            self.file_string += 'bpy.context.collection.objects.link(%s)\n' % name
            self.file_string += 'verts = %s\n' % repr(verts)
            self.file_string += 'faces = [(0,1,3,2), (4,5,7,6), (0,1,5,4), (2,3,7,6), (1,3,7,5), (0,2,6,4)]\n'
            self.file_string += 'mesh.from_pydata(verts, [], faces)\n'
            self.file_string += 'mesh.update(calc_edges=True)\n'
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def plane(self, x1=None, x2=None, y1=None, y2=None, z1=None, z2=None,
              c=None, l=None, name="plane", color=None, alpha=1.0, verts=None,
              emis=False, image=None, layer='render', **kwargs):
        self.name = name
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
            self.file_string += 'bpy.ops.mesh.primitive_plane_add()\n'
            self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
            self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
            self.file_string += 'bpy.ops.object.transform_apply(scale=True)\n'
            self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
            self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'
            
            self.file_string += 'bpy.context.object.rotation = (%15.10e, %15.10e, %15.10e)\n' % (r[0], r[1], r[2])
            self.file_string += 'bpy.ops.object.transform_apply(rotation=True)\n'
            self.file_string += '%s = bpy.context.object\n' % (name)
            if layer == 'render':
                self.file_string += 'fg.objects.link({name})\n'.format(name=name)
            elif layer == 'trans':
                self.file_string += 'tg.objects.link({name})\n'.format(name=name)
            self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif image is not None:
            self.image(name="%s_color" % name, fname=image, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)

    def scatter(self, arr, color=None, alpha=1.0, layer='render', r=0.01):
        #self.rpp(c=arr[0], l=[0.01, 0.01, 0.01], name='sphere', color=color, alpha=alpha)
        ri = np.random.randint(1E9)
        self.file_string += 'bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)\n'
        meanx = np.mean(arr[:, 0])
        meany = np.mean(arr[:, 1])
        meanz = np.mean(arr[:, 2])
        firstx = arr[0, 0]
        firsty = arr[0, 1]
        firstz = arr[0, 2]
        self.sph(c=arr[0, :], r=r, name='sphere%d' % ri, color=color, alpha=alpha, layer=layer)
        self.file_string += 'arr = [[%e, %e, %e],\n' % (arr[1, 0], arr[1, 1], arr[1, 2])
        for row in arr[2:]:
            self.file_string += '      [%e, %e, %e],\n' % (row[0], row[1], row[2])
        self.file_string += '      ]\n'
        self.file_string += 'bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)\n'
        self.file_string += 'for i, row in enumerate(arr[1:]):\n'
        self.file_string += '    ob = sphere%d.copy()\n' % ri
        #self.file_string += '    bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)\n'
        self.file_string += '    scene.objects.link(ob)\n'
        #self.file_string += f'    ob.location.x = row[0] - arr[0][0] - {meanx}\n'
        #self.file_string += f'    ob.location.y = row[1] - arr[0][1] - {meany}\n'
        #self.file_string += f'    ob.location.z = row[2] - arr[0][2] - {meanz}\n'
        self.file_string += f'    ob.location.x = row[0] - {firstx}\n'
        self.file_string += f'    ob.location.y = row[1] - {firsty}\n'
        self.file_string += f'    ob.location.z = row[2] - {firstz}\n'
        #self.file_string += '    bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '    bpy.context.scene.update()\n'
        #self.file_string += '    bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)\n'
        if layer == 'render':
            self.file_string += 'fg.objects.link(ob)\n'
        elif layer == 'trans':
            self.file_string += 'tg.objects.link(ob)\n'
        self.file_string += 'bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)\n'
        #self.file_string += 'bpy.context.scene.update()\n'
        #self.file_string += "{name} = bpy.context.object\n".format(name=name)

    def sph(self, c=None, r=None, name="sph", color=None, alpha=1.0,
            emis=False, layer='render', subd=4, **kwargs):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=%d)\n' % (subd)
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (r, r, r)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, alpha=alpha, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def gq(self, A=0.0, B=0.0, C=0.0, D=0.0, E=0.0, F=0.0, G=0.0, H=0.0, J=0.0,
           K=0.0, name="gq", color=None, alpha=1.0, emis=False, layer='render',
           **kwargs):
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
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def rcc(self, c=None, r=None, h=None, name="rcc", color=None, direction='z',
            alpha=1.0, emis=False, layer='render', **kwargs):
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
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def pyramid(self, c=(0., 0., 0.), tw=None, bw=None, h=None, name="pyramid",
                color=None, direction='z', alpha=1.0, emis=False, layer='render',
                rotation=None, **kwargs):
        self.name = name
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
        c = list(c)
        #c[direction] += h/2.
        self.file_string += f"verts = [\n"
        self.file_string += f"         ({- tw/2.0}, {- tw/2.0}, {h/2.0}),\n"
        self.file_string += f"         ({tw/2.0}, {- tw/2.0}, {h/2.0}),\n"
        self.file_string += f"         ({tw/2.0}, {tw/2.0}, {h/2.0}),\n"
        self.file_string += f"         ({- tw/2.0}, {tw/2.0}, {h/2.0}),\n"
        self.file_string += f"         ({- bw/2.0}, {- bw/2.0}, {- h/2.0}),\n"
        self.file_string += f"         ({bw/2.0}, {- bw/2.0}, {- h/2.0}),\n"
        self.file_string += f"         ({bw/2.0}, {bw/2.0}, {- h/2.0}),\n"
        self.file_string += f"         ({- bw/2.0}, {bw/2.0}, {- h/2.0}),\n"
        self.file_string += f"        ]\n"
        self.file_string += f"faces = [(0, 1, 2, 3), (4, 5, 1, 0),\n"
        self.file_string += f"         (5, 6, 2, 1), (6, 7, 3, 2),\n"
        self.file_string += f"         (7, 4, 0, 3), (4, 5, 6, 7)]\n"
        self.file_string += f"edges = []\n"
        self.file_string += f"mesh = bpy.data.meshes.new(\"{name}_mesh\")\n"
        self.file_string += f"mesh.from_pydata(verts, edges, faces)\n"
        self.file_string += f"obj = bpy.data.objects.new(\"{name}\", mesh)\n"
        self.file_string += f"obj.location = ({c[0]}, {c[1]}, {c[2]})\n"
        self.file_string += f"scene = bpy.context.scene\n"
        self.file_string += f"scene.objects.link(obj)\n"
        self.file_string += 'obj.select = True\n'
        self.file_string += 'scene.objects.active = obj\n'
        self.file_string += f"{name} = bpy.context.object\n"
        self.file_string += 'bpy.context.object.rotation_euler = '
        self.file_string += '(%15.10e, %15.10e, %15.10e)\n' % \
            (rotation[0], rotation[1], rotation[2])
        self.file_string += 'bpy.ops.object.transform_apply(rotation=True)\n'
        self.file_string += 'bpy.context.object.location = '
        self.file_string += '(%15.10e, %15.10e, %15.10e)\n' % \
            (c[0], c[1], c[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def cone(self, c=(0., 0., 0.), r1=None, r2=None, h=None, name="cone",
             color=None, direction='z', alpha=1.0, emis=False, layer='render',
             rotation=None, **kwargs):
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
        if layer == 'render':
            self.file_string += 'fg.objects.link({name})\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name})\n'.format(name=name)
        self.file_string += "{name} = bpy.context.object\n".format(name=name)
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)

    def subtract(self, left, right, unlink=True):
        self.boolean(left=left, right=right, operation="DIFFERENCE",
                     unlink=unlink)

    def union(self, left, right, unlink=True):
        self.boolean(left=left, right=right, operation="UNION",
                     unlink=unlink)

    def intersect(self, left, right, unlink=True):
        self.boolean(left=left, right=right, operation="INTERSECT",
                     unlink=unlink)

    def explode(self, name, c, l):
        if isinstance(l, float):
            l = (l, l, l)
        self.file_string += 'scene.objects.active = %s\n' % name
        self.file_string += 'o = bpy.context.object\n'
        self.file_string += 'vcos = [ o.matrix_world * v.co for v in o.data.vertices ]\n'
        self.file_string += 'findCenter = lambda l: ( max(l) + min(l) ) / 2\n'
        self.file_string += 'x,y,z  = [ [ v[i] for v in vcos ] for i in range(3) ]\n'
        self.file_string += 'center = [ findCenter(axis) for axis in [x,y,z] ]\n'
        self.file_string += 'ds = (center[0] - %15.10e, center[1] - %15.10e, center[2] - %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 's = (%15.10e * ds[0], %15.10e * ds[1], %15.10e * ds[2])\n' % (l[0], l[1], l[2])
        self.file_string += 'bpy.context.object.location = s\n'
        #self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (axis[0], axis[1], axis[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True)\n'

    def boolean(self, left, right, operation, unlink=True):
        if operation == "DIFFERENCE":
            op = 'less'
        elif operation == "UNION":
            op = 'plus'
        elif operation == "INTERSECT":
            op = 'inter'
        name = left + "_" + operation.lower() + "_" + right
        self.file_string += 'bpy.context.collection.objects.active = %s\n' % (left)
        self.file_string += '%s = bpy.context.object.modifiers.new(type="BOOLEAN", name="%s")\n' % (name, left + "_" + operation.lower() + "_" + right)
        self.file_string += '%s.operation = "%s"\n' % (name, operation)
        self.file_string += '%s.object = %s\n' % (name, right)
        #self.file_string += '%s.double_threshold = 0.1\n' % name
        self.file_string += '%s.solver = "CARVE"\n' % (name)
        self.file_string += 'bpy.ops.object.modifier_apply(apply_as="DATA", modifier="%s")\n' % (left + "_" + operation.lower() + "_" + right)
        if unlink:
            self.file_string += 'bpy.context.collection.objects.unlink(%s)\n' % right
        self.file_string += 'bpy.context.collection.objects.active = bpy.context.object\n'
        self.file_string += '%s = bpy.context.object\n' % (left + "_" + op + "_" + right)

    def unlink(self, name):
        self.file_string += 'bpy.context.collection.objects.unlink(%s)\n' % name

    def principled_volume(self, name="PVol", color='#555555', alpha=1.0, color_attribute=None, density_attribute=None, **kwargs):
        self.file_string += '%s = bpy.data.materials.new("%s")\n' % (name, name)
        print(color, color_attribute)
        rgb = Color(color).rgb
        self.file_string += '%s.use_nodes = True\n' % name
        self.file_string += 'nodes = %s.node_tree.nodes\n' % name
        self.file_string += 'for key in nodes.values():\n'
        self.file_string += '    nodes.remove(key)\n'
        self.file_string += 'links = %s.node_tree.links\n' % name
        self.file_string += '%s_volp = nodes.new("ShaderNodeVolumePrincipled")\n' % name
        self.file_string += f'{name}_volp.inputs[1].default_value = \'color\'\n'
        self.file_string += f'{name}_volp.inputs[3].default_value = \'density\'\n'
        self.file_string += '%s_material_output = nodes.new("ShaderNodeOutputMaterial")\n' % name
        self.file_string += 'links.new(%s_volp.outputs[0], %s_material_output.inputs[1])\n' % (name, name)
        self.file_string += 'for node in nodes:\n'
        self.file_string += '    node.update()\n'
        #self.file_string += '%s = flat\n' % name

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

    def emis(self, name="Source", color="#555555", alpha=1.0, volume=False,
             emittance=1.0, **kwargs):
        rgb = Color(color).rgb
        self.file_string += 'source = bpy.data.materials.new("%s")\n' % name
        self.file_string += 'source.use_nodes = True\n'
        self.file_string += 'nodes = source.node_tree.nodes\n'
        self.file_string += 'for key in nodes.values():\n'
        self.file_string += '    nodes.remove(key)\n'
        self.file_string += 'links = source.node_tree.links\n'
        self.file_string += '%s_e = nodes.new(type="ShaderNodeEmission")\n' % name
        self.file_string += '%s_e.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (name, rgb[0], rgb[1], rgb[2], alpha)
        self.file_string += '%s_e.inputs[1].default_value = %6.4f\n' % (name, emittance)
        self.file_string += '%s_glass = nodes.new("ShaderNodeBsdfTransparent")\n' % name
        self.file_string += '%s_mix = nodes.new("ShaderNodeMixShader")\n' % name
        self.file_string += 'links.new(%s_e.outputs[0], %s_mix.inputs[1])\n' % (name, name)
        self.file_string += 'links.new(%s_glass.outputs[0], %s_mix.inputs[2])\n' % (name, name)
        self.file_string += '%s_mix.inputs[0].default_value = %6.4f\n' % (name, 1.0 - alpha)
        self.file_string += '%s_material_output = nodes.new("ShaderNodeOutputMaterial")\n' % name
        self.file_string += 'links.new(%s_mix.outputs[0], %s_material_output.inputs[0])\n' % (name, name)
        self.file_string += 'for node in nodes:\n'
        self.file_string += '    node.update()\n'
        self.file_string += '%s = source\n' % name

    def trans(self, name="Trans", color="#555555"):
        self.file_string += 'trans = bpy.data.materials.new("%s")\n' % name
        rgb = Color(color).rgb
        self.file_string += 'trans.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2])
        self.file_string += '%s = trans\n' % name

    def line3d(self, xs, ys, zs, name='line', bevel=1.0, color=None, alpha=1.0,
               emis=False, layer='render', **kwargs):
        self.file_string += "render_layers = bpy.context.scene.render.layers\n"
        self.file_string += "print([rl.name for rl in render_layers])\n"
        self.file_string += "verts = [\n"
        for i, (x, y, z) in enumerate(zip(xs, ys, zs)):
            self.file_string += \
                "         ({x}, {y}, {z}),\n".format(x=x, y=y, z=z)
        self.file_string += "         ]\n"
        self.file_string += "edges = [\n"
        pts = range(len(xs))
        for i, j in zip(pts[:-1], pts[1:]):
            self.file_string += "         [{i}, {j}],\n".format(i=i, j=j)
        self.file_string += "         ]\n"
        self.file_string += "{name}_mesh = bpy.data.meshes.new(\"{name}_Data\")\n".format(name=name)
        self.file_string += "{name}_mesh.from_pydata(verts, edges, [])\n".format(name=name)
        self.file_string += "{name}_mesh.update()\n".format(name=name)
        self.file_string += "{name}_object = bpy.data.objects.new(\"{name}\", {name}_mesh)\n".format(name=name)
        self.file_string += "{name}_object.data = {name}_mesh\n".format(name=name)
        self.file_string += "scene = bpy.context.scene\n".format(name=name)
        self.file_string += "scene.objects.link({name}_object)\n".format(name=name)
        self.file_string += "{name}_object.select = True\n".format(name=name)
        self.file_string += "bpy.context.collection.objects.active = {name}_object\n".format(name=name)
        self.file_string += "bpy.ops.object.convert(target=\"CURVE\")\n".format(name=name)
        self.file_string += "{name}_object.data.fill_mode = \"FULL\"\n".format(name=name)
        self.file_string += "{name}_object.data.bevel_depth = {bevel}\n".format(name=name, bevel=bevel)
        #if layer == 'render':
        #    self.file_string += "{name}_object.layers[0]= True\n".format(name=name)
        #    self.file_string += "for i in range(2):\n"
        #    self.file_string += "\t{name}_object.layers[i] = (i == 0)\n".format(name=name)
        #elif layer == 'trans':
        #    self.file_string += "{name}_object.layers[1] = True\n".format(name=name)
        #    self.file_string += "for i in range(2):\n"
        #    self.file_string += "\t{name}_object.layers[i] = (i == 1)\n".format(name=name)
        if layer == 'render':
            self.file_string += 'fg.objects.link({name}_object)\n'.format(name=name)
        elif layer == 'trans':
            self.file_string += 'tg.objects.link({name}_object)\n'.format(name=name)
        self.file_string += "{name}_object = bpy.context.object\n".format(name=name)
        name = name + '_object'
        if color is not None and not emis:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)
        elif color is not None and emis:
            self.emis(name="%s_color" % name, color=color, **kwargs)
            self.set_matl(obj=name, matl="%s_color" % name)


    def image(self, name="Image", fname=None, alpha=1.0, volume=False,
              color="#ffffff", layer='render'):
        rgb = Color(color).rgb
        self.file_string += 'source = bpy.data.materials.new("%s")\n' % name
        self.file_string += 'source.use_nodes = True\n'
        self.file_string += 'nodes = source.node_tree.nodes\n'
        self.file_string += 'for key in nodes.values():\n'
        self.file_string += '    nodes.remove(key)\n'
        self.file_string += 'links = source.node_tree.links\n'
        self.file_string += '%s_e = nodes.new(type="ShaderNodeEmission")\n' % name
        self.file_string += '%s_e.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (name, rgb[0], rgb[1], rgb[2], 1.0)
        self.file_string += '%s_e.inputs[1].default_value = 5.0\n' % name
        self.file_string += '%s_image = bpy.data.images.load(\'%s\')\n' % (name, fname)
        self.file_string += '%s_node_texture = nodes.new(type=\'ShaderNodeTexImage\')\n' % name
        self.file_string += '%s_node_texture.image = %s_image\n' % (name, name)
        self.file_string += '%s_glass = nodes.new("ShaderNodeBsdfTransparent")\n' % name
        self.file_string += '%s_mix = nodes.new("ShaderNodeMixShader")\n' % name
        self.file_string += 'links.new(%s_node_texture.outputs[0], %s_mix.inputs[1])\n' % (name, name)
        self.file_string += 'links.new(%s_glass.outputs[0], %s_mix.inputs[2])\n' % (name, name)
        self.file_string += '%s_mix.inputs[0].default_value = %6.4f\n' % (name, 1.0 - alpha)
        self.file_string += '# Make a material output\n'
        self.file_string += '%s_material_output = nodes.new("ShaderNodeOutputMaterial")\n' % name
        self.file_string += 'links.new(%s_mix.outputs[0], %s_material_output.inputs[0])\n' % (name, name)
        self.file_string += '# link from the shader and displacement groups to the outputs\n'
        if volume:
            self.file_string += 'links.new(%s_mix.outputs[0], %s_material_output.inputs[1])\n' % (name, name)
        else:
            self.file_string += 'links.new(%s_mix.outputs[0], %s_material_output.inputs[0])\n' % (name, name)
        self.file_string += 'for node in nodes:\n'
        self.file_string += '    node.update()\n'
        self.file_string += '%s = source\n' % name

    def set_matl(self, obj=None, matl=None):
        # self.file_string += 'obj = bpy.context.collection.objects.get("%s")\n' % obj
        # self.file_string += 'bpy.context.collection.objects.active = obj\n'
        self.file_string += '%s.active_material = %s\n' % (obj, matl)

    def split_scene(self, filename):
        newscene = copy.deepcopy(self)
        newscene.filename = filename
        return newscene

    def draft(self, i=True):
        self._draft = i
        return self

    def cutaway(self, c=(0., 0., 0.), l=(0., 0., 0.),
                exclude='asdlfjkals;djkfasdlfj'):
        # first, create an extrude that will cutaway
        name = 'cutaway{iid}'.format(iid=cutawayid.val)
        cutawayid.val += 1
        self.file_string += 'exclude = "%s"\n' % (exclude)
        self.file_string += 'bpy.ops.mesh.primitive_cube_add()\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        self.file_string += 'bpy.context.collection.objects.active = bpy.data.objects[0]\n'
        self.file_string += 'for ob in bpy.data.objects:\n'
        self.file_string += '    bpy.context.collection.objects.active = ob\n'
        self.file_string += '    if ob.name != "%s" and exclude not in ob.name:\n' % name
        self.file_string += '        obname = ob.name\n'
        self.file_string += '        try:\n'
        self.file_string += '            _cutaway = bpy.context.object.modifiers.new(type="BOOLEAN", name=obname + "cut")\n'
        self.file_string += '            _cutaway.operation = "DIFFERENCE"\n'
        self.file_string += '            _cutaway.object = %s\n' % name
        self.file_string += '            _cutaway.solver = "CARVE"\n'
        self.file_string += '            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=obname + "cut")\n'
        self.file_string += '        except AttributeError:\n'
        self.file_string += '            pass\n'
        self.file_string += 'bpy.context.collection.objects.unlink(%s)\n' % name
        self.file_string += 'bpy.context.collection.objects.active = bpy.context.object\n'

    def look_at(self, target=None):
        self.file_string += 'camera_track.target = (bpy.data.objects["%s"])\n' % target

    def peek(self, camera_location=(500, 500, 300), c=(0., 0., 0.),
             l=(250., 250., 250.), fit=True, filename=None,
             perspective=True, **kwargs):
        """Render an opengl example of the 3d scene.

        :param tuple camera_location: location of the camera.
        :param tuple c: scene center location
        :param tuple l: scene etents emanating from center
        :param bool fit: whether to fit the scene or not
        :param str filename: a file path to move the rendered peek to
        """
        res = [640, 480]
        samples = 10
        resw = res[0]
        resh = res[1]
        self.old_file_string = self.file_string
        self.file_string += 'bpy.context.collection.objects.active.select = False\n'
        self.file_string += 'bpy.ops.object.visual_transform_apply()\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.engine = "CYCLES"\n'
        self.file_string += 'render = bpy.data.scenes["Scene"].render\n'
        self.file_string += 'world = bpy.data.worlds["World"]\n'
        self.file_string += 'world.use_nodes = True\n'
        self.file_string += 'empty = bpy.data.objects.new("Empty", None)\n'
        self.file_string += 'bpy.context.collection.objects.link(empty)\n'
        #self.file_string += 'empty.empty_draw_size = 1\n'
        #self.file_string += 'empty.empty_draw_type = "CUBE"\n'
        self.file_string += 'bpy.data.objects["Empty"].location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.data.objects["Empty"].scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'empty = bpy.data.objects["Empty"]\n'
        self.file_string += 'camera = bpy.data.objects["Camera"]\n'
        self.file_string += 'camera.location = (%6.4f, %6.4f, %6.4f)\n' % \
            (camera_location[0], camera_location[1], camera_location[2])
        self.file_string += 'bpy.data.cameras[camera.name].clip_end = 10000.0\n'
        self.file_string += 'bpy.data.cameras[camera.name].clip_start = 0.0\n'
        if not perspective:
            self.file_string += 'bpy.data.cameras[camera.name].type = "ORTHO"\n'
        self.file_string += 'camera_track = camera.constraints.new("TRACK_TO")\n'
        self.file_string += 'camera_track.track_axis = "TRACK_NEGATIVE_Z"\n'
        self.file_string += 'camera_track.up_axis = "UP_Y"\n'
        self.look_at(target="Empty")
        self.file_string += 'bpy.data.scenes["Scene"].render.filepath = "%s" + ".png"\n' % self.filename
        self.file_string += 'bpy.ops.wm.save_as_mainfile(filepath="%s.blend")\n' % self.filename
        self.file_string += 'area = next(area for area in bpy.context.screen.areas if area.type == \'VIEW_3D\')\n'
        self.file_string += 'area.spaces[0].region_3d.view_perspective = \'CAMERA\'\n'
        self.file_string += 'bpy.ops.render.opengl( write_still=True )\n'
        self.file_string += 'modelview_matrix = camera.matrix_world.inverted()\n'
        self.file_string += 'proj_matrix = camera.calc_matrix_camera(bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph)\n'
        self.file_string += 'print(proj_matrix.shape)\n'
        self.file_string += 'projection_matrix = camera.calc_matrix_camera(\n'
        self.file_string += '        render.resolution_x / 2.0,\n'
        self.file_string += '        render.resolution_y / 2.0,\n'
        self.file_string += '        render.pixel_aspect_x,\n'
        self.file_string += '        render.pixel_aspect_y,\n'
        self.file_string += '        )\n'
        self.file_string += 'P, K, RT = get_3x4_P_matrix_from_blender(camera)\n'
        self.file_string += 'import os\n'
        self.file_string += 'proj_matrix = "[[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e]]" % (P[0][0], P[0][1], P[0][2], P[0][3], P[1][0], P[1][1], P[1][2], P[1][3], P[2][0], P[2][1], P[2][2], P[2][3])\n'
        self.file_string += 'os.system("convert %s.png -set proj_matrix \'%%s\' %s.png" %% proj_matrix)\n' % (self.filename, self.filename)
        self.file_string += 'bpy.ops.wm.quit_blender()\n'

        if sys.platform == "darwin":
            blender_path = '/Applications/blender.app/Contents/MacOS/blender'
        else:
            blender_path = 'blender'
        with open(self.filename + '.py', 'w') as f:
            f.write(self.file_string)
            cmd = "{bpath} --python {fname}.py".format(bpath=blender_path, fname=self.filename)
            #print cmd
            #print os.popen('cat %s' % self.filename + '.py').read()
        render = subprocess.Popen(cmd, shell=True)
        block = True
        if block:
            render.communicate()
        if filename is not None and block:
            shutil.copy(self.filename + ".png", filename)
            proj_matrix = os.popen("identify -verbose %s | grep proj_matrix" % filename).read()
            exec(proj_matrix.replace(" ", "").replace(":", "="))
            self.proj_matrix = proj_matrix
            self.filename = filename.replace('.png.png', '.png')
        self.has_run = True
        self.show()
        self.has_run = False
        self.old_file_string = self.file_string

    def render(self, camera_location=(500, 500, 300), c=(0., 0., 0.),
               l=(250., 250., 250.), render=True, fit=True, samples=20,
               res=[1920, 1080], draft=False, freestyle=True,
               perspective=True, pscale=350, bg_lum=1.0, **kwargs):
        if self._draft or draft:
            res = [640, 480]
            samples = 10
        resw = res[0]
        resh = res[1]
        self.file_string += 'try:\n'
        self.file_string += '    bpy.context.collection.objects.active.select = False\n'
        self.file_string += 'except AttributeError:\n'
        self.file_string += '    pass\n'
        self.file_string += 'bpy.ops.object.visual_transform_apply()\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.engine = "CYCLES"\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_x = %d * 2.\n' % resw
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_y = %d * 2.\n' % resh
        self.file_string += 'render = bpy.data.scenes["Scene"].render\n'
        self.file_string += 'world = bpy.data.worlds["World"]\n'
        self.file_string += 'world.use_nodes = True\n'
        self.file_string += 'empty = bpy.data.objects.new("Empty", None)\n'
        self.file_string += 'bpy.context.collection.objects.link(empty)\n'
        #self.file_string += 'empty.empty_draw_size = 1\n'
        #self.file_string += 'empty.empty_draw_type = "CUBE"\n'
        self.file_string += 'bpy.data.objects["Empty"].location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.data.objects["Empty"].scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'empty = bpy.data.objects["Empty"]\n'
        self.file_string += 'camera = bpy.data.objects["Camera"]\n'
        self.file_string += 'camera.location = (%6.4f, %6.4f, %6.4f)\n' % \
            (camera_location[0], camera_location[1], camera_location[2])
        self.file_string += 'bpy.data.cameras[camera.name].clip_end = 10000.0\n'
        self.file_string += 'bpy.data.cameras[camera.name].clip_start = 0.0\n'
        if not perspective:
            self.file_string += 'bpy.data.cameras[camera.name].type = "ORTHO"\n'
            self.file_string += f'bpy.data.cameras[camera.name].ortho_scale = {pscale}\n'
        self.file_string += 'camera_track = camera.constraints.new("TRACK_TO")\n'
        self.file_string += 'camera_track.track_axis = "TRACK_NEGATIVE_Z"\n'
        self.file_string += 'camera_track.up_axis = "UP_Y"\n'
        self.look_at(target="Empty")
        self.file_string += '# changing these values does affect the render.\n'
        self.file_string += 'bpy.data.worlds[\'World\'].use_nodes = True\n'
        self.file_string += 'bpy.data.worlds[\'World\'].node_tree.nodes[\'Background\'].inputs[0].default_value[:3] = (1,1,1)\n'
        self.file_string += f'bpy.data.worlds[\'World\'].node_tree.nodes[\'Background\'].inputs[1].default_value = {bg_lum}\n'
        self.file_string += 'bg = world.node_tree.nodes["Background"]\n'
        self.file_string += 'bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)\n'
        self.file_string += f'bg.inputs[1].default_value = {bg_lum}\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.filepath = "%s" + ".png"\n' % self.filename
        self.file_string += 'bpy.context.scene.render.use_freestyle = %s\n' % freestyle
        self.file_string += 'bpy.data.scenes["Scene"].view_layers[0].use_pass_normal = True\n'
        #self.file_string += 'print(bpy.data.scenes["Scene"].layers)\n'
        #self.file_string += 'print(bpy.data.scenes["Scene"].layers[0])\n'
        #self.file_string += 'print(dir(bpy.data.scenes["Scene"].render))\n'
        #self.file_string += 'sceneR = bpy.context.scene\n'
        #self.file_string += 'freestyle = sceneR.render.layers.active.freestyle_settings\n'
        self.file_string += 'linestyle = bpy.data.scenes["Scene"].view_layers[0].freestyle_settings.linesets[0]\n'
        #self.file_string += 'sceneR.render.use_freestyle = True\n'
        #self.file_string += 'sceneR.svg_export.use_svg_export = True\n'
        #self.file_string += 'freestyle.use_smoothness = True\n'
        #self.file_string += 'freestyle.use_culling = True\n'
        #self.file_string += 'linestyle.select_by_visibility = True\n'
        #self.file_string += 'linestyle.select_by_edge_types = True\n'
        #self.file_string += 'linestyle.visibility = "RANGE"\n'
        #self.file_string += 'linestyle.select_silhouette = True\n'
        #self.file_string += 'print(dir(linestyle))\n'
        #self.file_string += 'linestyle.select_by_group = True\n'
        #self.file_string += 'linestyle.group = fg\n'
        #self.file_string += 'linestyle.group_negation = tg\n'
        #self.file_string += 'bpy.data.scenes["Scene"].render.layers["RenderLayer"].layers[0].use_freestyle = True\n'
        #self.file_string += 'print(bpy.context.scene.render.layers)\n'
        #self.file_string += 'raise ValueError("A very specific bad thing happened.")\n'
        #self.file_string += 'bpy.data.scenes["Scene"].layers[1] = True\n'
        #self.file_string += 'bpy.data.scenes["Scene"].render.layers["RenderLayer"].layers[1].use_freestyle = False\n'
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
        self.file_string += 'bpy.data.scenes["Scene"].render.film_transparent = True\n'
        self.file_string += 'bpy.ops.wm.save_as_mainfile(filepath="%s.blend")\n' % self.filename
        if render:
            self.file_string += 'bpy.ops.render.render( write_still=True )\n'
        self.file_string += 'modelview_matrix = camera.matrix_world.inverted()\n'
        self.file_string += 'print(dir(camera))\n'
        #self.file_string += 'projection_matrix = camera.calc_matrix_camera(\n'
        #self.file_string += '        bpy.data.scenes["Scene"].render.resolution_x / 2.0,\n'
        #self.file_string += '        bpy.data.scenes["Scene"].render.resolution_y / 2.0,\n'
        #self.file_string += '        bpy.data.scenes["Scene"].render.pixel_aspect_x,\n'
        #self.file_string += '        bpy.data.scenes["Scene"].render.pixel_aspect_y,\n'
        #self.file_string += '        )\n'

        self.file_string += 'proj_matrix = camera.calc_matrix_camera(bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph,\n'
        self.file_string += '                                        x = render.resolution_x / 2.0,\n'
        self.file_string += '                                        y = render.resolution_y / 2.0,\n'
        self.file_string += '                                        scale_x = render.pixel_aspect_x,\n'
        self.file_string += '                                        scale_y = render.pixel_aspect_y,)\n'
        #self.file_string += 'proj_matrix = camera.calc_matrix_camera(bpy.data.scenes["Scene"].view_layers["View Layer"].depsgraph
        self.file_string += 'P = proj_matrix @ modelview_matrix\n'
        #self.file_string += '_P, K, RT = get_3x4_P_matrix_from_blender(camera)\n'
        self.file_string += 'persp_matrix = projection_matrix(camera.data)\n'
        #self.file_string += 'print(persp_matrix)\n'
        #self.file_string += 'P = persp_matrix\n'
        self.file_string += 'import os\n'
        self.file_string += 'proj_matrix =  f"[[{P[0][0]:15.2e}, {P[0][1]:15.2e}, {P[0][2]:15.2e}, {P[0][3]:15.2e}],"\n'
        self.file_string += 'proj_matrix +=  f"[{P[1][0]:15.2e}, {P[1][1]:15.2e}, {P[1][2]:15.2e}, {P[1][3]:15.2e}],"\n'
        self.file_string += 'proj_matrix +=  f"[{P[2][0]:15.2e}, {P[2][1]:15.2e}, {P[2][2]:15.2e}, {P[2][3]:15.2e}],"\n'
        self.file_string += 'proj_matrix +=  f"[{P[3][0]:15.2e}, {P[3][1]:15.2e}, {P[3][2]:15.2e}, {P[3][3]:15.2e}]]"\n'
        if render:
            self.file_string += f'os.system(f"convert {self.filename}.png -set proj_matrix \'{{proj_matrix}}\' {self.filename}.png")\n'

    def open(self, blend=None):
        if '.blend' not in blend:
            blend = blend + '.blend'
        self.file_string += 'bpy.ops.wm.open_mainfile(filepath="{blend}")\n'.format(blend=blend)

    def run(self, filename=None, block=True, **kwargs):
        """ Opens a blender instance and runs the generated model rendering
        """
        self.render(**kwargs)
        if sys.platform == "darwin":
            blender_path = '/Applications/Blender.app/Contents/MacOS/Blender' # '/Applications/blender.app/Contents/MacOS/blender'
        else:
            blender_path = 'blender'
        with open(self.filename + '.py', 'w') as f:
            f.write(self.file_string)
            cmd = "{bpath} --background --python {fname}.py".format(bpath=blender_path, fname=self.filename)
            #print cmd
            #print os.popen('cat %s' % self.filename + '.py').read()
        render = subprocess.Popen(cmd, shell=True)
        if block:
            render.communicate()
        if 'render' in kwargs:
            rendered = kwargs['render']
        else:
            rendered = True
        if filename is not None and rendered and block:
            shutil.copy(self.filename + ".png", filename)
            proj_matrix = os.popen("identify -verbose %s | grep proj_matrix" % filename).read()
            exec(proj_matrix.replace(" ", "").replace(":", "="))
            self.proj_matrix = proj_matrix
        self.has_run = True



    def show(self):
        """ Opens the image if it has been rendered
        """
        if self.has_run:
            iid = random.randint(0, 1E9)
            path = os.path.join(self.path, self.filename)
            homepath = os.path.expanduser('~')
            path = os.path.relpath(path, homepath)
            print (path)
            html_str = '<img src="/files/{fname}.png?{iid}"\/>'.format(fname=path, iid=iid)
            return display(HTML(html_str))
            cmd = "eog %s.png" % self.filename
            subprocess.Popen(cmd, shell=True)
