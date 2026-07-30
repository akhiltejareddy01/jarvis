"""Local embeddings — per Sara_Job_Arch.docx §Stack: "local nomic/bge, 768 dims."

Using BAAI/bge-base-en-v1.5 specifically (768-dim, loads via sentence-transformers
with no special flags — nomic's model needs trust_remote_code and extra deps that
are more fragile to install; bge is the more reliable of the two named options).

First call downloads the model (~440MB) and caches it under ~/.cache/huggingface —
expect a one-time delay.
"""

import os
from functools import lru_cache
from pathlib import Path

# Akhil's C: drive is nearly full (3.6MB free as of 2026-07-27) — redirect the
# HuggingFace model cache to D: before sentence_transformers/transformers pick
# a default under C:\Users\...\.cache. Must happen before the import below.
os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parent.parent.parent / ".cache" / "huggingface"))

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-base-en-v1.5"
DIMENSIONS = 768


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    return _model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True).tolist()
