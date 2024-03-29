#!/bin/bash
# Install ComfyUI websockets-based client API for Autodesk Flame / Flare

AUTODESK_PATH='/opt/Autodesk/'
PYBOX_DIR="$AUTODESK_PATH/shared/presets/pybox"

echo "____________________________________________________"
echo "Installing ComfyUI client for Autodesk Flame / Pybox"
echo "____________________________________________________"

echo "Installing additional required Python libraries..."
pip=`find $AUTODESK_PATH/python -name pip3`
#eval '$pip install -r requirements.txt'
echo "$pip install -r requirements.txt"

echo "Copying Python module to $PYBOX_DIR"
#cp comfyui_api_ws.api $PYBOX_DIR

echo "Installation terminated" 
