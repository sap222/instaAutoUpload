import sys
import os
import time
import traceback
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
import yt_dlp
from typing import List
from queue import Queue

# Debug MoviePy setup
print("Python version:", sys.version)
print("sys.path:", sys.path)

moviepy_path = os.path.join(sys.path[-1], 'moviepy')
if os.path.exists(moviepy_path):
    print(f"moviepy directory exists at {moviepy_path}")
    editor_path = os.path.join(moviepy_path, 'editor.py')
    init_path = os.path.join(moviepy_path, '__init__.py')
    if os.path.exists(editor_path):
        print(f"editor.py exists at {editor_path}")
    else:
        print("editor.py does not exist in moviepy directory")
    if os.path.exists(init_path):
        print("__init__.py exists in moviepy directory")
    else:
        print("__init__.py does not exist in moviepy directory")
else:
    print("moviepy directory does not exist")

try:
    import moviepy.editor as mp
    print("MoviePy imported successfully at:", mp.__file__)
except ImportError as e:
    print("Failed to import moviepy.editor:", e)

import moviepy.config as mp_config
mp_config.FFMPEG_BINARY = "ffmpeg"  # Use system-installed FFmpeg

# Configuration
TEMP_FOLDER = "./temp_videos/"
SESSION_FILE = "instagram_session.json"  # Save session locally (update for persistent storage if needed)
DEFAULT_CAPTION = "#ai "
UPLOAD_DELAY = 300  # 5-minute delay

# Initialize FastAPI
app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instagram Client
cl = Client()

# Load or initialize Instagram session
def load_instagram_session(username: str, password: str = None, verification_code: str = None):
    global cl
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            cl.login()
            print("Logged in using saved session!")
        elif username and password:
            cl.login(username, password, verification_code=verification_code)
            cl.dump_settings(SESSION_FILE)
            print("Logged in and saved new session!")
        else:
            raise Exception("No session file found and no credentials provided.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")

# Video Request Model
class VideoRequest(BaseModel):
    instagram_links: List[str]

# Login Request Model
class LoginRequest(BaseModel):
    username: str
    password: str
    verification_code: str = None  # Optional 2FA code

# Queue for Videos
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

# Login Endpoint
@app.post("/login/")
def login(request: LoginRequest):
    try:
        load_instagram_session(request.username, request.password, request.verification_code)
        return {"status": "success", "message": "Logged in successfully!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Video Processing Endpoint
@app.post("/process_videos/")
def process_videos(request: VideoRequest, background_tasks: BackgroundTasks):
    try:
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
        
        # Ensure we're logged in
        if not cl.pk:  # Check if client is authenticated
            raise HTTPException(status_code=401, detail="Not logged in. Please log in first.")
        
        for link in request.instagram_links:
            video_queue.put(link)
        
        background_tasks.add_task(process_queue)
        return {"status": "success", "message": f"{len(request.instagram_links)} videos queued for upload."}
    except Exception as e:
        print("❌ ERROR:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Health Check Endpoint
@app.get("/")
def health_check():
    return {"status": "healthy", "message": "API is running!"}
