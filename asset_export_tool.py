bl_info = {
    "name": "Asset Export Tool",
    "blender": (4, 0, 0),
    "category": "Object",
}

import bpy
import os


# ------------------------
# UTILS
# ------------------------

def get_hierarchy(obj):
    result = []

    def recurse(o):
        result.append(o)
        for c in o.children:
            recurse(c)

    recurse(obj)
    return result


def is_valid_scale(scale):
    return all(abs(abs(s) - 1.0) < 0.001 for s in scale)


def get_scale_issues(obj):
    bad = []
    for o in get_hierarchy(obj):
        if not is_valid_scale(o.scale):
            bad.append(o.name)
    return bad


def get_linked_duplicates(obj):
    linked = []

    for o in get_hierarchy(obj):
        if o.data and o.data.users > 1:
            linked.append((o.name, o.data.name, o.data.users))

    return linked


def clean_name(name):
    if "." in name:
        parts = name.split(".")
        if parts[-1].isdigit():
            name = ".".join(parts[:-1])

    return name.replace(" ", "_").replace("/", "_").replace("\\", "_")


# ------------------------
# EXPORT OPERATOR
# ------------------------

class OBJECT_OT_asset_export(bpy.types.Operator):
    bl_idname = "object.asset_export_tool_export"
    bl_label = "Export FBX"

    def execute(self, context):
        obj = context.active_object
        folder = context.scene.export_folder

        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        if not folder:
            self.report({'ERROR'}, "No export folder selected")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        hierarchy = get_hierarchy(obj)
        for o in hierarchy:
            o.select_set(True)

        context.view_layer.objects.active = obj
        bpy.ops.object.duplicate()

        dup_objects = context.selected_objects

        for o in dup_objects:
            if o.parent is None:
                o.location = (0, 0, 0)

                if o.rotation_mode == 'QUATERNION':
                    o.rotation_quaternion = (1, 0, 0, 0)
                else:
                    o.rotation_euler = (0, 0, 0)

        bpy.context.view_layer.update()

        filename = clean_name(obj.name) + ".fbx"
        filepath = os.path.join(folder, filename)

        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z',
            axis_up='Y',
            bake_space_transform=False
        )

        bpy.ops.object.delete()

        self.report({'INFO'}, f"FBX exported: {filename}")
        return {'FINISHED'}


# ------------------------
# UI PANEL
# ------------------------

class VIEW3D_PT_asset_export_tool(bpy.types.Panel):
    bl_label = "Asset Export Tool"
    bl_idname = "VIEW3D_PT_asset_export_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Export'

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        layout.prop(context.scene, "export_folder")
        layout.separator()

        if obj:
            bad_scales = get_scale_issues(obj)
            linked = get_linked_duplicates(obj)

            # SCALE
            if bad_scales:
                layout.label(text="Scale issues:", icon='ERROR')
                for name in bad_scales:
                    layout.label(text=f"- {name}")
            else:
                layout.label(text="Scale: OK", icon='CHECKMARK')

            layout.separator()

            # ALT+D LINKED
            if linked:
                layout.label(text=f"Linked: {len(linked)}", icon='LINKED')
                for name, data_name, users in linked:
                    layout.label(text=f"- {name} ({data_name}, {users})")
            else:
                layout.label(text="Linked: 0", icon='CHECKMARK')

        else:
            layout.label(text="No active object", icon='INFO')

        layout.separator()

        layout.operator("object.asset_export_tool_export", icon='EXPORT')


# ------------------------
# REGISTER
# ------------------------

def register():
    bpy.utils.register_class(OBJECT_OT_asset_export)
    bpy.utils.register_class(VIEW3D_PT_asset_export_tool)

    bpy.types.Scene.export_folder = bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH'
    )


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_asset_export)
    bpy.utils.unregister_class(VIEW3D_PT_asset_export_tool)

    del bpy.types.Scene.export_folder


if __name__ == "__main__":
    register()