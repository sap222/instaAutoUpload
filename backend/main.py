import sys
print("Python version:", sys.version)
print("sys.path:", sys.path)
import moviepy.editor as mp
print("MoviePy is installed!")

import moviepy.config as mp_config
mp_config.FFMPEG_BINARY = "ffmpeg"  # Use system-installed FFmpeg
print("MoviePy is working!")

import yt_dlp
import os
import time
import traceback
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
from typing import List
from queue import Queue

# ✅ Configuration
TEMP_FOLDER = "./temp_videos/"  # Relative path for Render
USERNAME = "mehmoood_safdar"
PASSWORD = "facebook1032"
DEFAULT_CAPTION = "#ai "
UPLOAD_DELAY = 300  # ⏳ 5-minute (300 seconds) delay

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Enable CORS for Frontend Requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Instagram Login
cl = Client()
cl.login(USERNAME, PASSWORD)

# ✅ Video Request Model
class VideoRequest(BaseModel):
    instagram_links: List[str]

# ✅ Queue for Videos
video_queue = Queue()

def download_instagram_video(video_url):
    """Downloads an Instagram video to a temporary folder."""
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_FOLDER, '%(id)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        video_path = ydl.prepare_filename(info).replace(".webm", ".mp4")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError("Download failed, video not found!")

    return video_path

def upload_to_instagram(video_path):
    """Uploads the video to Instagram and deletes it after upload."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File {video_path} not found for upload!")
    
    cl.video_upload(video_path, DEFAULT_CAPTION)
    print(f"✅ Uploaded: {video_path}")

    os.remove(video_path)
    print(f"🗑 Deleted: {video_path}")

def process_queue():
    """Processes videos from the queue one by one with a delay."""
    while not video_queue.empty():
        try:
            video_url = video_queue.get()
            print(f"🎬 Processing: {video_url}")

            video_path = download_instagram_video(video_url)
            print(f"✅ Downloaded: {video_path}")

            upload_to_instagram(video_path)
            print(f"✅ Uploaded Successfully: {video_path}")

            print(f"⏳ Waiting {UPLOAD_DELAY} seconds before next upload...")
            time.sleep(UPLOAD_DELAY)

        except Exception as e:
            print("❌ ERROR:", e)
            traceback.print_exc()

@app.post("/process_videos/")
def process_videos(request: VideoRequest, background_tasks: BackgroundTasks):
    """API endpoint to queue and schedule uploads."""
    try:
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)

        for link in request.instagram_links:
            video_queue.put(link)

        # ✅ Run queue processor in the background
        background_tasks.add_task(process_queue)

        return {"status": "success", "message": f"{len(request.instagram_links)} videos queued for upload."}

    except Exception as e:
        print("❌ ERROR:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Optional: Health check endpoint
@app.get("/")
def health_check():
    return {"status": "healthy", "message": "API is running!"}
