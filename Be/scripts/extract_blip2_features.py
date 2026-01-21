import os, glob, torch, numpy as np
from PIL import Image
from transformers import Blip2Processor, Blip2Model

# ==== PATHS ====
FRAME_DIR = "features/video"
OUTPUT_DIR = "features/video"
MODEL_PATH = "models/blip2-opt-2"  # Local model

# ==== Load Model & Processor ====
processor = Blip2Processor.from_pretrained(MODEL_PATH)
model = Blip2Model.from_pretrained(MODEL_PATH, torch_dtype=torch.float16).to("cpu").eval()

def extract_blip2_features(video_id):
    """
    Extract BLIP-2 CLS token features from all frames of a video and save as [T_v, 1408] .npy
    """
    folder = os.path.join(FRAME_DIR, video_id)
    frame_paths = sorted(glob.glob(os.path.join(folder, "*.jpg")))

    if not frame_paths:
        raise RuntimeError(f"No frames found in {folder}")

    all_feats = []

    # Process in mini-batches of 8
    for i in range(0, len(frame_paths), 8):
        imgs = [Image.open(p).convert("RGB") for p in frame_paths[i:i+8]]
        inputs = processor(images=imgs, return_tensors="pt", padding=True).to("cpu", torch.float16)
        with torch.no_grad():
            outputs = model.vision_model(**inputs)
            cls_feats = outputs.last_hidden_state[:, 0, :].float()  # CLS token per frame
            all_feats.append(cls_feats)

    feat_tensor = torch.cat(all_feats, dim=0)  # [T_v, 1408]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_path = os.path.join(OUTPUT_DIR, f"{video_id}_video.npy")
    np.save(save_path, feat_tensor.cpu().numpy())
    print(f"[BLIP-2] Saved to {save_path}")
