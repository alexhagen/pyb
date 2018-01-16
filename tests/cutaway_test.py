import bpy
import bpy
import bpy_extras
from mathutils import Matrix

#---------------------------------------------------------------
# 3x4 P matrix from Blender camera
#---------------------------------------------------------------

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camd.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal),
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal),
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm


    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v
    u_0 = resolution_x_in_px * scale / 2
    v_0 = resolution_y_in_px * scale / 2
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((alpha_u, skew,    u_0),
        (    0  , alpha_v, v_0),
        (    0  , 0,        1 )))
    return K

# Returns camera rotation and translation matrices from Blender.
#
# There are 3 coordinate systems involved:
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction
#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates
#         used in digital images)
#       - right-handed: positive z look-at direction
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Transpose since the rotation is object rotation,
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam * location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:
    T_world2bcam = -1*R_world2bcam * location

    # Build the coordinate transform matrix from world to computer vision camera
    R_world2cv = R_bcam2cv*R_world2bcam
    T_world2cv = R_bcam2cv*T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))
    return RT

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K*RT, K, RT

# ----------------------------------------------------------
# Alternate 3D coordinates to 2D pixel coordinate projection code
# adapted from http://blender.stackexchange.com/questions/882/how-to-find-image-coordinates-of-the-rendered-vertex?lq=1
# to have the y axes pointing up and origin at the top-left corner
def project_by_object_utils(cam, point):
    scene = bpy.context.scene
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, cam, point)
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
            int(scene.render.resolution_x * render_scale),
            int(scene.render.resolution_y * render_scale),
            )
    return Vector((co_2d.x * render_size[0], render_size[1] - co_2d.y * render_size[1]))
scene = bpy.context.scene
# First, delete the default cube
bpy.ops.object.delete()
bpy.ops.mesh.primitive_cube_add()
bpy.context.object.name = "rpp"
bpy.context.object.location = (5.0000000000e+00, 0.0000000000e+00, 0.0000000000e+00)
bpy.context.object.scale = (1.0000000000e+00, 2.5000000000e+00, 1.0000000000e+01)
bpy.ops.object.transform_apply(location=True, scale=True)
rpp = bpy.context.object
rpp_color = bpy.data.materials.new("rpp_color")
rpp_color.diffuse_color = (1.0000, 0.0000, 0.0000)
rpp.active_material = rpp_color
bpy.ops.mesh.primitive_cylinder_add(vertices=128)
bpy.context.object.name = "cyl1"
bpy.context.object.rotation_euler = (1.5707963268e+00, 0.0000000000e+00, 0.0000000000e+00)
bpy.ops.object.transform_apply(rotation=True)
bpy.context.object.location = (0.0000000000e+00, -5.0000000000e+00, 0.0000000000e+00)
bpy.context.object.scale = (2.5000000000e+00, 5.0000000000e+00, 2.5000000000e+00)
bpy.ops.object.transform_apply(location=True, scale=True)
cyl1 = bpy.context.object
cyl1_color = bpy.data.materials.new("cyl1_color")
cyl1_color.diffuse_color = (1.0000, 0.6000, 1.0000)
cyl1.active_material = cyl1_color
bpy.ops.mesh.primitive_cylinder_add(vertices=128)
bpy.context.object.name = "cyl2"
bpy.context.object.rotation_euler = (0.0000000000e+00, 0.0000000000e+00, 1.5707963268e+00)
bpy.ops.object.transform_apply(rotation=True)
bpy.context.object.location = (0.0000000000e+00, 1.0000000000e+01, 5.0000000000e+00)
bpy.context.object.scale = (2.0000000000e+00, 2.0000000000e+00, 5.0000000000e+00)
bpy.ops.object.transform_apply(location=True, scale=True)
cyl2 = bpy.context.object
cyl2_color = bpy.data.materials.new("cyl2_color")
cyl2_color.diffuse_color = (0.6000, 0.6000, 1.0000)
cyl2.active_material = cyl2_color
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4)
bpy.context.object.name = "sph"
bpy.context.object.location = (0.0000000000e+00, 0.0000000000e+00, 0.0000000000e+00)
bpy.context.object.scale = (5.0000000000e+00, 5.0000000000e+00, 5.0000000000e+00)
bpy.ops.object.transform_apply(location=True, scale=True)
sph = bpy.context.object
sph_color = bpy.data.materials.new("sph_color")
sph_color.diffuse_color = (0.6000, 1.0000, 0.6000)
sph.active_material = sph_color
bpy.ops.mesh.primitive_cube_add()
bpy.context.object.name = "cutaway1"
bpy.context.object.location = (0.0000000000e+00, 0.0000000000e+00, 2.0000000000e+00)
bpy.context.object.scale = (1.0000000000e+01, 1.0000000000e+01, 1.0000000000e+00)
bpy.ops.object.transform_apply(location=True, scale=True)
cutaway1 = bpy.context.object
bpy.context.scene.objects.active = bpy.data.objects[0]
for ob in bpy.data.objects:
    bpy.context.scene.objects.active = ob
    if ob.name != "cutaway1":
        obname = ob.name
        try:
            _cutaway = bpy.context.object.modifiers.new(type="BOOLEAN", name=obname + "cut")
            _cutaway.operation = "DIFFERENCE"
            _cutaway.object = cutaway1
            _cutaway.solver = "CARVE"
            bpy.ops.object.modifier_apply(apply_as="DATA", modifier=obname + "cut")
        except AttributeError:
            pass
