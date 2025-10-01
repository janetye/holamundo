from sentence_transformers import SentenceTransformer
import faiss, numpy as np
import streamlit as st
import os
from pathlib import Path
from llm import call_llm

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

def load_prompts(prompts_dir="prompts"):
    """Load all prompt files from the prompts directory."""
    prompts = {}
    prompt_files = Path(prompts_dir).glob("*.txt")
    for file in prompt_files:
        name = file.stem  # filename without extension
        with open(file, 'r') as f:
            prompts[name] = f.read().strip()
    return prompts

def run_all_prompts(context_chunks, level="B1", test_mode=False):
    """Run all prompts through the LLM with the given context."""
    context = "\n\n---\n\n".join([chunk["text"] for chunk in context_chunks])
    prompts = load_prompts()
    results = {}

    for name, prompt_template in prompts.items():
        full_prompt = f"""Context:\n{context}\n\nStudent Level: {level}\n\n{prompt_template}"""
        results[name] = call_llm(full_prompt, test_mode=test_mode)

    return results

def get_sentence_feedback(sentence, target_word, level, test_mode=False):
    """Get grammar feedback and natural language suggestions for a practice sentence."""
    prompt = f"""You are a patient Spanish teacher helping a {level}-level student practice using the word "{target_word}" in a sentence.

Student's sentence: "{sentence}"

Please provide:
1. Grammar feedback - Is the sentence grammatically correct? Point out any errors.
2. Natural language - Suggest a more natural way to say this if needed.
3. Encouragement - Give positive feedback on what they did well.

Keep your response friendly, clear, and concise (3-4 sentences max)."""

    return call_llm(prompt, test_mode=test_mode)

def get_comprehension_feedback(question, student_answer, expected_answer, level, test_mode=False):
    """Get feedback on a comprehension question answer."""
    prompt = f"""You are a patient Spanish teacher helping a {level}-level student with comprehension.

Question: {question}
Expected answer: {expected_answer}
Student's answer: "{student_answer}"

Please provide:
1. Accuracy - Is their answer correct? If not, gently explain what they missed.
2. Language quality - Comment on their Spanish grammar and vocabulary.
3. Encouragement - Give positive feedback and suggest how to improve.

Keep your response friendly, clear, and concise (3-4 sentences max)."""

    return call_llm(prompt, test_mode=test_mode)

