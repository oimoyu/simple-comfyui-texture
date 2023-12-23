import requests
from . import utils
import json
from . import websocket
import contextlib
from . import utils


def _api_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # TODO:should not place here
            utils.set_progress_msg(str(e))
            raise e

    return wrapper


def _comfyui_request(path, method, data={}, files={}, params={}):
    url = f"{utils.get_setting().comfyui_host}:{utils.get_setting().comfyui_port}"
    if not url.startswith("http"):
        url = f"http://{url}"
    url = f"{url}{path}"
    if method == "GET":
        response = requests.get(url, params=params)
    elif method == "POST":
        if files:
            response = requests.post(url, data=data, files=files)
        else:
            response = requests.post(url, json=data, files=files)
    else:
        raise Exception("Unknow Method")
    if response.status_code != 200:
        raise Exception(f"request err:{response.text}")
    return response


def get_status():
    path = "/system_stats"
    try:
        response = _comfyui_request(path, "GET")
        data = response.json()
        return data
        message = f"系统信息: 操作系统 {data['system']['os']}, Python版本 {data['system']['python_version']}。\n"
        message += f"设备信息: 名称 {data['devices'][0]['name']}, 类型 {data['devices'][0]['type']}, VRAM总量 {data['devices'][0]['vram_total']}字节, 可用VRAM {data['devices'][0]['vram_free']}字节。"
    except:
        return {}


@_api_exception
def upload_image(img_path, file_name):
    utils.set_progress_msg(f"Uploading Image {file_name}")
    path = "/upload/image"
    with open(img_path, "rb") as f:
        file_content = f.read()
    files = {"image": (file_name, file_content, "image/png")}
    data = {"overwrite": "1"}
    response = _comfyui_request(path, "POST", files=files, data=data)
    image_name = json.loads(response.content)["name"]
    return image_name


@_api_exception
def queue_prompt(prompt, client_id):
    utils.set_progress_msg(f"Quene Prompt")
    path = "/prompt"
    data = {"prompt": prompt, "client_id": client_id}
    response = _comfyui_request(path, "POST", data=data)
    return response.json()


@_api_exception
@contextlib.contextmanager
def create_ws(client_id):
    utils.set_progress_msg(f"creating ws")
    ws = websocket.WebSocket()
    ws.connect(
        "ws://{}/ws?clientId={}".format(
            f"{utils.get_setting().comfyui_host}:{utils.get_setting().comfyui_port}",
            client_id,
        )
    )
    try:
        yield ws
    finally:
        ws.close()


@_api_exception
def get_prompt_progress(ws, prompt_id):
    utils.set_progress_msg(f"fetching progress {prompt_id}")
    output_images = {}
    while True:
        out = ws.recv()
        yield out
        if (
            isinstance(out, str)
            and json.loads(out)["type"] == "status"
            and json.loads(out)["data"]["status"]["exec_info"]["queue_remaining"] == 0
        ):
            break


@_api_exception
def get_history(prompt_id):
    utils.set_progress_msg(f"fetching history")
    path = f"/history/{prompt_id}"
    response = _comfyui_request(path, "GET")
    return response.json()


@_api_exception
def get_image(filename, subfolder, folder_type):
    utils.set_progress_msg(f"get image {filename}")
    path = f"/view"
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    response = _comfyui_request(path, "GET", params=params)
    return response.content


@_api_exception
def get_images(prompt_id):
    utils.set_progress_msg(f"get images")
    history = get_history(prompt_id)[prompt_id]
    output_images = {}
    for o in history["outputs"]:
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            if "images" in node_output:
                images_output = []
                for image in node_output["images"]:
                    image_data = get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images


@_api_exception
def interrupt():
    utils.set_progress_msg(f"interrupt")
    path = f"/interrupt"
    response = _comfyui_request(path, "POST")
    return
