from sentence_transformers import SentenceTransformer
import faiss, numpy as np
import streamlit as st

@st.cache_resource
def get_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

@st.cache_data
def embed_chunks(chunks):
    model = get_model()
    return model.encode([c["text"] for c in chunks], normalize_embeddings=True)

def build_index(chunks):
    vecs = embed_chunks(chunks)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(np.array(vecs).astype("float32"))
    return index, vecs

def retrieve(chunks, index, query, k=5):
    model = get_model()
    qv = model.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, k)
    return [chunks[i] for i in I[0]]

