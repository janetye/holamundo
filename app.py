import streamlit as st
from utils.scrape import get_text
from utils.chunk import chunk_text
from rag import build_index, retrieve

st.set_page_config(page_title="Hola Mundo", page_icon="👋")
st.title("Hola Mundo: Spanish Study Companion")

url = st.text_input("Spanish article URL")
text = st.text_area("Or paste text", height=160)
top_k = st.slider("Number of chunks", 1, 8, 5)

if st.button("Scrape, index, retrieve"):
    source = text.strip() or url.strip()
    if not source:
        st.warning("Please provide a URL or some text")
        st.stop()

    scraped = get_text(source)
    st.write(f"✅ Scraped text length: **{len(scraped)} characters**")

    chunks = chunk_text(scraped)
    st.write(f"✅ Created **{len(chunks)} chunks**")

    index, _ = build_index(chunks)
    st.success("FAISS index built")

    query = "vocabulary extraction"
    hits = retrieve(chunks, index, query, k=top_k)

    st.subheader("First retrieved chunk preview")
    st.caption(f'Query: "{query}"  •  Showing 1 of {len(hits)}')
    st.text_area("Chunk 0", hits[0]["text"][:2000], height=180)
