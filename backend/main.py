import yt_dlp
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
from typing import List

# Configuration
TEMP_FOLDER = "/tmp/"  # Temporary storage (free deployment)
USERNAME = "mehmoood_safdar"
PASSWORD = "facebook1032"
DEFAULT_CAPTION = "#ai "  # Use this caption for all uploads
UPLOAD_DELAY = 120  # 2 minutes delay between uploads to prevent flagging

# FastAPI App
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Instagram Login
cl = Client()
cl.login(USERNAME, PASSWORD)

class VideoRequest(BaseModel):
    instagram_links: List[str]  # Accept multiple links

def download_instagram_video(video_url):
    """Downloads an Instagram video to a temporary folder."""
    ydl_opts = {
        'outtmpl': f'{TEMP_FOLDER}%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        video_path = ydl.prepare_filename(info)
    
    return video_path

def upload_to_instagram(video_path):
    """Uploads the downloaded video to Instagram and deletes it after upload."""
    cl.video_upload(video_path, DEFAULT_CAPTION)
    print(f"Uploaded: {video_path}")
    os.remove(video_path)  # Delete video after upload

@app.post("/process_videos/")
def process_videos(request: VideoRequest):
    """API endpoint to process multiple videos with delay."""
    try:
        for index, link in enumerate(request.instagram_links):
            print(f"Processing video {index + 1}/{len(request.instagram_links)}")
            video_path = download_instagram_video(link)
            upload_to_instagram(video_path)
            if index < len(request.instagram_links) - 1:
                print(f"Waiting {UPLOAD_DELAY} seconds before next upload...")
                time.sleep(UPLOAD_DELAY)  # Delay between uploads
        return {"status": "success", "message": "All videos uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
