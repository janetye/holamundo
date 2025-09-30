import requests
from bs4 import BeautifulSoup

def get_text(source:str)->str:
    if source.startswith("http"):
        html = requests.get(source, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script","style","nav","footer","header"]): s.decompose()
        return " ".join(soup.get_text(" ").split())
    return source

