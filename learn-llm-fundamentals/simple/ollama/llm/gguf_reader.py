"""gguf_reader -- read llama3.2's own model file (the .gguf Ollama downloaded), no extra packages
=============================================================================================

Used by the lessons in this folder to show REAL data instead of made-up numbers:
the vocabulary, the BPE merge rules, the tensor shapes, and real embedding rows.

WHERE THE FILE IS:
  ollama pull llama3.2  ->  ~/.ollama/models/manifests/registry.ollama.ai/library/llama3.2/latest
                            (a small JSON that lists the "layers" of the download)
                        ->  the layer with mediaType "application/vnd.ollama.image.model"
                            points to  ~/.ollama/models/blobs/sha256-<digest>   (~2 GB, the GGUF)

GGUF FILE LAYOUT (version 3):
   ┌───────────────────────────────────────────────┐
   │ "GGUF"  version  tensor_count  kv_count       │  header
   ├───────────────────────────────────────────────┤
   │ key/value metadata (30 entries for llama3.2)  │  llama.block_count = 28,
   │                                               │  tokenizer.ggml.tokens = [128,256 strings],
   │                                               │  tokenizer.ggml.merges = [280,147 rules], ...
   ├───────────────────────────────────────────────┤
   │ tensor table (255 entries)                    │  name, shape, type, offset
   ├───────────────────────────────────────────────┤
   │ tensor data (~2 GB of weights)                │  token_embd.weight, blk.0.attn_q.weight, ...
   └───────────────────────────────────────────────┘
"""

import json
import struct
from pathlib import Path

OLLAMA_MODELS = Path.home() / ".ollama" / "models"

_SCALAR = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
TENSOR_TYPES = {0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 6: "Q5_0", 7: "Q5_1", 8: "Q8_0",
                10: "Q2_K", 11: "Q3_K", 12: "Q4_K", 13: "Q5_K", 14: "Q6_K", 15: "Q8_K", 30: "BF16"}


def find_model_file(model="llama3.2", tag="latest"):
    manifest = OLLAMA_MODELS / "manifests" / "registry.ollama.ai" / "library" / model / tag
    layers = json.loads(manifest.read_text())["layers"]
    digest = next(l["digest"] for l in layers if l["mediaType"].endswith(".model"))
    return OLLAMA_MODELS / "blobs" / digest.replace(":", "-")


def _read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")


def _read_value(f, t):
    if t == 8:
        return _read_str(f)
    if t == 9:                                           # array: element type + count
        et, n = struct.unpack("<IQ", f.read(12))
        return [_read_value(f, et) for _ in range(n)]
    fmt = "<" + _SCALAR[t]
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]


def read_gguf(path=None):
    """Returns (metadata dict, tensor dict, path). Reads only the header -- a few seconds."""
    path = path or find_model_file()
    with open(path, "rb") as f:
        assert f.read(4) == b"GGUF", "not a GGUF file"
        _version, n_tensors, n_kv = struct.unpack("<IQQ", f.read(20))
        meta = {}
        for _ in range(n_kv):
            key = _read_str(f)
            (t,) = struct.unpack("<I", f.read(4))
            meta[key] = _read_value(f, t)
        tensors = {}
        for _ in range(n_tensors):
            name = _read_str(f)
            (n_dims,) = struct.unpack("<I", f.read(4))
            shape = struct.unpack("<" + "Q" * n_dims, f.read(8 * n_dims))
            (t,) = struct.unpack("<I", f.read(4))
            (offset,) = struct.unpack("<Q", f.read(8))
            tensors[name] = {"shape": shape, "type": TENSOR_TYPES.get(t, t), "offset": offset}
        align = meta.get("general.alignment", 32)
        data_start = (f.tell() + align - 1) // align * align
    for t in tensors.values():
        t["offset"] += data_start
    return meta, tensors, path


def bytes_to_unicode():
    """GPT-2's trick: give each of the 256 bytes a VISIBLE character, so the vocabulary can be
    stored as normal strings. Printable bytes keep their own character ('P' -> 'P'); the others
    get 256, 257, ... in order -> space (32) = 'Ġ', newline (10) = 'Ċ', tab (9) = 'ĉ'."""
    keep = (list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1))
            + list(range(ord("®"), ord("ÿ") + 1)))
    table, extra = {}, 0
    for b in range(256):
        if b in keep:
            table[b] = chr(b)
        else:
            table[b] = chr(256 + extra)
            extra += 1
    return table


def read_f32(tensors, path, name):
    """F32 tensors (the norm weights, rope_freqs) are stored unpacked: N little-endian floats."""
    t = tensors[name]
    assert t["type"] == "F32", t["type"]
    n = 1
    for d in t["shape"]:
        n *= d
    with open(path, "rb") as f:
        f.seek(t["offset"])
        return list(struct.unpack(f"<{n}f", f.read(4 * n)))


def _dequantize_q6_k(block):
    """One Q6_K block (210 bytes) -> 256 floats. Same maths as ggml's dequantize_row_q6_K:
    each weight is a 6-bit integer x a per-16 scale x a per-256 scale."""
    ql, qh = block[0:128], block[128:192]
    scales = struct.unpack("<16b", block[192:208])
    (d,) = struct.unpack("<e", block[208:210])           # 'e' = 16-bit float
    out = [0.0] * 256
    for half in range(2):
        y, l_off, h_off, s_off = half * 128, half * 64, half * 32, half * 8
        for l in range(32):
            i = l // 16
            q1 = ((ql[l_off + l] & 0xF) | (((qh[h_off + l] >> 0) & 3) << 4)) - 32
            q2 = ((ql[l_off + l + 32] & 0xF) | (((qh[h_off + l] >> 2) & 3) << 4)) - 32
            q3 = ((ql[l_off + l] >> 4) | (((qh[h_off + l] >> 4) & 3) << 4)) - 32
            q4 = ((ql[l_off + l + 32] >> 4) | (((qh[h_off + l] >> 6) & 3) << 4)) - 32
            out[y + l] = d * scales[s_off + i] * q1
            out[y + l + 32] = d * scales[s_off + i + 2] * q2
            out[y + l + 64] = d * scales[s_off + i + 4] * q3
            out[y + l + 96] = d * scales[s_off + i + 6] * q4
    return out


def embedding_row(token_id, tensors, path):
    """Row `token_id` of token_embd.weight = that token's 3,072 numbers (step 3 / ZOOM A)."""
    t = tensors["token_embd.weight"]
    width, _vocab = t["shape"]                           # (3072, 128256)
    assert t["type"] == "Q6_K", t["type"]
    blocks = width // 256                                # 12 blocks of 256 numbers
    row_bytes = blocks * 210                             # 2,520 bytes per token
    with open(path, "rb") as f:
        f.seek(t["offset"] + token_id * row_bytes)
        raw = f.read(row_bytes)
    row = []
    for b in range(blocks):
        row += _dequantize_q6_k(raw[b * 210:(b + 1) * 210])
    return row
