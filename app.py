import streamlit as st
import json
from utils.scrape import get_text
from utils.chunk import chunk_text
from rag import build_index, retrieve, run_all_prompts

def build_markdown(results):
    """Convert JSON results to formatted markdown."""
    md = "# Spanish Study Materials\n\n"

    for name, output in results.items():
        md += f"## {name.title()}\n\n"

        try:
            data = json.loads(output)

            if name == "vocab" and "vocabulary" in data:
                for item in data["vocabulary"]:
                    md += f"- **{item.get('spanish', '')}** ({item.get('pos', '')}) - {item.get('english', '')}\n"
                    if item.get('example'):
                        md += f"  - *{item['example']}*\n"
                md += "\n"

            elif name == "questions" and "questions" in data:
                for i, q in enumerate(data["questions"], 1):
                    md += f"{i}. **Q:** {q.get('question', '')}\n"
                    md += f"   **A:** {q.get('answer', '')}\n"
                    md += f"   *Difficulty: {q.get('difficulty', '')}*\n\n"

            elif name == "dialogue":
                if "title" in data:
                    md += f"**{data['title']}**\n\n"
                if "lines" in data:
                    for line in data["lines"]:
                        md += f"**{line.get('speaker', '')}:** {line.get('es', '')}\n\n"
                if "glossary" in data:
                    md += "### Glossary\n\n"
                    for word in data["glossary"]:
                        md += f"- {word.get('spanish', '')} - {word.get('english', '')}\n"
                md += "\n"

            elif name == "studyplan" and "plan" in data:
                plan = data["plan"]
                if "vocabulary" in plan:
                    md += "**Vocabulary:**\n"
                    for word in plan["vocabulary"]:
                        md += f"- {word}\n"
                    md += "\n"
                if "grammar" in plan:
                    md += "**Grammar:**\n"
                    for concept in plan["grammar"]:
                        md += f"- {concept}\n"
                    md += "\n"
                if "activities" in plan:
                    md += "**Activities:**\n"
                    for activity in plan["activities"]:
                        md += f"- {activity}\n"
                    md += "\n"
                if "timeline" in plan:
                    md += f"**Timeline:** {plan['timeline']}\n\n"

        except json.JSONDecodeError:
            md += f"```\n{output}\n```\n\n"

    return md

st.set_page_config(page_title="Hola Mundo", page_icon="👋")
st.title("Hola Mundo: Spanish Study Companion")

url = st.text_input("Spanish article URL")
text = st.text_area("Or paste text", height=160)

if st.button("Generate Study Materials"):
    source = text.strip() or url.strip()
    if not source:
        st.warning("Please provide a URL or some text")
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Step 1: Scrape
    status_text.text("Scraping Spanish text...")
    scraped = get_text(source)
    progress_bar.progress(20)

    # Step 2: Chunk
    status_text.text("Processing content...")
    chunks = chunk_text(scraped)
    progress_bar.progress(40)

    # Auto-calculate optimal number of chunks to retrieve
    total_chunks = len(chunks)
    top_k = min(max(int(total_chunks * 0.6), 3), 8)  # 60% of chunks, min 3, max 8

    # Step 3: Build index
    status_text.text("Organizing for analysis...")
    index, _ = build_index(chunks)
    progress_bar.progress(60)

    # Step 4: Retrieve
    status_text.text("Finding key sections...")
    query = "vocabulary and grammar concepts"
    hits = retrieve(chunks, index, query, k=top_k)
    progress_bar.progress(80)

    # Step 5: Generate
    status_text.text("Generating study materials...")
    results = run_all_prompts(hits)
    progress_bar.progress(100)

    # Clear progress and show summary
    progress_bar.empty()
    status_text.empty()

    st.success("✅ Successfully processed Spanish article")
    st.markdown(f"""
    • **{len(scraped):,} characters** analyzed
    • **{len(hits)} key sections** identified
    • **Study materials** generated
    """)

    # Build markdown
    markdown_content = build_markdown(results)

    st.subheader("Study Materials")
    st.markdown(markdown_content)

    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download Markdown",
            data=markdown_content,
            file_name="spanish_study_materials.md",
            mime="text/markdown"
        )
    with col2:
        st.download_button(
            label="Download JSON",
            data=json.dumps(results, indent=2),
            file_name="spanish_study_materials.json",
            mime="application/json"
        )
