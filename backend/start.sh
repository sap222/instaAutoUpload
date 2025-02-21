#!/bin/bash
chmod +x D:/ffmpeg-7.1-essentials_build/ffmpeg-7.1-essentials_build/bin/ffmpeg.exe
uvicorn main:app --host 0.0.0.0 --port 10000
