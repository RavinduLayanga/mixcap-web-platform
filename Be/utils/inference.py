import os
import torch
import numpy as np
import sentencepiece as spm
from utils.model import MixcapModel

# === Configuration ===
DEVICE = "cpu"  
PAD, SOS, EOS = 4, 5, 6
FUSED_DIM = 768  
MAX_LEN = 30

# === Load Tokenizer ===
sp = spm.SentencePieceProcessor(model_file="tokenizer/spm_model.model")
VOCAB_SIZE = sp.get_piece_size()

# === Load Model ===
model = MixcapModel(fused_dim=FUSED_DIM, vocab_size=VOCAB_SIZE).to(DEVICE)

MODEL_PATH = "models/MixCap/MixCap_model_only.pth"
checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
model.load_state_dict(checkpoint)
model.eval()

# === Caption Generation ===
def generate_caption(video_id: str):
    try:
        # === Load Features ===
        video_path = f"features/video/{video_id}_video.npy"
        audio_path = f"features/audio/{video_id}_audio.npy"

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Missing video features: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Missing audio features: {audio_path}")

        video_feat = np.load(video_path)  
        audio_feat = np.load(audio_path)  

        if len(audio_feat.shape) == 1:
            audio_feat = np.expand_dims(audio_feat, 0)  # [1, 1024]

        # === Convert to Tensors ===
        v = torch.tensor(video_feat, dtype=torch.float32).unsqueeze(0).to(DEVICE)  # [1, T_v, 1408]
        a = torch.tensor(audio_feat, dtype=torch.float32).unsqueeze(0).to(DEVICE)  # [1, 1, 1024] or [1, T_a, 1024]

        # === Decoder Start Token ===
        tgt = torch.tensor([[SOS]], dtype=torch.long, device=DEVICE)

        for _ in range(MAX_LEN):
            tgt_pad_mask = tgt.eq(PAD)
            logits = model(v, a, tgt, tgt_pad_mask=tgt_pad_mask)
            next_token = logits[:, -1].argmax(-1, keepdim=True)
            tgt = torch.cat([tgt, next_token], dim=1)
            if next_token.item() == EOS:
                break

        tokens = [t for t in tgt.squeeze().tolist() if t not in [PAD, SOS, EOS]]
        caption = sp.decode(tokens)
        return caption or "No meaningful caption generated."

    except Exception as e:
        print("[ERROR] Inference failed:", str(e))
        raise RuntimeError(f"Inference failed: {str(e)}")
