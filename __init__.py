import bpy
from .panel import classes, op, panel, setting

bl_info = {
    "name": "Simple ComfyUI Texture",
    "author": "oimoyu",
    "version": (1, 1),
    "blender": (3, 6, 2),
    "location": "View3D > Sidebar > Simple ComfyUI Texture",
    "description": "Simple ComfyUI Texture",
    "category": "Object",
}


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.simple_comfyui_texture_setting = bpy.props.PointerProperty(
        type=setting.SimpleComfyUITextureSetting
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.simple_comfyui_texture_setting


if __name__ == "__main__":
    register()
