def chunk_text(t:str, size=1200, overlap=200):
    words = t.split()
    out=[]; i=0
    while i < len(words):
        out.append({"id":len(out), "text":" ".join(words[i:i+size])})
        i += max(1, size - overlap)
    return out