bpy.context.scene.objects.unlink(cutaway1)
bpy.context.scene.objects.active = bpy.context.object
bpy.context.scene.objects.active.select = False
bpy.ops.object.visual_transform_apply()
bpy.data.scenes["Scene"].render.engine = "CYCLES"
render = bpy.data.scenes["Scene"].render
bpy.data.scenes["Scene"].render.resolution_x = 680 * 2.
bpy.data.scenes["Scene"].render.resolution_y = 420 * 2.
world = bpy.data.worlds["World"]
world.use_nodes = True
empty = bpy.data.objects.new("Empty", None)
bpy.context.scene.objects.link(empty)
empty.empty_draw_size = 1
empty.empty_draw_type = "CUBE"
bpy.data.objects["Empty"].location = (0.0000000000e+00, 0.0000000000e+00, 0.0000000000e+00)
bpy.data.objects["Empty"].scale = (5.0000000000e+00, 5.0000000000e+00, 5.0000000000e+00)
empty = bpy.data.objects["Empty"]
camera = bpy.data.objects["Camera"]
camera.location = (20.0000, 20.0000, 20.0000)
bpy.data.cameras[camera.name].clip_end = 10000.0
bpy.data.cameras[camera.name].clip_start = 0.0
camera_track = camera.constraints.new("TRACK_TO")
camera_track.track_axis = "TRACK_NEGATIVE_Z"
camera_track.up_axis = "UP_Y"
camera_track.target = (bpy.data.objects["Empty"])
# changing these values does affect the render.
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value[:3] = (1.0, 1.0, 1.0)
bg.inputs[1].default_value = 1.0
bpy.data.scenes["Scene"].render.filepath = "cutaway_test" + ".png"
bpy.context.scene.render.use_freestyle = True
bpy.context.scene.cycles.samples = 10
bpy.context.scene.cycles.max_bounces = 32
bpy.context.scene.cycles.min_bounces = 3
bpy.context.scene.cycles.glossy_bounces = 16
bpy.context.scene.cycles.transmission_bounces = 32
bpy.context.scene.cycles.volume_bounces = 4
bpy.context.scene.cycles.transparent_max_bounces = 32
bpy.context.scene.cycles.transparent_min_bounces = 8
bpy.data.scenes["Scene"].cycles.film_transparent = True
bpy.context.scene.cycles.filter_glossy = 0.05
bpy.ops.wm.save_as_mainfile(filepath="cutaway_test.blend")
bpy.ops.render.render( write_still=True )
modelview_matrix = camera.matrix_world.inverted()
projection_matrix = camera.calc_matrix_camera(
        render.resolution_x,
        render.resolution_y,
        render.pixel_aspect_x,
        render.pixel_aspect_y,
        )
P, K, RT = get_3x4_P_matrix_from_blender(camera)
import os
proj_matrix = "[[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e],[%15.10e, %15.10e, %15.10e, %15.10e]]" % (P[0][0], P[0][1], P[0][2], P[0][3], P[1][0], P[1][1], P[1][2], P[1][3], P[2][0], P[2][1], P[2][2], P[2][3])
os.system("convert cutaway_test.png -set proj_matrix '%s' cutaway_test.png" % proj_matrix)
