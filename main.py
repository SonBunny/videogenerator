import os
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from moviepy.editor import VideoFileClip, concatenate_videoclips
import re
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8081",   # Expo default port
    "http://http://192.168.1.108:8081",  # Your deployed frontend URL
    "*",  # You can allow all origins for testing, but better to restrict in prod
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # or ["GET", "POST", "OPTIONS"]
    allow_headers=["*"],  # or specify needed headers like ["Authorization", "Content-Type"]
)

VIDEO_DIR = "stock_videos"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_filename(title: str):
    return re.sub(r'[^a-zA-Z0-9_]', '_', title.lower().strip())

class VideoRequest(BaseModel):
    title: str
    instructions: List[str]

@app.post("/generate-video")
def generate_video(data: VideoRequest):
    title = data.title
    instructions = data.instructions

    filename = f"{safe_filename(title)}.mp4"
    output_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(output_path):
        # Video already exists, return its URL path
        return {"message": "Video already exists", "video_url": f"/videos/{filename}"}

    keywords = [k.strip().lower() for k in ",".join(instructions).split(",")]
    matched_files = []

    for keyword in keywords:
        for video_file in os.listdir(VIDEO_DIR):
            if keyword in video_file.lower():
                matched_files.append(os.path.join(VIDEO_DIR, video_file))
                break

    if not matched_files:
        raise HTTPException(status_code=404, detail="No matching video files found.")

    clips = [VideoFileClip(path) for path in matched_files]
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_path, codec="libx264", fps=24)

    return {"message": "Video created!", "video_url": f"/videos/{filename}"}

@app.get("/videos/{video_name}")
def get_video(video_name: str):
    video_path = os.path.join(OUTPUT_DIR, video_name)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(video_path, media_type="video/mp4")