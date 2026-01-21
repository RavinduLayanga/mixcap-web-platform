from flask import Flask, request, jsonify
from flask_cors import CORS 
from werkzeug.utils import secure_filename
import os
import csv
import re

# === Internal module imports ===
from scripts.extract_frames_audio import extract_audio_frames_ffmpeg
from scripts.extract_blip2_features import extract_blip2_features
from scripts.extract_wav2vec2_features import extract_wav2vec2_features
from utils.inference import generate_caption

# === Configurations ===
UPLOAD_DIR = "uploads"
FEATURE_DIR_VIDEO = "features/video"
FEATURE_DIR_AUDIO = "features/audio"
SAVE_FILE = "saved_captions.csv"  

# === App Initialization ===
app = Flask(__name__)
CORS(app)  
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Routes ===
@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "Server is running!"})


@app.route("/upload", methods=["POST"])
def upload_video():
    print("Upload endpoint hit")
    video = request.files.get("video")
    if not video:
        return jsonify({"error": "No video uploaded"}), 400

    # filename = secure_filename(video.filename)
    filename = secure_filename(video.filename).replace(" ", "_")
    save_path = os.path.join(UPLOAD_DIR, filename)
    video.save(save_path)

    return jsonify({"message": "Upload successful", "filename": filename})


@app.route("/extract_features", methods=["POST"])
def extract_features():
    print("Feature extraction endpoint hit")
    data = request.get_json()
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    # video_id = os.path.splitext(filename)[0]
    
    video_id = re.sub(r'[^\w\-]', '_', os.path.splitext(filename)[0])

    video_path = os.path.join(UPLOAD_DIR, filename)

    try:
        extract_audio_frames_ffmpeg(video_path, video_id)
        extract_blip2_features(video_id)
        extract_wav2vec2_features(video_id)
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return jsonify({"error": f"Feature extraction failed: {str(e)}"}), 500

    return jsonify({"message": "Feature extraction complete", "video_id": video_id})


@app.route("/generate_caption", methods=["POST"])
def caption_route():
    print("Caption generation endpoint hit")
    data = request.get_json()
    video_id = re.sub(r'[^\w\-]', '_', os.path.splitext(data.get("filename", ""))[0])

    if not video_id:
        return jsonify({"error": "Missing video ID"}), 400

    try:
        caption = generate_caption(video_id)
    except Exception as e:
        print(f"Inference error: {e}")
        return jsonify({"error": f"Inference failed: {str(e)}"}), 500

    return jsonify({"caption": caption})


@app.route("/save_caption", methods=["POST"])
def save_caption():
    print("Save caption endpoint hit")
    data = request.get_json()
    filename = data.get("filename")
    caption = data.get("caption")

    if not filename or not caption:
        return jsonify({"error": "Missing filename or caption"}), 400

    try:
        file_exists = os.path.isfile(SAVE_FILE)
        with open(SAVE_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Filename", "Caption"])  
            writer.writerow([filename, caption])
    except Exception as e:
        print(f"Save error: {e}")
        return jsonify({"error": f"Failed to save: {str(e)}"}), 500

    return jsonify({"message": "Caption saved successfully"})


# === Entry Point ===
if __name__ == "__main__":
    app.run(debug=True)
