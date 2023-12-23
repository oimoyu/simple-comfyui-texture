import bpy
from ..utils import const, utils, api
import uuid
import numpy as np
import json
from ..utils import websocket
from ..utils.task import task
import os


def match_brush(context):
    area = utils.get_area()
    if not area:
        utils.ShowMessageBox(message="No 3D VIEW", icon="INFO")
        return

    active_camera = bpy.context.scene.camera
    if not active_camera:
        utils.ShowMessageBox(message="No Active Camera", icon="INFO")
        return
    area.spaces[0].region_3d.view_perspective = "CAMERA"

    area_width = area.width
    area_height = area.height

    r3d = area.spaces[0].region_3d
    view_camera_zoom_fac = (2**0.5 + r3d.view_camera_zoom / 50) ** 2 / 4
    length = max(area.width, area.height) * view_camera_zoom_fac
    render_width = bpy.context.scene.render.resolution_x
    render_height = bpy.context.scene.render.resolution_y
    length = length * min(render_width / render_height, render_height / render_width)

    brush = utils.get_or_create_brush(const.brush_name)
    texture = utils.get_or_create_texture(const.texture_name)
    texture.image = bpy.data.images[const.result_image_filename]
    brush.texture = texture
    brush.texture_slot.map_mode = "STENCIL"

    brush.color = (1, 1, 1)
    brush.strength = 1

    # transform
    tex_slot = brush.texture_slot
    view_camera_offset = r3d.view_camera_offset
    view_camera_zoom = r3d.view_camera_zoom
    r3d.view_camera_offset = (0, 0)
    brush.stencil_pos = ((area_width) / 2, (area_height - 25) / 2)
    brush.stencil_dimension = (length / 2, length / 2)
    texture = brush.texture

    bpy.context.tool_settings.image_paint.brush = brush

    try:
        # mode
        active_obj = bpy.context.active_object
        current_mode = bpy.context.object.mode
        if current_mode == "TEXTURE_PAINT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")
        elif (
            current_mode != "TEXTURE_PAINT"
            and active_obj is not None
            and active_obj.type == "MESH"
        ):
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

        # tool
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Draw")
    except:
        pass

    return True


def run(context):
    client_id = str(uuid.uuid4())

    setting = utils.get_setting()

    if setting.is_render_depth:
        api.upload_image(const.depth_map_path, const.depth_map_filename)
    if setting.is_render_outline:
        api.upload_image(const.outline_image_path, const.outline_image_filename)
    if setting.is_render_mask:
        api.upload_image(const.mask_path, const.mask_filename)
    if setting.is_render_viewport:
        api.upload_image(const.viewport_path, const.viewport_filename)
    if setting.is_upload_result:
        api.upload_image(const.result_image_path, const.result_image_filename)

    prompt_text = utils.get_workflow_text(context)

    prompt_text = utils.process_prompt_text(prompt_text)

    with open(const.temp_workflow_path, "w") as outfile:
        outfile.write(prompt_text)

    prompt = json.loads(prompt_text)

    prompt_id = api.queue_prompt(prompt, client_id)["prompt_id"]
    with api.create_ws(client_id) as ws:
        for out in api.get_prompt_progress(ws, prompt_id):
            # stop case
            # TODO:make it work for stop ws conn
            if task.stop_flag == True:
                return

            # get progress case
            if isinstance(out, str):
                data = json.loads(out)
                if data.get("type") == "progress":
                    utils.set_progress_msg(
                        f"{data['data']['value']}/{data['data']['max']}"
                    )

                print(data)

            # get progress image case
            if isinstance(out, bytes):
                try:
                    with open(const.progress_image_path, "wb") as file:
                        file.write(out[8:])
                except:
                    pass

    output_images = api.get_images(prompt_id)

    image_output_bytes = next(iter(next(iter(output_images.values()))), None)
    if not image_output_bytes:
        utils.ShowMessageBox(message="No Image Output", icon="INFO")
        return

    with open(const.result_image_path, "wb") as file:
        file.write(image_output_bytes)

    utils.set_progress_msg(f"Done")

    return True


