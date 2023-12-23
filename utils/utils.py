import bpy
import re
import random
import os
import json


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def ShowMessageBox(message="", title="Message", icon="INFO"):
    def draw(self, context):
        for line in message.split("\n"):
            self.layout.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def get_setting():
    return bpy.context.scene.simple_comfyui_texture_setting


def process_prompt_text(prompt_text):
    # seed
    prompt_text = re.sub(
        r"(\"seed\":\s+)(\d+)",
        lambda m: f"{m.group(1)}{get_setting().seed}",
        prompt_text,
        flags=re.MULTILINE,
    )

    if get_setting().is_replace_prompt:
        # prompt
        json_data = json.loads(prompt_text)
        for node_index, KS_node in json_data.items():
            print(KS_node)
            if KS_node.get("class_type") != "KSampler":
                continue

            temp_dict = {}
            text_type_list = ["positive", "negative"]
            for text_type in text_type_list:
                if KS_node["inputs"].get(text_type):
                    temp_node_index = KS_node["inputs"][text_type][0]

                    while True:
                        if (
                            json_data[temp_node_index].get("class_type")
                            == "CLIPTextEncode"
                        ):
                            temp_dict[temp_node_index] = text_type
                            break
                        if json_data[temp_node_index]["inputs"].get("conditioning"):
                            temp_node_index = json_data[temp_node_index]["inputs"][
                                "conditioning"
                            ][0]
                        else:
                            break

        for node_index, text_type in temp_dict.items():
            if text_type == "positive":
                json_data[node_index]["inputs"]["text"] = get_setting().pos_prompt
            elif text_type == "negative":
                json_data[node_index]["inputs"]["text"] = get_setting().neg_prompt
        prompt_text = json.dumps(json_data)

    return prompt_text


def get_or_create_brush(brush_name):
    if brush_name in bpy.data.brushes:
        return bpy.data.brushes[brush_name]
    else:
        new_brush = bpy.data.brushes.new(name=brush_name, mode="TEXTURE_PAINT")

        return new_brush


def get_or_create_texture(texture_name):
    if texture_name in bpy.data.textures:
        return bpy.data.textures[texture_name]
    else:
        new_texture = bpy.data.textures.new(name=texture_name, type="IMAGE")
        return new_texture


def get_or_create_grease_pencil_obj(obj_name):
    obj = bpy.context.scene.objects.get(obj_name)
    if not obj:
        gp_data = bpy.data.grease_pencils.new(obj_name)
        gp_obj = bpy.data.objects.new(obj_name, gp_data)
        bpy.context.scene.collection.objects.link(gp_obj)
        obj = gp_obj
    return obj


def get_or_create_grease_pencil_material(name):
    gp_mat = bpy.data.materials.get(name)
    if not gp_mat:
        gp_mat = bpy.data.materials.new(name)
        bpy.data.materials.create_gpencil_data(gp_mat)
    return gp_mat


def get_or_create_grease_pencil_layer(gp_obj, gp_layer_name):
    gp_layer = gp_obj.data.layers.get(gp_layer_name)
    if not gp_layer:
        gp_layer = gp_obj.data.layers.new(gp_layer_name)
    return gp_layer


def setup_outline_grease_pencil(
    gp_obj_name, gp_material_name, gp_color, gp_layer_name, gp_modifier_name
):
    gp_obj = bpy.context.scene.objects.get(gp_obj_name)
    if not gp_obj:
        gp_obj = get_or_create_grease_pencil_obj(gp_obj_name)
        gp_mat = get_or_create_grease_pencil_material(gp_material_name)
        if gp_mat.name not in gp_obj.data.materials:
            gp_obj.data.materials.append(gp_mat)
        gp_layer = get_or_create_grease_pencil_layer(gp_obj, gp_layer_name)
        gp_mat.grease_pencil.color = gp_color

        gp_mod = gp_obj.grease_pencil_modifiers.get(gp_modifier_name)
        if not gp_mod:
            gp_mod = gp_obj.grease_pencil_modifiers.new(gp_modifier_name, "GP_LINEART")

        gp_mod.show_render = False
        gp_mod.source_type = "SCENE"
        gp_mod.target_layer = gp_layer.info
        gp_mod.target_material = gp_mat
        gp_mod.thickness = 2
        gp_mod.use_intersection = False

        if not gp_layer.frames:
            gp_frame = gp_layer.frames.new(0)
            gp_stroke = gp_frame.strokes.new()
            gp_stroke.display_mode = "3DSPACE"
    return gp_obj


