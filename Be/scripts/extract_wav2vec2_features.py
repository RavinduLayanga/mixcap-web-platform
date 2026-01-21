import os
import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2Model

AUDIO_DIR = "features/audio"

# Load model
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h").to("cpu").eval()

def extract_wav2vec2_features(video_id):
    audio_path = os.path.join(AUDIO_DIR, f"{video_id}.wav")
    out_path = os.path.join(AUDIO_DIR, f"{video_id}_audio.npy")

    # Check if audio file exists
    if not os.path.exists(audio_path):
        print(f"[WARN] No audio file found for {video_id}. Using zero vector as fallback.")
        np.save(out_path, np.zeros((1024,), dtype=np.float32))
        return

    # Load audio
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)(waveform)

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # Extract features
    inputs = processor(waveform.squeeze(0), sampling_rate=16000, return_tensors="pt", padding=True).to("cpu")
    with torch.no_grad():
        feat = model(inputs.input_values).last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

    # Pad to 1024D
    padded = np.zeros(1024, dtype=np.float32)
    padded[:min(768, len(feat))] = feat[:min(768, len(feat))]

    np.save(out_path, padded)
    print(f"[Wav2Vec2] Saved to {out_path}")
