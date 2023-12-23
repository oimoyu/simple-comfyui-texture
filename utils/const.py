import os
from ..utils import utils


# class MyImage:
#     # filename = None
#     # path = None
#     # enable_setting_name = None

#     def __init__(self, filename, path, enable_setting_name):
#         self.filename = filename
#         self.path = path
#         self.enable_setting_name = enable_setting_name

#     @property
#     def enable(self):
#         return getattr(utils.get_setting(), self.enable_setting_name)

#     @enable.setter
#     def enable(self, value):
#         setattr(utils.get_setting(), self.enable_setting_name, value)


# myimage_mask = MyImage(
#     filename="oimoyu_depth_map.png",
#     path=os.path.join(temp_dir, "oimoyu_depth_map.png"),
#     enable_setting_name="is_render_mask",
# )


panel_tag_name = "Simple ComfyUI Texture"

addon_prefix = "simple_comfyui_texture"
root_dir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
)
workflow_dir = os.path.join(root_dir, "workflow")
temp_dir = os.path.join(root_dir, "temp")
temp_path = os.path.join(temp_dir, "temp.png")

temp_workflow_path = os.path.join(temp_dir, "workflow.json")


depth_map_filename = "oimoyu_depth_map.png"
depth_map_path = os.path.join(temp_dir, depth_map_filename)

mask_filename = "oimoyu_mask.png"
mask_path = os.path.join(temp_dir, mask_filename)

viewport_filename = "oimoyu_viewport.png"
viewport_path = os.path.join(temp_dir, viewport_filename)

progress_image_filename = "oimoyu_progress.png"
progress_image_path = os.path.join(temp_dir, progress_image_filename)

result_image_filename = "oimoyu_result.png"
result_image_path = os.path.join(temp_dir, result_image_filename)

outline_image_filename = "oimoyu_outline.png"
outline_image_path = os.path.join(temp_dir, outline_image_filename)

brush_name = "oimoyu_comfyui_brush"
texture_name = "oimoyu_comfyui_texture"

outline_obj_name = "oimoyu_outline"
mask_obj_name = "oimoyu_mask"

grease_pencil_material_name = "oimoyu_grease_pencil_material"
grease_pencil_layer_name = "oimoyu_grease_pencil_layer"
grease_pencil_modifier_name = "oimoyu_grease_pencil_modifier"
grease_pencil_color = (0, 0, 1, 1)

all_image_filename_list = [
    mask_filename,
    viewport_filename,
    depth_map_filename,
    outline_image_filename,
]
