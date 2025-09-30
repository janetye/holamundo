import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_llm(prompt, model=os.getenv("MODEL_NAME", "claude-3-5-haiku-20241022")):
    """Call Claude with a prompt. The LLM acts as a patient and precise Spanish teacher."""
    system = "You are a patient and precise Spanish teacher. Help students understand Spanish language, grammar, vocabulary, and culture clearly and thoroughly."

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.content[0].text

