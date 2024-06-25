##########################################################################
#
# Filename: comfyui_api_ws.py
#
# Copyright (c) 2024 Julien Martin
# All rights reserved.
#
###########################################################################

import os
import json
import glob
from enum import Enum
from pathlib import Path
from pprint import pprint
import urllib.request
import urllib.parse
from urllib.error import URLError
import websocket


COMFYUI_HOSTNAME = "192.168.1.14"
COMFYUI_HOSTPORT = "8188"
COMFYUI_SERVER_ADDRESS = COMFYUI_HOSTNAME + ':' + COMFYUI_HOSTPORT
COMFYUI_DIR = "002_COMFYUI"

COMFYUI_SERVER_MOUNT_DIR_MAC = "/Volumes/silo2"
COMFYUI_WORKING_DIR = str(Path(COMFYUI_SERVER_MOUNT_DIR_MAC) / COMFYUI_DIR)
COMFYUI_WORKFLOWS_DIR = str(Path(COMFYUI_WORKING_DIR) / "workflows")
COMFYUI_IO_DIR = {
    "in": str(Path(COMFYUI_WORKING_DIR) / "in"), 
    "out": str(Path(COMFYUI_WORKING_DIR) / "out") 
}
COMFYUI_INPUT_DIR = COMFYUI_IO_DIR["in"]
COMFYUI_OUTPUT_DIR = COMFYUI_IO_DIR["out"]

COMFYUI_SERVER_MOUNT_DIR_WIN = "S:"
COMFYUI_SERVER_WORKING_DIR = str(Path(COMFYUI_SERVER_MOUNT_DIR_WIN) / COMFYUI_DIR)
COMFYUI_SERVER_WORKFLOWS_DIR = str(Path(COMFYUI_SERVER_WORKING_DIR) / "workflows")
COMFYUI_SERVER_IO_DIR = {
    "in": str(Path(COMFYUI_SERVER_WORKING_DIR) / "in"),
    "out": str(Path(COMFYUI_SERVER_WORKING_DIR) / "out")
}
COMFYUI_SERVER_INPUT_DIR = COMFYUI_SERVER_IO_DIR["in"]
COMFYUI_SERVER_OUTPUT_DIR = COMFYUI_SERVER_IO_DIR["out"]

COMFYUI_OUTPUT_DEFAULT_INITIAL_VERSION = 1

COMFYUI_MODELS_EXCLUDED_DIRS = [
    ".git", 
    "doc", 
    "tokenizer", 
    "text_encoder", 
    "unet", 
    "scheduler"
    ]
COMFYUI_MODELS_FILETYPES = [
    "safetensors", 
    "ckpt",
    "pth"
    ]

DEFAULT_IMAGE_FORMAT = "exr"

class ComfyUIStatus(str, Enum):
    PROGRESS = "progress"
    EXECUTING = "executing"
    EXECUTION_CACHED = "execution_cached"
    STATUS = "status"
    ERROR = "execution_error"

class Side(str, Enum):
    CLIENT = "Client"
    SERVER = "Server"


def find_models(root_dirs):
    models = []
    for model_path in root_dirs:
        print("Searching for models in {}".format(model_path))
        for _, dirs, files in os.walk(model_path):
            dirs[:] = [d for d in dirs if d not in COMFYUI_MODELS_EXCLUDED_DIRS]
            for filename in [f for f in files if f.endswith(tuple(COMFYUI_MODELS_FILETYPES))]:
                print("Found {} model".format(filename))
                models.append(filename)
    return list(set(models))


def list_files(dir, basename, layer="*", frame="*", version="*", extension=DEFAULT_IMAGE_FORMAT):
    basename_pattern = "_".join([basename, layer, frame, version])
    filepath_pattern = str(Path(dir) / (basename_pattern + '_.' + extension))
    filepaths = glob.glob(filepath_pattern)
    return filepaths


def queue_prompt(prompt, client_id, server_address=COMFYUI_SERVER_ADDRESS):
    url = "http://{}/prompt".format(server_address)
    print(url)
    try:
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req =  urllib.request.Request(url, data=data)
        return json.loads(urllib.request.urlopen(req).read())
    except ConnectionRefusedError:
        print("Error - Connection refused at URL {}".format(url))
    except URLError:
        print("Error - Invalid URL {}".format(url))
    return {}


def get_history(prompt_id, server_address=COMFYUI_SERVER_ADDRESS):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())


def interrupt_execution(prompt, client_id, server_address=COMFYUI_SERVER_ADDRESS):
    url = "http://{}/interrupt".format(server_address)
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request(url, data=data)
    r = urllib.request.urlopen(req).read()
    response = {}
    if r:
        response = json.loads(r)
    return response


def pull_message(ws):
    out = ws.recv()
    if isinstance(out, str):
        return json.loads(out) 
    return {}
    
    
def prompt_execution(server_address, client_id, prompt_id):
    def queue_size(message):
        return int(message['data']["status"]["exec_info"]["queue_remaining"]) 
    
    message = {
        "server": {},
        "node": {},
        "node_info": {}
    } 
    try:
        url = "ws://{}/ws?clientId={}&promptId={}".format(server_address, client_id, prompt_id)
        ws = websocket.WebSocket()
        ws.connect(url)
        print("Requesting {}".format(url))
        message["server"] = pull_message(ws)
        if queue_size(message["server"]) > 0:    
            message["node"] = pull_message(ws)
            message["node_info"] = pull_message(ws)
    except ConnectionRefusedError:
        print("Pulling message from server failed")
        return {}
    if message["node_info"] and message["node_info"]['type'] == ComfyUIStatus.ERROR:
        print("Workflow execution on server failed")
        pprint(message["node_info"])
        return {}
    return message


def get_image(filename, subfolder, folder_type, server_address=COMFYUI_SERVER_ADDRESS):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()


def get_images(ws, prompt, server_address=COMFYUI_SERVER_ADDRESS):
    prompt_id = queue_prompt(prompt, server_address=server_address)['prompt_id']
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break 
        else:
            continue 
    output_images = {}
    history = get_history(prompt_id, server_address)[prompt_id]
    for o in history['outputs']:
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for image in node_output['images']:
                    image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                    images_output.append(image_data)
            output_images[node_id] = images_output
    return history
