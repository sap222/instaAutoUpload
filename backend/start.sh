#!/bin/bash

# Install ffmpeg as root
sudo apt-get update
sudo apt-get install -y ffmpeg

# Set up the Python environment
python -m venv .venv
. .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the application with uvicorn
uvicorn main:app --host 0.0.0.0 --port 10000
