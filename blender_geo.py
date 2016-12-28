import bpy

class bgeo:
    def __init__(self):
        pass

    def __add__(self, right):
        if right is not None:
            self.name = self.name + "p" + right.name
            union = self.object.modifiers.new(self.name,"BOOLEAN")
            union.operation = "UNION"
            union.object = right.object
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=self.name)
            bpy.context.scene.objects.unlink(right.object)
            # self.object = bpy.context.scene.objects.get(self.name)
            bpy.context.scene.objects.active = self.object
            return self

    def __sub__(self, right):
        if right is not None:
            self.name = self.name + "m" + right.name
            union = self.object.modifiers.new(self.name,"BOOLEAN")
            union.operation = "DIFFERENCE"
            union.object = right.object
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=self.name)
            bpy.context.scene.objects.unlink(right.object)
            # self.object = bpy.context.scene.objects.get(self.name)
            bpy.context.scene.objects.active = self.object
            return self

    def pz(self, x1=None, x2=None, y1=None, y2=None, z=None,
           name='p'):
        self.name = name
        verts = [(x1, y1, z), (x1, y2, z), (x2, y2, z), (x2, y1, z)]
        faces = [(0, 1, 2, 3)]
        ground_plane = bpy.data.meshes.new("ground_plane")
        ground_plane_object = bpy.data.objects.new("ground_plane", ground_plane)
        ground_plane_object.location = (0., 0., 0.)
        bpy.context.scene.objects.link(ground_plane_object)
        ground_plane.from_pydata(verts, [], faces)
        ground_plane.update(calc_edges=True)
        self.object = bpy.context.object
        return self

    def set_matl(self, matl=None):
        obj = bpy.context.scene.objects.get(self.name)
        bpy.context.scene.objects.active = obj
        # bpy.ops.object.material_slot_add()
        self.object.active_material = matl.matl
