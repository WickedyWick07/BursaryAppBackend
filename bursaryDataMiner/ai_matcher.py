from sentence_transformers import SentenceTransformer
import numpy as np 

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None

def get_model():
    global _model
    if _model is None: 
        _model = SentenceTransformer(_MODEL_NAME)
    return _model

def embed_text(text:str) -> list[float]:
    text = (text or "").strip()
    if not text:
        return []
    model = get_model()
    vec = model.encode(text, normalize_embedding=True)
    return vec.astype(float).tolist()

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_bursary_corpus(bursary) -> str:
    parts = [
        bursary.title or "",
        bursary.description or "",
        bursary.url or "", 
    ]
    return "\n".join(p.strip() for p in parts if p)