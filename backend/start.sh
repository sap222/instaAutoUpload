#!/bin/bash

# Install ffmpeg on Render's Linux environment
apt-get update
apt-get install -y ffmpeg

# Make sure Python environment is set up (if you have a virtualenv)
python -m venv .venv
. .venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt

# Start the app with uvicorn
uvicorn main:app --host 0.0.0.0 --port 10000
