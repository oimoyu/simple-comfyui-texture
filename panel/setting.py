import bpy
from . import functions, workflow_list
from ..utils import utils, const


def seed_update(self, context):
    try:
        int(self.seed)
    except ValueError:
        utils.ShowMessageBox(message="Not Valid Integer", icon="INFO")
        self.seed = "123456"


def workflow_item_update(self, context):
    workflow_items = self.workflow_items
    workflow_item_index = self.workflow_item_index
    if workflow_item_index < 0 or len(workflow_items) <= workflow_item_index:
        utils.ShowMessageBox(message="No workflow selected", icon="INFO")
        return
    workflow_item = workflow_items[workflow_item_index]
    workflow_item_name = workflow_item.name
    workflow_text = utils.get_workflow_text(context)

    data = (
        (const.mask_filename, "is_render_mask"),
        (const.depth_map_filename, "is_render_depth"),
        (const.outline_image_filename, "is_render_outline"),
        (const.viewport_filename, "is_render_viewport"),
        (const.result_image_filename, "is_upload_result"),
    )

    for _, setting_name in data:
        setattr(self, setting_name, False)

    for filename, setting_name in data:
        if filename in workflow_text:
            setattr(self, setting_name, True)

    # TODO:update pos neg prompt in panel, or not? user may have its fix prompt


class SimpleComfyUITextureSetting(bpy.types.PropertyGroup):
    comfyui_host: bpy.props.StringProperty(name="ComfyUI Host", default="127.0.0.1")
    comfyui_port: bpy.props.IntProperty(name="ComfyUI Port", min=1, default=8188)

    is_randomized_seed: bpy.props.BoolProperty(name="Is Randomize Seed", default=True)
    seed: bpy.props.StringProperty(
        name="Seed",
        default="123456789",
        update=seed_update,
    )

    is_replace_prompt: bpy.props.BoolProperty(name="Replace prompt", default=False)
    pos_prompt: bpy.props.StringProperty(name="Positive Prompt", default="1girl")
    neg_prompt: bpy.props.StringProperty(name="Negative Prompt", default="bad quality")

    is_render_depth: bpy.props.BoolProperty(name="Is Render Depth", default=False)
    is_render_outline: bpy.props.BoolProperty(name="Is Render Outline", default=False)
    is_render_mask: bpy.props.BoolProperty(name="Is Render Mask", default=False)
    is_render_viewport: bpy.props.BoolProperty(name="Is Render Viewport", default=False)
    is_upload_result: bpy.props.BoolProperty(name="Is Render Result", default=False)

    progress_msg: bpy.props.StringProperty(name="", default="")

    auto_match_brush: bpy.props.BoolProperty(
        name="Auto Match Brush",
        default=False,
    )

    # is_running: bpy.props.BoolProperty(name="Is Running", default=False)

    workflow_items: bpy.props.CollectionProperty(
        type=workflow_list.SimpleComfyUITextureWorkflowItem
    )
    workflow_item_index: bpy.props.IntProperty(
        update=workflow_item_update,
    )


classes = (SimpleComfyUITextureSetting,)
