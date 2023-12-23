import bpy
from ..utils import const, utils
from . import op
from ..utils.task import task


class SimpleComfyUITextureMainPanel(bpy.types.Panel):
    bl_label = ""
    bl_idname = "VIEW3D_PT_OIMOYU_SIMPLE_COMFYUI_TEXTURE_MAIN_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = const.panel_tag_name
    bl_order = 1

    def draw(self, context):
        setting = utils.get_setting()
        layout = self.layout

        row = layout.row()
        row.scale_y = 2.0
        # if not setting.is_running:
        if task.status != task.RUNNING:
            row.operator(f"{const.addon_prefix}.run", text="Run", icon="PLAY")
        else:
            row.operator(f"{const.addon_prefix}.stop", text="Stop", icon="PAUSE")

        layout.row().label(
            text=setting.progress_msg,
        )

        row = layout.row()
        split = row.split(factor=0.9)
        col = split.column()
        col.operator(
            f"{const.addon_prefix}.match_brush", text="Match Brush", icon="BRUSH_DATA"
        )

        col = split.column()
        col.prop(
            setting,
            "auto_match_brush",
            icon="FILE_REFRESH",
            text="",
        )

        upload_col = layout.column(align=True)
        guide_mesh_box = upload_col.box()
        guide_mesh_box.row().label(text="Upload Options")

        split = guide_mesh_box.row().split(factor=0.1)
        split.column().prop(
            setting,
            "is_render_depth",
            text="",
        )
        split.column().operator(
            f"{const.addon_prefix}.render_depth_map",
            text="Render Depth Map",
            icon="IMAGE_ZDEPTH",
        )

        split = guide_mesh_box.row().split(factor=0.1)
        split.column().prop(
            setting,
            "is_render_outline",
            text="",
        )
        split.column().operator(
            f"{const.addon_prefix}.render_outline",
            text="Render Outline",
            icon="IPO_LINEAR",
        )

        split = guide_mesh_box.row().split(factor=0.1)
        split.column().prop(
            setting,
            "is_render_mask",
            text="",
        )
        split.column().operator(
            f"{const.addon_prefix}.render_mask",
            text="Render Mask",
            icon="MOD_MASK",
        )

        split = guide_mesh_box.row().split(factor=0.1)
        split.column().prop(
            setting,
            "is_render_viewport",
            text="",
        )
        split.column().operator(
            f"{const.addon_prefix}.render_viewport",
            text="Render Viewport",
            icon="SEQ_PREVIEW",
        )

        split = guide_mesh_box.row().split(factor=0.1)
        split.column().prop(
            setting,
            "is_upload_result",
            text="",
        )
        split.column().operator(
            f"{const.addon_prefix}.show_result",
            text="Show Result",
            icon="SEQ_PREVIEW",
        )
        guide_mesh_box.row().operator(
            f"{const.addon_prefix}.show_progress",
            text="Show Progress",
            icon="SEQUENCE",
        )

        layout.separator()
        layout.separator()
        layout.row().label(text="Workflow File")
        row = layout.row()
        row.template_list(
            "SIMPLECOMFYUITEXTURE_UL_WORKFLOW",
            "",
            setting,
            "workflow_items",
            setting,
            "workflow_item_index",
        )
        col = row.column(align=True)
        row.operator(
            f"{const.addon_prefix}.refresh_workflow",
            text="",
            icon="FILE_REFRESH",
        )

        row = layout.row()
        split = row.split(factor=0.2)
        split.column().label(text="Seed")
        split1 = split.split(factor=0.8)
        col = split1.column()
        if setting.is_randomized_seed:
            col.label(
                text=str(setting.seed),
            )
        else:
            col.prop(
                setting,
                "seed",
                text="",
            )
        split1.column().prop(
            setting,
            "is_randomized_seed",
            icon="FILE_REFRESH",
            text="",
        )

        layout.row().prop(
            setting,
            "is_replace_prompt",
        )
        if setting.is_replace_prompt:
            layout.row().prop(
                setting,
                "pos_prompt",
            )
            layout.row().prop(
                setting,
                "neg_prompt",
            )

    def draw_header(self, context):
        setting = utils.get_setting()

        row = self.layout.row(align=True)
        row.label(text="Main")
        row.operator(f"{const.addon_prefix}.popup_config", text="", icon="PREFERENCES")
        row.operator(
            f"{const.addon_prefix}.open_addon_folder", text="", icon="FILE_FOLDER"
        )


classes = (SimpleComfyUITextureMainPanel,)
