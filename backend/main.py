import os
import time
import traceback
import random
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from instagrapi import Client
import yt_dlp
from typing import List, Optional
from queue import Queue

# Configuration
TEMP_FOLDER = "./temp_videos/"  # Where downloaded videos are stored temporarily
SESSION_FILE = "instagram_session.json"  # File to save Instagram session
HASHTAGS = [
    "#automation", "#software", "#saas", "#agency", "#smma", "#highlevel", "#deepseek",
    "#aiautomationagency", "#freevalue", "#explorepage", "#instagram", "#trending", "#viral",
    "#memes", "#instagood", "#instadaily", "#trendingreels", "#trend", "#instalike",
    "#dailymemes", "#tech", "#trump"
]

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Instagram client
cl = Client()

# Models for API requests
class VideoRequest(BaseModel):
    video_links: List[str]  # Changed from instagram_links to video_links for generality

class LoginRequest(BaseModel):
    username: str
    password: str
    verification_code: Optional[str] = None  # Optional 2FA code

# Queue for video processing
video_queue = Queue()

# Instagram session management
def load_instagram_session(username: str, password: str = None, verification_code: str = None):
    """Load or create an Instagram session."""
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

# Download function
def download_video(video_url):
    """Downloads a video from various platforms to a temporary folder with retries."""
    print(f"🎬 Attempting to download: {video_url}")
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_FOLDER, '%(id)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'retries': 3,
        'noplaylist': True,
        'quiet': False,
    }
    
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_path = ydl.prepare_filename(info).replace(".webm", ".mp4")
            
            if not os.path.exists(video_path):
                raise FileNotFoundError("Download failed, video not found!")
            
            print(f"✅ Downloaded successfully: {video_path}")
            return video_path
        except Exception as e:
            print(f"⚠️ Download attempt {attempt + 1} failed for {video_url}: {e}")
            time.sleep(2)
            if attempt == 2:
                raise FileNotFoundError(f"❌ Failed to download {video_url} after 3 attempts: {e}")

# Caption generation
def get_random_caption():
    """Generates a random caption with 10-16 random hashtags."""
    num_hashtags = random.randint(15, 19)
    selected_hashtags = random.sample(HASHTAGS, num_hashtags)
    return " ".join(selected_hashtags)

# Upload function
def upload_to_instagram(video_path):
    """Uploads the video to Instagram and deletes it after upload."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File {video_path} not found for upload!")
    
    caption = get_random_caption()
    cl.video_upload(video_path, caption)
    print(f"✅ Uploaded: {video_path} with caption: {caption}")
    os.remove(video_path)
    print(f"🗑 Deleted: {video_path}")

# Queue processing with delay
def process_queue():
    """Processes videos from the queue one by one with a random delay (40-70 mins)."""
    while not video_queue.empty():
        try:
            video_url = video_queue.get()
            print(f"📥 Processing video from queue: {video_url}")
            video_path = download_video(video_url)
            upload_to_instagram(video_path)
            print(f"✔️ Completed: {video_path}")
            
            # Random delay between 40 and 70 minutes (converted to seconds)
            delay_minutes = random.uniform(60, 120)
            delay_seconds = delay_minutes * 60
            print(f"⏳ Waiting {delay_minutes:.2f} minutes ({delay_seconds:.0f} seconds) before next upload...")
            time.sleep(delay_seconds)
        except Exception as e:
            print(f"❌ Error processing {video_url}: {e}")
            traceback.print_exc()
            continue

# Login endpoint
@app.post("/login/")
async def login(login_request: LoginRequest):
    """Log in to Instagram."""
    try:
        load_instagram_session(login_request.username, login_request.password, login_request.verification_code)
        return {"status": "success", "message": "Logged in successfully!"}
    except HTTPException as e:
        raise e
    except Exception as e:
        print("❌ ERROR:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Video processing endpoint
@app.post("/process_videos/")
async def process_videos(request: VideoRequest, background_tasks: BackgroundTasks):
    """Queue video links for download and upload."""
    try:
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)
            print(f"📁 Created temp folder: {TEMP_FOLDER}")
        
        # Ensure Instagram client is logged in
        if not cl.user_id:
            raise HTTPException(status_code=401, detail="Not logged in. Please log in first.")
        
        for link in request.video_links:
            video_queue.put(link)
            print(f"➕ Added to queue: {link}")
        
        background_tasks.add_task(process_queue)
        return {
            "status": "success",
            "message": f"{len(request.video_links)} videos queued for download and upload."
        }
    except Exception as e:
        print(f"❌ Error in process_videos: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")

# Health check endpoint for external pinging
@app.get("/health")
async def health_check():
    """Check if the API is running for external pinging."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