# TODO: render process using with context, process before and after
def render_depth_map(context):
    result = utils.check_for_render()
    if result is None:
        return result
    view_layer = bpy.context.scene.view_layers[0]

    # TODO:recover after done
    view_layer.use_pass_mist = True
    bpy.context.scene.render.film_transparent = True

    # mist range
    bpy.context.scene.world.mist_settings.start = 0
    bpy.context.scene.world.mist_settings.depth = 100

    # TODO:do not messup the original nodes
    # Set up rendering of depth map:

    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    for n in tree.nodes:
        tree.nodes.remove(n)
    rl = tree.nodes.new("CompositorNodeRLayers")
    color_ramp = tree.nodes.new(type="CompositorNodeValToRGB")
    links.new(rl.outputs[2], color_ramp.inputs[0])
    composite = tree.nodes.new(type="CompositorNodeComposite")
    links.new(color_ramp.outputs[0], composite.inputs[0])
    comp_alpha_output_link = links.new(rl.outputs[1], composite.inputs[1])
    viewer = tree.nodes.new(type="CompositorNodeViewer")
    links.new(color_ramp.outputs[0], viewer.inputs[0])
    viewer_alpha_output_link = links.new(rl.outputs[1], viewer.inputs[1])
    bpy.ops.render.render(animation=False)

    # bpy.ops.render.render()
    image = bpy.data.images["Viewer Node"]
    pixels = np.asarray(image.pixels[:])
    width = image.size[0]
    height = image.size[1]
    pixels = pixels.reshape((-1, 4))

    # invert
    # pixels[:, :, :3] = 1.0 - pixels[:, :, :3]
    # get data
    alpha_mask = pixels[:, 3] == 1
    max_grey = np.max(pixels[:, :3][alpha_mask])  # most light
    min_grey = np.min(pixels[:, :3][alpha_mask])  # most dark
    # set ramp
    color_ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    color_ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    color_ramp.color_ramp.elements[0].position = min(min_grey * 0.99, 1)
    color_ramp.color_ramp.elements[1].position = min(max_grey * 1.01, 1)
    # remove alpha
    links.remove(comp_alpha_output_link)
    links.remove(viewer_alpha_output_link)

    # TODO:without rerender
    bpy.ops.render.render(animation=False)
    image = bpy.data.images["Viewer Node"]
    # TODO:without save file
    depth_map_filename = const.depth_map_filename

    image.save_render(const.depth_map_path)
    utils.load_image_from_path(const.depth_map_path)
    # result_image = utils.duplicate_bpy_image(image, depth_map_filename)

    # utils.set_image_editor(image.name)
    return True


def render_outline(context):
    result = utils.check_for_render()
    if result is None:
        return result
    area = utils.get_area()

    utils.deselect_all()
    gp_obj = utils.setup_outline_grease_pencil(
        const.outline_obj_name,
        const.grease_pencil_material_name,
        const.grease_pencil_color,
        const.grease_pencil_layer_name,
        const.grease_pencil_modifier_name,
    )
    gp_obj.hide_render = True

    gp_mod = gp_obj.grease_pencil_modifiers.get(const.grease_pencil_modifier_name)
    if gp_mod:
        # set for performance
        gp_mod.show_viewport = True

    temp_overlay = area.spaces.active.overlay.show_overlays
    area.spaces.active.overlay.show_overlays = False
    objs_viewport_visible_info = utils.get_all_objs_viewport_hide_info()

    # show gp obj
    gp_obj.hide_set(False)

    # update gp result
    bpy.context.view_layer.update()

    # hide all except gp
    for obj in bpy.context.scene.objects:
        if obj.name in bpy.context.view_layer.objects and obj.name != gp_obj.name:
            obj.hide_set(True)

    bpy.ops.render.opengl()
    image = bpy.data.images["Render Result"]
    image.save_render(const.outline_image_path)

    # set for performance
    if gp_mod:
        gp_mod.show_viewport = False
    area.spaces.active.overlay.show_overlays = temp_overlay

    utils.resume_all_objs_viewport_hide(objs_viewport_visible_info)

    result_image = utils.load_image_from_path(const.outline_image_path)
    pixels = np.asarray(result_image.pixels[:])
    pixels = pixels.reshape((-1, 4))

    # grey value by alpha
    grey_values = pixels[:, 3] * 255

    # grey values to RGB channels
    pixels[:, 0] = grey_values
    pixels[:, 1] = grey_values
    pixels[:, 2] = grey_values

    # Set alpha 1
    pixels[:, 3] = 1

    result_image.pixels = pixels.ravel()

    result_image.save_render(const.outline_image_path)

    # utils.set_image_editor(result_image.name)
    return True