def setup_grease_pencil(
    gp_obj_name, gp_material_name, gp_color, gp_layer_name, gp_modifier_name
):
    gp_obj = bpy.context.scene.objects.get(gp_obj_name)
    if not gp_obj:
        gp_obj = get_or_create_grease_pencil_obj(gp_obj_name)
        gp_mat = get_or_create_grease_pencil_material(gp_material_name)
        if gp_mat.name not in gp_obj.data.materials:
            gp_obj.data.materials.append(gp_mat)
        gp_layer = get_or_create_grease_pencil_layer(gp_obj, gp_layer_name)
        gp_mat.grease_pencil.color = gp_color

        if not gp_layer.frames:
            gp_frame = gp_layer.frames.new(0)
            gp_stroke = gp_frame.strokes.new()
            gp_stroke.display_mode = "3DSPACE"

    # TODO: set gp strength

    return gp_obj


def set_progress_msg(msg):
    print(msg)
    get_setting().progress_msg = msg


def load_image_from_path(path):
    basename = os.path.basename(path)
    image = bpy.data.images.get(basename)
    if image:
        bpy.data.images[basename].filepath = path
        bpy.data.images[basename].reload()
    else:
        if os.path.exists(path):
            image = bpy.data.images.load(path)
    return image


def get_all_objs_viewport_hide_info():
    data = {}
    for obj in bpy.context.scene.objects:
        data[obj.name] = obj.hide_get()
    return data


def resume_all_objs_viewport_hide(data):
    for k, v in data.items():
        bpy.context.scene.objects[k].hide_set(v)


def hide_all_objs_from_viewport():
    for obj in bpy.context.scene.objects:
        if obj.name in bpy.context.view_layer.objects:
            obj.hide_set(True)


def deselect_all():
    if bpy.context.object and bpy.context.object.mode == "OBJECT":
        bpy.ops.object.select_all(action="DESELECT")


def duplicate_bpy_image(ori_image, new_image_name):
    width = ori_image.size[0]
    height = ori_image.size[1]
    temp_image = bpy.data.images.get(new_image_name)
    if temp_image:
        bpy.data.images.remove(temp_image)
    new_image = bpy.data.images.new(
        new_image_name,
        width=width,
        height=height,
        alpha=True,
        float_buffer=True,
    )
    new_image.pixels[:] = ori_image.pixels
    return new_image


def get_area():
    area = None
    for area_temp in bpy.context.screen.areas:
        if area_temp.type == "VIEW_3D":
            area = area_temp
    return area


def randomize_seed():
    get_setting().seed = str(random.randint(0, int(1e14)))


def check_for_render():
    area = get_area()
    if not area:
        ShowMessageBox(message="No 3D VIEW", icon="INFO")
        return

    if area.spaces.active.region_3d.view_perspective != "CAMERA":
        ShowMessageBox(message="View not in a Camera", icon="INFO")
        return

    view_layers = bpy.context.scene.view_layers
    if len(view_layers) == 0:
        ShowMessageBox(message="No View Layer", icon="INFO")
        return
    view_layer = bpy.context.scene.view_layers[0]
    view_layer.use_pass_mist = True
    bpy.context.scene.render.film_transparent = True
    return True


def set_image_editor(image_name):
    if image_name in bpy.data.images:
        image = bpy.data.images[image_name]
        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                for space in area.spaces:
                    if space.type == "IMAGE_EDITOR":
                        space.image = image
                        return


def set_render_quad():
    if bpy.context.scene.render.resolution_x > bpy.context.scene.render.resolution_y:
        bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y
    else:
        bpy.context.scene.render.resolution_y = bpy.context.scene.render.resolution_x


def get_workflow_text(context):
    # get workflow text
    setting = get_setting()
    workflow_items = setting.workflow_items
    workflow_item_index = setting.workflow_item_index
    if workflow_item_index < 0 or len(workflow_items) <= workflow_item_index:
        ShowMessageBox(message="No workflow selected", icon="INFO")
        return
    workflow_item = workflow_items[workflow_item_index]

    workflow_path = workflow_item.path
    if not os.path.exists(workflow_path):
        ShowMessageBox(message="File not exist", icon="INFO")
        return

    workflow_text = ""
    with open(workflow_path, "r") as file:
        workflow_text = file.read()
    return workflow_text
