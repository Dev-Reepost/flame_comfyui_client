##########################################################################
#
# Filename: comfyui_api_ws.py
#
# Copyright (c) 2024 Julien Martin
# All rights reserved.
#
###########################################################################

import json
import urllib.request
import urllib.parse
from urllib.error import URLError
import websocket 


COMFYUI_HOSTNAME = "192.168.1.14"
COMFYUI_HOSTPORT = "8188"
COMFYUI_SERVER_ADDRESS = COMFYUI_HOSTNAME + ':' + COMFYUI_HOSTPORT

PROGRESS = "progress"
EXECUTING = "executing"
STATUS = "status"


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

def get_image(filename, subfolder, folder_type, server_address=COMFYUI_SERVER_ADDRESS):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

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
        message = json.loads(out) 
        return message
    return {}
    
def prompt_execution(server_address, client_id, prompt_id):
    def queue_size(message):
        return int(message['data']["status"]["exec_info"]["queue_remaining"]) 
    
    message_status = "" 
    try:
        url = "ws://{}/ws?clientId={}".format(server_address, client_id)
        print("Connecting to {}".format(url))
        ws = websocket.WebSocket()
        ws.connect(url)
        message_status = pull_message(ws)
        print("message {}".format(message_status))
        if queue_size(message_status) > 0:
            message_executing = pull_message(ws)
            print("message {}".format(message_executing))
            message_progress = pull_message(ws)
            print("message {}".format(message_progress))
    except ConnectionRefusedError:
        print("Connection refused at URL {}".format(url))
        return {}
    message = message_status
    response = {
        "executing": False,
        "message": message
        }
    if message:
        response["message"] = message
        if message['type'] == EXECUTING:
            data = message['data']
            if data['node'] is not None:
                response["executing"] = True
        elif message['type'] == PROGRESS:
            data = message['data']
            if data['prompt_id'] == prompt_id:
                response["executing"] = True
        elif message['type'] == STATUS:
            if queue_size(message) > 0:                
                response["executing"] = True
    return response


def get_images(ws, prompt, server_address=COMFYUI_SERVER_ADDRESS):
    prompt_id = queue_prompt(prompt, server_address=server_address)['prompt_id']
    
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break # Execution is doen
        else:
            continue # previews are binary data
    
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

#Commented out code to display the output images:
# for node_id in images:
#     for image_data in images[node_id]:
#         from PIL import Image
#         import io
#         image = Image.open(io.BytesIO(image_data))
#         image.show()

