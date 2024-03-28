#!/bin/bash
# Install ComfyUI websockets-based client API for Autodesk Flame / Flare

AUTODESK_PATH='/opt/Autodesk/'
PYBOX_DIR=$AUTODESK_PATH/shared/presets/pybox

echo "______________________________________________________________"
echo "ComfyUI websockets-based client aPI for Autodesk Flame / Pybox"
echo "______________________________________________________________"

echo "Installing additional required Python libraries..."
pip=`find $AUTODESK_PATH/python -name pip3`
eval '$pip install -r requirements.txt'

echo "Copying Python module to $PYBOX_DIR"
cp comfyui_api_ws.api $PYBOX_DIR

echo "Installation terminated" 
