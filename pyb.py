import os
import subprocess
import tempfile
from colour import Color
import numpy as np
import shutil

class pyb(object):
    """ An object to save commands for blender 3d plotting and render
    """
    def __init__(self):
        self.file_string = ''
        #self.file = tempfile.NamedTemporaryFile(suffix=".py", prefix="brender_")
        self.filename = "brender_01"
        self.has_run = False
        self.scene_setup()

    def scene_setup(self):
        """ deletes the default cube and sets up a scene to be used to render in
        """
        self.file_string += 'import bpy\n'
        self.file_string += open('/home/ahagen/code/pyb/blender_mats_utils.py', 'r').read()
        self.file_string += 'scene = bpy.context.scene\n'
        self.file_string += '# First, delete the default cube\n'
        self.file_string += 'bpy.ops.object.delete()\n'

    def sun(self, location=(500., 500., 500.), strength=1.0):
        self.file_string += '# Now add a sun\n'
        self.file_string += 'lamp_data = bpy.data.lamps.new(name="Sun", type="SUN")\n'
        self.file_string += 'lamp_data.use_nodes = True\n'
        self.file_string += 'lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = %15.10e\n' % strength
        self.file_string += 'lamp_object = bpy.data.objects.new(name="Sun", object_data=lamp_data)\n'
        self.file_string += 'bpy.context.scene.objects.link(lamp_object)\n'
        self.file_string += 'lamp_object.location = (%15.10e, %15.10e, %15.10e)\n' % (location[0], location[1], location[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'

        self.file_string += 'lamp_object.select = True\n'
        self.file_string += 'bpy.context.scene.objects.active = lamp_object\n'

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

    def sph(self, c=None, r=None, name="sph", color=None, alpha=1.0):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=8)\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (r, r, r)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)

    def rcc(self, c=None, r=None, h=None, name="rcc", color=None, direction='z',
            alpha=1.0):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_cylinder_add()\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        rotation = [0., 0., 0.]
        if direction == 'z':
            direction = 2
        elif direction == 'y':
            direction = 1
        elif direction == 'x':
            direction = 0
        else:
            direction = int(direction)
        rotation[direction] = np.pi/2.
        axis = [r, r, r]
        c = list(c)
        axis[direction] = h/2.
        c[direction] += h/2.
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (axis[0], axis[1], axis[2])
        self.file_string += 'bpy.context.object.rotation_euler = (%15.10e, %15.10e, %15.10e)\n' % (rotation[0], rotation[1], rotation[2])
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True, rotation=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)
        if color is not None:
            self.flat(name="%s_color" % name, color=color, alpha=alpha)
            self.set_matl(obj=name, matl="%s_color" % name)

    def flat(self, name="Flat", color='#555555', alpha=1.0):
        self.file_string += 'flat = bpy.data.materials.new("%s")\n' % name
        rgb = Color(color).rgb
        self.file_string += 'flat.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2])
        if alpha < 1.0:
            self.file_string += 'flat.use_nodes = True\n'
            self.file_string += 'nodes = flat.node_tree.nodes\n'
            self.file_string += 'for key in nodes.values():\n'
            self.file_string += '    nodes.remove(key)\n'
            self.file_string += 'links = flat.node_tree.links\n'
            self.file_string += 'glass = nodes.new("ShaderNodeBsdfGlass")\n'
            self.file_string += 'glass.inputs[1].default_value = 0.0\n'
            self.file_string += 'glass.inputs[0].default_value = (%6.4f, %6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2], alpha)
            self.file_string += 'material_output = nodes.new("ShaderNodeOutputMaterial")\n'
            self.file_string += 'links.new(glass.outputs[0], material_output.inputs[0])\n'
            self.file_string += 'for node in nodes:\n'
            self.file_string += '    node.update()\n'
        self.file_string += '%s = flat\n' % name

    def trans(self, name="Trans", color="#555555"):
        self.file_string += 'trans = bpy.data.materials.new("%s")\n' % name
        rgb = Color(color).rgb
        self.file_string += 'trans.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2])
        self.file_string += '%s = trans\n' % name

    def set_matl(self, obj=None, matl=None):
        self.file_string += 'obj = bpy.context.scene.objects.get("%s")\n' % obj
        self.file_string += 'bpy.context.scene.objects.active = obj\n'
        self.file_string += '%s.active_material = %s\n' % (obj, matl)

    def look_at(self, target=None):
        self.file_string += 'camera_track.target = (bpy.data.objects["%s"])\n' % target

    def render(self, camera_location=(500, 500, 300), fit=True):
        self.file_string += 'bpy.context.scene.objects.active.select = False\n'
        self.file_string += 'bpy.ops.object.visual_transform_apply()\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.engine = "CYCLES"\n'
        self.file_string += 'render = bpy.data.scenes["Scene"].render\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_x = 1920. * 2.\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.resolution_y = 1080. * 2.\n'
        self.file_string += 'world = bpy.data.worlds["World"]\n'
        self.file_string += 'world.use_nodes = True\n'
        self.file_string += 'empty = bpy.data.objects.new("Empty", None)\n'
        self.file_string += 'bpy.context.scene.objects.link(empty)\n'
        self.file_string += 'empty.empty_draw_size = 1\n'
        self.file_string += 'empty.empty_draw_type = "CUBE"\n'
        c = (0., 100., 0.)
        l = (175.*2.,175.*2., 85.*2.)
        self.file_string += 'bpy.data.objects["Empty"].location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.data.objects["Empty"].scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'empty = bpy.data.objects["Empty"]\n'
        self.file_string += 'camera = bpy.data.objects["Camera"]\n'
        self.file_string += 'camera.location = (%6.4f, %6.4f, %6.4f)\n' % \
            (camera_location[0], camera_location[1], camera_location[2])
        self.file_string += 'bpy.data.cameras[camera.name].clip_end = 1000.0\n'
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
        # self.file_string += 'for object in bpy.data.objects:\n'
        # self.file_string += '    if object.type == "MESH":\n'
        # self.file_string += '        for edge in object.data.edges:\n'
        # self.file_string += '            edge.use_freestyle_mark = True\n'

        # self.file_string += '        #show the marked edges\n'
        # self.file_string += '        object.data.show_freestyle_edge_marks = True\n'
        # self.file_string += 'bpy.data.scenes["Scene"].FreestyleLineSet.select_crease = False\n'
        # self.file_string += 'bpy.data.scenes["Scene"].FreestyleLineSet.select_edge_mark = True\n'
        # self.file_string += 'bpy.context.scene.cycles.use_progressive_refine = True\n'
        self.file_string += 'bpy.context.scene.cycles.samples = 100\n'
        self.file_string += 'bpy.context.scene.cycles.max_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.min_bounces = 3\n'
        self.file_string += 'bpy.context.scene.cycles.glossy_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.transmission_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.volume_bounces = 4\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_max_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_min_bounces = 8\n'
        self.file_string += 'bpy.data.scenes["Scene"].cycles.film_transparent = True\n'
        self.file_string += 'bpy.context.scene.cycles.filter_glossy = 0.05\n'
        self.file_string += 'bpy.ops.wm.save_as_mainfile(filepath="%s.blend")\n' % self.filename
        self.file_string += 'bpy.ops.render.render( write_still=True )\n'
        self.file_string += 'modelview_matrix = camera.matrix_world.inverted()\n'
        self.file_string += 'projection_matrix = camera.calc_matrix_camera(\n'
        self.file_string += '        render.resolution_x,\n'
        self.file_string += '        render.resolution_y,\n'
        self.file_string += '        render.pixel_aspect_x,\n'
        self.file_string += '        render.pixel_aspect_y,\n'
        self.file_string += '        )\n'
        self.file_string += 'print(projection_matrix)\n'
        self.file_string += 'P, K, RT = get_3x4_P_matrix_from_blender(camera)\n'
        self.file_string += 'print(P)\n'
        self.file_string += 'with open("%s" + "_projection.py", "w") as f:\n' % self.filename
        self.file_string += '   f.write(repr(P))\n'

    def run(self, filename=None, **kwargs):
        """ Opens a blender instance and runs the generated model rendering
        """
        self.render(**kwargs)
        with open(self.filename + '.py', 'w') as f:
            f.write(self.file_string)
            cmd = "blender --background --python %s" % self.filename + '.py'
            print cmd
            print os.popen('cat %s' % self.filename + '.py').read()
        render = subprocess.Popen(cmd, shell=True)
        render.communicate()
        if filename is not None:
            shutil.copy(self.filename + ".png", filename)
            shutil.copy(self.filename + "_projection.py", filename.replace('.png', '') + "_projection.txt")
        execfile(self.filename + "_projection.py")
        self.has_run = True
        print P
        return P

    def show(self):
        """ Opens the image if it has been rendered
        """
        if self.has_run:
            cmd = "eog %s.png" % self.filename
            subprocess.Popen(cmd, shell=True)
