import streamlit as st

st.set_page_config(page_title="Hola Mundo", page_icon="👋")
st.title("Hola Mundo: Spanish Study Companion")
st.write("Paste a Spanish article URL or text, pick level, click Generate.")

url = st.text_input("URL")
text = st.text_area("Or paste text", height=150)
if st.button("Generate"):
    st.success("App running. Next step is wiring RAG.")

