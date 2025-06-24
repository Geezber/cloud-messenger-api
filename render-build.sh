#!/bin/bash
# render-build.sh
set -e  # Exit immediately if any command fails

# Upgrade pip and install wheel
python -m pip install --upgrade pip
pip install wheel

# Install requirements
pip install -r requirements.txt

# Optional: Print installed packages for debugging
pip freeze