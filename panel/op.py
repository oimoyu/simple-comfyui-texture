import bpy
from ..utils import const, utils, api
import uuid
import numpy as np
import json
from ..utils import websocket
from . import functions
import threading
from ..utils.task import task
import os


class SimpleComfyUITextureOpenAddonFolderOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.open_addon_folder"
    bl_label = "Open Addon Folder"

    def execute(self, context):
        os.startfile(const.root_dir)

        return {"FINISHED"}


class SimpleComfyUITexturePopupConfigOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.popup_config"
    bl_label = "pop config"

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        setting = context.scene.simple_comfyui_texture_setting
        layout = self.layout

        row = layout.row()
        split = row.split(factor=0.5)
        col = split.column()
        col.label(text="Host")
        col.prop(setting, "comfyui_host", text="")

        split = split.split(factor=0.6)
        col = split.column()
        col.label(text="Port")
        col.prop(setting, "comfyui_port", text="")

        col = split.column()
        col.label(text="")
        col.operator(f"{const.addon_prefix}.test_comfyui", text="", icon="FILE_REFRESH")


class SimpleComfyUITextureTestComfyUIOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.test_comfyui"
    bl_label = "Test ComfyUI"

    def execute(self, context):
        data = api.get_status()
        if data:
            message = f"系统信息: 操作系统 {data['system']['os']}, Python版本 {data['system']['python_version']}。\n"
            message += f"设备信息: 名称 {data['devices'][0]['name']}, 类型 {data['devices'][0]['type']}, VRAM总量 {data['devices'][0]['vram_total']}字节, 可用VRAM {data['devices'][0]['vram_free']}字节。"
            utils.ShowMessageBox(message=message, icon="CHECKMARK")
        else:
            message = "API test failed"
            utils.ShowMessageBox(message=message, icon="CANCEL")

        return {"FINISHED"}


class SimpleComfyUITextureRunOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.run"
    bl_label = "Run Prompt"

    _timer = None

    # TODO:modal should handle except, or may result running hang on
    def modal(self, context, event):
        if event.type == "TIMER":
            area = utils.get_area()
            if area:
                area.tag_redraw()

            utils.load_image_from_path(const.progress_image_path)

            # done or exception case
            if task.status != task.RUNNING:
                self.before_finished(context)
                self.finish(context)
                return {"FINISHED"}

            # stop case
            if task.stop_flag == True:
                # # wait until thread finished
                # while True:
                #     if task.status != task.RUNNING:
                #         break

                # send stop signal
                api.interrupt()
                # finish threading is done in function

                # set msg, do not forget set data in threading
                # threading exception set stop
                self.finish(context)

                return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        setting = utils.get_setting()

        # check workflow
        result = functions.check_workflow(context)
        if result is None:
            return {"FINISHED"}

        # set quad
        utils.set_render_quad()

        # render needed image
        if setting.is_render_depth:
            result = functions.render_depth_map(context)
            if result is None:
                return {"FINISHED"}
        if setting.is_render_outline:
            result = functions.render_outline(context)
            if result is None:
                return {"FINISHED"}
        if setting.is_render_mask:
            result = functions.render_mask(context)
            if result is None:
                return {"FINISHED"}
        if setting.is_render_viewport:
            result = functions.render_viewport(context)
            if result is None:
                return {"FINISHED"}

        self.start(context)

        task.run_task(functions.run, context)

        return {"RUNNING_MODAL"}

    def start(self, context):
        # add timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        utils.set_progress_msg("")
        # utils.get_setting().is_running = True

        # preprocess
        if utils.get_setting().is_randomized_seed:
            utils.randomize_seed()

    def finish(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        # utils.set_progress_msg("")
        # utils.get_setting().is_running = False

    def before_finished(self, context):
        utils.load_image_from_path(const.result_image_path)
        # utils.get_setting().is_running = False
        if utils.get_setting().auto_match_brush:
            result = functions.match_brush(context)
            if result is None:
                return {"FINISHED"}


class SimpleComfyUITextureStopOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.stop"
    bl_label = "Stop Running"

    def execute(self, context):
        task.stop_flag = True
        return {"FINISHED"}


class SimpleComfyUITextureMatchTextureOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.match_brush"
    bl_label = "Match Brush"

    def execute(self, context):
        result = functions.match_brush(context)
        if result is None:
            return {"FINISHED"}
        return {"FINISHED"}


class SimpleComfyUITextureRenderDepthMapOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.render_depth_map"
    bl_label = "render_depth_map"

    def execute(self, context):
        functions.render_depth_map(context)
        utils.set_image_editor(const.depth_map_filename)
        return {"FINISHED"}


class SimpleComfyUITextureRenderOutlineOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.render_outline"
    bl_label = "render_outline"

    def execute(self, context):
        functions.render_outline(context)
        utils.set_image_editor(const.outline_image_filename)
        return {"FINISHED"}


class SimpleComfyUITextureRenderMaskOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.render_mask"
    bl_label = "render_mask"

    def execute(self, context):
        functions.render_mask(context)
        utils.set_image_editor(const.mask_filename)
        return {"FINISHED"}


class SimpleComfyUITextureRenderViewportOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.render_viewport"
    bl_label = "render_viewport"

    def execute(self, context):
        functions.render_viewport(context)
        utils.set_image_editor(const.viewport_filename)

        return {"FINISHED"}


class SimpleComfyUITextureRenderResultOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.show_result"
    bl_label = "show_result"

    def execute(self, context):
        utils.set_image_editor(const.result_image_filename)
        return {"FINISHED"}


class SimpleComfyUITextureShowProgressOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.show_progress"
    bl_label = "show_progress"

    def execute(self, context):
        utils.set_image_editor(const.progress_image_filename)
        return {"FINISHED"}


class SimpleComfyUITextureRefreshWorkflowOperator(bpy.types.Operator):
    bl_idname = f"{const.addon_prefix}.refresh_workflow"
    bl_label = "Refresh Workflow"

    def execute(self, context):
        functions.refresh_workflow(context)
        return {"FINISHED"}


classes = (
    SimpleComfyUITextureOpenAddonFolderOperator,
    SimpleComfyUITexturePopupConfigOperator,
    SimpleComfyUITextureTestComfyUIOperator,
    SimpleComfyUITextureRunOperator,
    SimpleComfyUITextureMatchTextureOperator,
    SimpleComfyUITextureStopOperator,
    SimpleComfyUITextureRenderDepthMapOperator,
    SimpleComfyUITextureRenderOutlineOperator,
    SimpleComfyUITextureRenderMaskOperator,
    SimpleComfyUITextureRefreshWorkflowOperator,
    SimpleComfyUITextureRenderViewportOperator,
    SimpleComfyUITextureRenderResultOperator,
    SimpleComfyUITextureShowProgressOperator,
)
