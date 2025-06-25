#!/usr/bin/env bash
# build.sh
set -o errexit

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt