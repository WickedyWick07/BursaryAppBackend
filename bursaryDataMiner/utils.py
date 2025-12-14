# bursaryDataMiner/utils.py

from sentence_transformers import SentenceTransformer

# load embedding model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str):
    """Generate vector embeddings for bursary descriptions"""
    if not text:
        return None
    return model.encode(text).tolist()
