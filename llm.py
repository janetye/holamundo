import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Try st.secrets first (for Streamlit Cloud), fall back to env var (for local)
try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
except Exception:
    api_key = os.getenv("ANTHROPIC_API_KEY")

client = Anthropic(api_key=api_key)

def get_mock_data(prompt):
    """Return mock data for testing without calling the LLM."""
    if "comprehension" in prompt.lower() and "Student's answer" in prompt:
        # Feedback for comprehension questions
        return "Good effort! Your answer captures the main idea correctly. Your Spanish grammar is solid, though you could use 'es sobre' instead of 'trata de' for a more natural expression. Keep practicing - your comprehension skills are improving!"
    elif "Spanish teacher" in prompt and "Student's sentence" in prompt:
        # Feedback for practice sentences
        return "Great job using the word! Your sentence is grammatically correct. A more natural way to say this might be: 'Me gusta correr cada mañana en el parque.' Keep up the good work - you're using the verb correctly!"
    elif "vocabulary" in prompt.lower() or "vocab" in prompt.lower():
        return json.dumps({
            "vocabulary": [
                {"spanish": "casa", "english": "house", "pos": "noun", "example": "Mi casa es grande."},
                {"spanish": "correr", "english": "to run", "pos": "verb", "example": "Me gusta correr por la mañana."},
                {"spanish": "rápido", "english": "fast", "pos": "adjective", "example": "El coche es muy rápido."},
                {"spanish": "caminar", "english": "to walk", "pos": "verb", "example": "Prefiero caminar al trabajo."},
                {"spanish": "comida", "english": "food", "pos": "noun", "example": "La comida española es deliciosa."},
            ]
        })
    elif "dialogue" in prompt.lower():
        return json.dumps({
            "title": "En el Mercado",
            "lines": [
                {"speaker": "A", "es": "Buenos días, ¿cuánto cuesta el tomate?"},
                {"speaker": "B", "es": "Dos euros el kilo."},
                {"speaker": "A", "es": "Perfecto, quiero dos kilos por favor."},
                {"speaker": "B", "es": "Aquí tiene. ¿Algo más?"},
            ],
            "glossary": [
                {"spanish": "cuánto cuesta", "english": "how much does it cost"},
                {"spanish": "el kilo", "english": "the kilogram"},
            ]
        })
    elif "question" in prompt.lower():
        return json.dumps({
            "questions": [
                {"question": "¿Cuál es el tema principal del texto?", "answer": "El tema principal es...", "difficulty": "intermediate"},
                {"question": "¿Qué significa la palabra 'casa'?", "answer": "Casa significa house en inglés.", "difficulty": "beginner"},
                {"question": "¿Por qué se usa el subjuntivo aquí?", "answer": "Se usa el subjuntivo para expresar...", "difficulty": "advanced"},
            ]
        })
    else:
        return json.dumps({"message": "Mock data for testing"})

def call_llm(prompt, model=os.getenv("MODEL_NAME", "claude-3-5-haiku-20241022"), test_mode=False):
    """Call Claude with a prompt. The LLM acts as a patient and precise Spanish teacher."""
    if test_mode:
        return get_mock_data(prompt)

    system = "You are a patient and precise Spanish teacher. Help students understand Spanish language, grammar, vocabulary, and culture clearly and thoroughly."

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.content[0].text

