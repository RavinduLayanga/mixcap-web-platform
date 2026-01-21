import torch
import torch.nn as nn
import torch.nn.functional as F

PAD_ID = 4
VOCAB_SIZE = 8000
MAX_POS_LEN = 320

class PositionalEmbedding(nn.Module):
    def __init__(self, max_len: int, dim: int):
        super().__init__()
        self.embed = nn.Embedding(max_len, dim)

    def forward(self, x):
        idx = torch.arange(x.size(1), device=x.device)
        return x + self.embed(idx)[None, :, :]

class CrossAttentionBlock(nn.Module):
    def __init__(self, dim: int, heads: int, dropout: float = 0.1):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, heads, dropout, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.ReLU(),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout)
        )
        self.norm1 = nn.LayerNorm(dim)
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, q, kv, kv_mask=None):
        attn_out, _ = self.attn(q, kv, kv, key_padding_mask=kv_mask)
        x = self.norm1(q + attn_out)
        return self.norm2(x + self.ff(x))

class MixcapEncoder(nn.Module):
    def __init__(self, v_dim=1408, a_dim=1024, f_dim=768, layers=4, heads=8, dropout=0.1):
        super().__init__()
        self.v_proj = nn.Linear(v_dim, f_dim)
        self.a_proj = nn.Linear(a_dim, f_dim)
        self.pe = PositionalEmbedding(MAX_POS_LEN, f_dim)
        self.drop = nn.Dropout(dropout)
        self.v2a = nn.ModuleList([CrossAttentionBlock(f_dim, heads, dropout) for _ in range(layers)])
        self.a2v = nn.ModuleList([CrossAttentionBlock(f_dim, heads, dropout) for _ in range(layers)])

    def forward(self, v, a, v_mask=None, a_mask=None):
        v = self.drop(self.pe(self.v_proj(v)))
        a = self.drop(self.pe(self.a_proj(a)))
        for b_v2a, b_a2v in zip(self.v2a, self.a2v):
            v = b_v2a(v, a, kv_mask=a_mask)
            a = b_a2v(a, v, kv_mask=v_mask)
        return v, a

class CaptionDecoder(nn.Module):
    def __init__(self, f_dim=768, vocab=VOCAB_SIZE, layers=4, heads=8, ff=2048, dropout=0.1):
        super().__init__()
        self.embed = nn.Embedding(vocab, f_dim, padding_idx=PAD_ID)
        self.pe = PositionalEmbedding(MAX_POS_LEN, f_dim)
        dec_layer = nn.TransformerDecoderLayer(f_dim, heads, ff, dropout, batch_first=True)
        self.trans = nn.TransformerDecoder(dec_layer, layers)
        self.out = nn.Linear(f_dim, vocab)

    def _causal_mask(self, T, device):
        return torch.triu(torch.ones((T, T), dtype=torch.bool, device=device), 1)

    def forward(self, tgt, memory, tgt_pad_mask=None, mem_pad_mask=None):
        x = self.pe(self.embed(tgt))
        causal = self._causal_mask(tgt.size(1), tgt.device)
        out = self.trans(x, memory,
                         tgt_mask=causal,
                         tgt_key_padding_mask=tgt_pad_mask,
                         memory_key_padding_mask=mem_pad_mask)
        return self.out(out)

class MixcapModel(nn.Module):
    def __init__(self, fused_dim=768, vocab_size=VOCAB_SIZE):
        super().__init__()
        self.enc = MixcapEncoder(f_dim=fused_dim)
        self.dec = CaptionDecoder(f_dim=fused_dim, vocab=vocab_size)

    def forward(self, v, a, tgt, v_mask=None, a_mask=None, tgt_pad_mask=None):
        v_enc, a_enc = self.enc(v, a, v_mask, a_mask)
        memory = torch.cat([v_enc, a_enc], dim=1)
        mem_pad_mask = torch.cat([v_mask, a_mask], dim=1) if v_mask is not None else None
        return self.dec(tgt, memory, tgt_pad_mask, mem_pad_mask)
