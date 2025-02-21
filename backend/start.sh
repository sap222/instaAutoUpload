#!/bin/bash

apt-get update && apt-get install -y ffmpeg
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 10000
