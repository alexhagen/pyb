import os
import subprocess
import tempfile
from colour import Color

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
        self.file_string += 'scene = bpy.context.scene\n'
        self.file_string += '# First, delete the default cube\n'
        self.file_string += 'bpy.ops.object.delete()\n'

    def sun(self, location=(10., 10., 10.), strength=10.0):
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
            l=None, name="rpp"):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_cube_add()\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (l[0]/2., l[1]/2., l[2]/2.)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)

    def sph(self, c=None, r=None, name="sph"):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=8)\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (r/2., r/2., r/2.)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)

    def rcc(self, c=None, r=None, h=None, name="rcc"):
        self.name = name
        self.file_string += 'bpy.ops.mesh.primitive_cylinder_add()\n'
        self.file_string += 'bpy.context.object.name = "%s"\n' % (name)
        self.file_string += 'bpy.context.object.location = (%15.10e, %15.10e, %15.10e)\n' % (c[0], c[1], c[2])
        self.file_string += 'bpy.context.object.scale = (%15.10e, %15.10e, %15.10e)\n' % (r/2., r/2., h/2.)
        self.file_string += 'bpy.ops.object.transform_apply(location=True, scale=True)\n'
        self.file_string += '%s = bpy.context.object\n' % (name)

    def flat(self, name="Flat", color='#555555'):
        self.file_string += 'flat = bpy.data.materials.new("%s")\n' % name
        rgb = Color(color).rgb
        self.file_string += 'flat.diffuse_color = (%6.4f, %6.4f, %6.4f)\n' % (rgb[0], rgb[1], rgb[2])
        self.file_string += '%s = flat\n' % name

    def set_matl(self, obj=None, matl=None):
        self.file_string += 'obj = bpy.context.scene.objects.get("%s")\n' % obj
        self.file_string += 'bpy.context.scene.objects.active = obj\n'
        self.file_string += '%s.active_material = %s\n' % (obj, matl)

    def render(self, location=(500., 500., 300.), target=None):
        self.file_string += 'bpy.context.scene.objects.active.select = False\n'
        self.file_string += 'camera = bpy.data.objects["Camera"]\n'
        self.file_string += 'camera.location = (%6.4f, %6.4f, %6.4f)\n' % (location[0], location[1], location[2])
        self.file_string += 'bpy.data.cameras[camera.name].clip_end = 1000.0\n'
        self.file_string += 'bpy.data.cameras[camera.name].clip_start = 0.0\n'
        self.file_string += 'camera_track = camera.constraints.new("TRACK_TO")\n'
        self.file_string += 'camera_track.track_axis = "TRACK_NEGATIVE_Z"\n'
        self.file_string += 'camera_track.up_axis = "UP_Y"\n'
        if target is not None:
            self.file_string += 'camera_track.target = (bpy.data.objects["%s"])\n' % target
        self.file_string += 'bpy.ops.object.visual_transform_apply()\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.engine = "CYCLES"\n'
        self.file_string += 'world = bpy.data.worlds["World"]\n'
        self.file_string += 'world.use_nodes = True\n'

        self.file_string += '# changing these values does affect the render.\n'
        self.file_string += 'bg = world.node_tree.nodes["Background"]\n'
        self.file_string += 'bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)\n'
        self.file_string += 'bg.inputs[1].default_value = 1.0\n'
        self.file_string += 'bpy.data.scenes["Scene"].render.filepath = "%s" + ".png"\n' % self.filename
        self.file_string += 'bpy.context.scene.render.use_freestyle = True\n'
        self.file_string += 'bpy.context.scene.cycles.use_progressive_refine = True\n'
        self.file_string += 'bpy.context.scene.cycles.samples = 50\n'
        self.file_string += 'bpy.context.scene.cycles.max_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.min_bounces = 3\n'
        self.file_string += 'bpy.context.scene.cycles.glossy_bounces = 4\n'
        self.file_string += 'bpy.context.scene.cycles.transmission_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.volume_bounces = 4\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_max_bounces = 16\n'
        self.file_string += 'bpy.context.scene.cycles.transparent_min_bounces = 8\n'
        self.file_string += 'bpy.context.scene.cycles.filter_glossy = 0.05\n'
        self.file_string += 'bpy.ops.render.render( write_still=True )\n'

    def run(self, **kwargs):
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
        self.has_run = True

    def show(self):
        """ Opens the image if it has been rendered
        """
        if self.has_run:
            cmd = "eog %s.png" % self.filename
            subprocess.Popen(cmd, shell=True)
