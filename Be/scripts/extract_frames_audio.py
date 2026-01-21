import os
import subprocess

FRAME_DIR = "features/video"
AUDIO_DIR = "features/audio"
FPS = 1
RES = 256

def extract_audio_frames_ffmpeg(video_path: str, video_id: str):
    frame_out_dir = os.path.join(FRAME_DIR, video_id)
    audio_out_path = os.path.join(AUDIO_DIR, f"{video_id}.wav")

    os.makedirs(frame_out_dir, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Extract frames
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps={FPS},scale={RES}:{RES}",
        os.path.join(frame_out_dir, "frame_%04d.jpg")
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Extract audio
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-ac", "1", "-ar", "16000", "-vn", audio_out_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