def render_mask(context):
    result = utils.check_for_render()
    if result is None:
        return result
    area = utils.get_area()

    utils.deselect_all()
    gp_obj = utils.setup_grease_pencil(
        const.mask_obj_name,
        const.grease_pencil_material_name,
        const.grease_pencil_color,
        const.grease_pencil_layer_name,
        const.grease_pencil_modifier_name,
    )
    gp_obj.hide_render = True

    temp_overlay = area.spaces.active.overlay.show_overlays
    area.spaces.active.overlay.show_overlays = False
    objs_viewport_visible_info = utils.get_all_objs_viewport_hide_info()

    # show gp obj
    gp_obj.hide_set(False)

    # update gp result
    bpy.context.view_layer.update()

    # hide all except gp
    for obj in bpy.context.scene.objects:
        if obj.name in bpy.context.view_layer.objects and obj.name != gp_obj.name:
            obj.hide_set(True)

    bpy.ops.render.opengl()
    image = bpy.data.images["Render Result"]
    image.save_render(const.mask_path)

    utils.resume_all_objs_viewport_hide(objs_viewport_visible_info)
    result_image = utils.load_image_from_path(const.mask_path)
    pixels = np.asarray(result_image.pixels[:])
    pixels = pixels.reshape((-1, 4))

    # invert alpha
    pixels[:, 3] = 1 - pixels[:, 3]

    result_image.pixels = pixels.ravel()

    result_image.save_render(const.mask_path)

    area.spaces.active.overlay.show_overlays = temp_overlay

    # utils.set_image_editor(result_image.name)
    return True


def render_viewport(context):
    result = utils.check_for_render()
    if result is None:
        return result

    utils.deselect_all()

    view_layers = bpy.context.scene.view_layers
    if len(view_layers) == 0:
        utils.ShowMessageBox(message="No View Layer", icon="INFO")
        return
    view_layer = bpy.context.scene.view_layers[0]
    view_layer.use_pass_mist = True
    bpy.context.scene.render.film_transparent = True

    # hide mask and outline
    outline_obj = bpy.context.scene.objects.get(const.outline_obj_name)
    if outline_obj:
        outline_obj.hide_set(True)
    mask_obj = bpy.context.scene.objects.get(const.mask_obj_name)
    if mask_obj:
        mask_obj.hide_set(True)

    bpy.ops.render.opengl()
    image = bpy.data.images["Render Result"]

    image.save_render(const.viewport_path)

    result_image = utils.load_image_from_path(const.viewport_path)

    # utils.set_image_editor(result_image.name)
    return True


def refresh_workflow(context):
    setting = utils.get_setting()
    setting.workflow_items.clear()

    for filename in os.listdir(const.workflow_dir):
        if filename.endswith(".json") and os.path.isfile(
            os.path.join(const.workflow_dir, filename)
        ):
            my_item = setting.workflow_items.add()
            my_item.name = filename
            my_item.path = os.path.join(const.workflow_dir, filename)
    return True


def check_workflow(context):
    setting = utils.get_setting()
    workflow_text = utils.get_workflow_text(context)
    if workflow_text is None:
        return

    # refresh_workflow()

    info_list = (
        (const.mask_filename, setting.is_render_mask),
        (const.depth_map_filename, setting.is_render_depth),
        (const.outline_image_filename, setting.is_render_outline),
        (const.viewport_filename, setting.is_render_viewport),
        (const.result_image_filename, setting.is_upload_result),
    )
    for image_filename, is_enable in info_list:
        if image_filename in workflow_text and not is_enable:
            utils.ShowMessageBox(
                message=f"【{image_filename}】 in workflow, but not enable render",
                icon="INFO",
            )
            return

    # check result image
    image_filename = const.result_image_filename
    if image_filename in workflow_text and not bpy.data.images[image_filename]:
        utils.ShowMessageBox(
            message=f"【{image_filename}】 in workflow, but not exist",
            icon="INFO",
        )
        return

    return True
