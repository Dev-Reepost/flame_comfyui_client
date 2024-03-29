#!/bin/bash
# Install script of ComfyUI Websockets-based client for Autodesk Flame / Flare

AUTODESK_PATH='/opt/Autodesk/'
PYBOX_DIR="$AUTODESK_PATH/shared/presets/pybox"

echo "____________________________________________________"
echo "Installing ComfyUI client for Autodesk Flame / Pybox"
echo "____________________________________________________"

echo "Installing additional required Python libraries..."
pip=`find $AUTODESK_PATH/python -name pip3`
eval '$pip install -r requirements.txt'

comfyui_client_filename=comfyui_client.py
echo "Copying $comfyui_client_filename to $PYBOX_DIR"
cp $comfyui_client_filename $PYBOX_DIR

echo "Installation terminated" 
