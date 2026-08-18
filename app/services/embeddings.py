"""Product/catalog semantic search embeddings.

Providers (env-driven, see ``EMBEDDING_PROVIDER``):

* ``hash`` (default): dependency-free deterministic bag-of-words hashing
  into a fixed-dimension vector. Works offline and in tests; good enough
  for demo/CI, weaker than a real model.
* ``api``: any OpenAI-compatible ``/embeddings`` endpoint — OpenAI, or
  self-hosted Ollama/LocalAI. Configure ``EMBEDDING_BASE_URL`` and
  ``EMBEDDING_API_KEY`` (empty key for Ollama).
* ``none``: embeddings disabled; searches return 400 with a clear error.

The vector dimension must match the ``products.embedding`` column
(``EMBEDDING_DIM``, default 384).
"""

import hashlib
import logging

# pyrefly: ignore [missing-import]
from app.core.config import settings

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if t.isalnum()]


def _embed_hash(text: str, dim: int) -> list[float]:
    """Deterministic bag-of-words hashing into a unit vector."""
    vector = [0.0] * dim
    for token in _tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = sum(v * v for v in vector) ** 0.5
    if norm == 0:
        return vector
    return [v / norm for v in vector]


def _embed_api(text: str, dim: int) -> list[float]:
    import requests

    base_url = settings.EMBEDDING_BASE_URL.rstrip("/")
    url = f"{base_url}/embeddings"
    headers = {"Content-Type": "application/json"}
    if settings.EMBEDDING_API_KEY:
        headers["Authorization"] = f"Bearer {settings.EMBEDDING_API_KEY}"
    payload = {"model": settings.EMBEDDING_MODEL, "input": text}
    response = requests.post(url, json=payload, headers=headers, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        if "data" in data and data["data"]:
            embedding = data["data"][0].get("embedding")
            if embedding is not None:
                return list(embedding)
        if "embedding" in data:
            return list(data["embedding"])
    raise RuntimeError(f"Unrecognized embeddings response shape: {data}")


def embed_text(text: str) -> list[float] | None:
    """Embed a single text; ``None`` when embeddings are disabled."""
    if settings.EMBEDDING_PROVIDER == "none":
        return None
    text = (text or "").strip()
    if not text:
        return None
    try:
        if settings.EMBEDDING_PROVIDER == "api":
            return _embed_api(text, settings.EMBEDDING_DIM)
        return _embed_hash(text, settings.EMBEDDING_DIM)
    except Exception as exc:  # noqa: BLE001 - embedding must never break a sale
        logger.warning("embedding failed: %s", exc)
        return None
