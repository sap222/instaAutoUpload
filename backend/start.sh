#!/bin/bash

# Set up the Python environment
python -m venv .venv
. .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Manually install moviepy if it's still not working
pip install moviepy

# Start the application with uvicorn
uvicorn main:app --host 0.0.0.0 --port 10000
