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

# Initialize session state for results
if 'results' not in st.session_state:
    st.session_state.results = None
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = None

level = st.selectbox("Your Spanish Level", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)
test_mode = st.checkbox("🧪 Test Mode (skip LLM calls)", value=False)
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
    st.session_state.results = run_all_prompts(hits, level=level, test_mode=test_mode)
    progress_bar.progress(100)

    # Clear progress and show summary
    progress_bar.empty()
    status_text.empty()

    st.success(f"✅ Successfully processed Spanish article  •  {len(scraped):,} characters analyzed  •  {len(hits)} sections identified")

    # Build markdown
    st.session_state.markdown_content = build_markdown(st.session_state.results)

    # Reset flashcard state when new materials are generated
    st.session_state.card_index = 0
    st.session_state.show_answer = False
    st.session_state.known_cards = set()

# Display results if they exist
if st.session_state.results:
    # Flashcard mode for vocabulary
    if "vocab" in st.session_state.results:
        st.markdown("### 📚 Vocabulary Flashcards")
        try:
            vocab_data = json.loads(st.session_state.results["vocab"])
            if "vocabulary" in vocab_data:
                all_vocab = vocab_data["vocabulary"]

                # Initialize session state
                if 'card_index' not in st.session_state:
                    st.session_state.card_index = 0
                if 'show_answer' not in st.session_state:
                    st.session_state.show_answer = False
                if 'known_cards' not in st.session_state:
                    st.session_state.known_cards = set()

                # Filter out known cards and keep track of original indices
                vocab_with_indices = [(i, card) for i, card in enumerate(all_vocab) if i not in st.session_state.known_cards]
                total_original = len(all_vocab)
                total_remaining = len(vocab_with_indices)

                # Check if all cards are mastered
                if total_remaining == 0:
                    st.success("🎉 Congratulations! You've mastered all vocabulary words!")
                    st.balloons()
                else:
                    # Make sure card_index is valid
                    if st.session_state.card_index >= total_remaining:
                        st.session_state.card_index = 0

                    # Get current card and its original index
                    original_index, current_card = vocab_with_indices[st.session_state.card_index]

                    # Progress indicator
                    progress = len(st.session_state.known_cards) / total_original
                    st.progress(progress)
                    st.caption(f"Card {st.session_state.card_index + 1}/{total_remaining}  •  {len(st.session_state.known_cards)}/{total_original} mastered")

                    # Flashcard container
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 40px 30px;
                            border-radius: 15px;
                            text-align: center;
                            height: 200px;
                            max-width: 500px;
                            margin: 20px auto;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
                            overflow: hidden;
                        ">
                            <h1 style="color: white; font-size: 2.2em; margin: 0;">
                                {current_card['spanish'] if not st.session_state.show_answer else f'{current_card["english"]} <span style="color: #e0e0e0; font-size: 0.5em;">({current_card["pos"]})</span>'}
                            </h1>
                            {f'<p style="color: white; font-size: 0.95em; margin-top: 15px; font-style: italic;">"{current_card.get("example", "")}"</p>' if st.session_state.show_answer and current_card.get("example") else ''}
                        </div>
                        """, unsafe_allow_html=True)

                    # Controls
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                    with col1:
                        if st.button("◀ Previous", disabled=st.session_state.card_index == 0):
                            st.session_state.card_index -= 1
                            st.session_state.show_answer = False
                            st.rerun()

                    with col2:
                        if st.button("🔄 Flip Card"):
                            st.session_state.show_answer = not st.session_state.show_answer
                            st.rerun()

                    with col3:
                        if st.button("✓ Know It"):
                            st.session_state.known_cards.add(original_index)
                            # Stay on the same index position (the next card will shift into this position)
                            st.session_state.show_answer = False
                            st.rerun()

                    with col4:
                        if st.button("Next ▶", disabled=st.session_state.card_index == total_remaining - 1):
                            st.session_state.card_index += 1
                            st.session_state.show_answer = False
                            st.rerun()

                    # Practice sentence input
                    # Initialize session state for practice
                    if 'practice_sentence' not in st.session_state:
                        st.session_state.practice_sentence = ""
                    if 'practice_feedback' not in st.session_state:
                        st.session_state.practice_feedback = None

                    practice_input = st.text_area(
                        f"Try using **{current_card['spanish']}** in a sentence in Spanish:",
                        value=st.session_state.practice_sentence,
                        height=80,
                        placeholder=f"Example: {current_card.get('example', 'Write a sentence...')}"
                    )

                    if st.button("Get Feedback"):
                        if practice_input.strip():
                            st.session_state.practice_sentence = practice_input
                            # Get feedback from LLM
                            from rag import get_sentence_feedback
                            st.session_state.practice_feedback = get_sentence_feedback(
                                practice_input,
                                current_card['spanish'],
                                level,
                                test_mode
                            )
                            st.rerun()
                        else:
                            st.warning("Please write a sentence first!")

                    # Display feedback
                    if st.session_state.practice_feedback:
                        feedback = st.session_state.practice_feedback
                        st.markdown("#### 📝 Feedback")
                        st.info(feedback)

                    st.markdown("---")

                    # Comprehension Questions Section
                    if "questions" in st.session_state.results:
                        st.markdown("### 📖 Comprehension Questions")
                        try:
                            questions_data = json.loads(st.session_state.results["questions"])
                            if "questions" in questions_data:
                                all_questions = questions_data["questions"]

                                # Get one question of each difficulty
                                difficulties = ["beginner", "intermediate", "advanced"]
                                selected_questions = []
                                for diff in difficulties:
                                    for q in all_questions:
                                        if q.get("difficulty", "").lower() == diff:
                                            selected_questions.append(q)
                                            break

                                # Initialize session state for comprehension answers
                                if 'comp_answers' not in st.session_state:
                                    st.session_state.comp_answers = {}
                                if 'comp_feedback' not in st.session_state:
                                    st.session_state.comp_feedback = {}

                                # Display questions
                                for i, q in enumerate(selected_questions):
                                    difficulty = q.get("difficulty", "intermediate")
                                    question = q.get("question", "")

                                    st.markdown(f"**({difficulty.capitalize()}):** {question}")

                                    # Answer input
                                    answer_key = f"comp_answer_{i}"
                                    user_answer = st.text_area(
                                        "Your answer:",
                                        value=st.session_state.comp_answers.get(i, ""),
                                        height=60,
                                        key=answer_key,
                                        placeholder="Write your answer in Spanish..."
                                    )

                                    # Feedback button
                                    if st.button("Get Feedback", key=f"feedback_btn_{i}"):
                                        if user_answer.strip():
                                            st.session_state.comp_answers[i] = user_answer
                                            # Get feedback from LLM
                                            from rag import get_comprehension_feedback
                                            st.session_state.comp_feedback[i] = get_comprehension_feedback(
                                                question,
                                                user_answer,
                                                q.get("answer", ""),
                                                level,
                                                test_mode
                                            )
                                            st.rerun()
                                        else:
                                            st.warning(f"Please write an answer for Question {i+1} first!")

                                    # Display feedback if available
                                    if i in st.session_state.comp_feedback:
                                        st.info(st.session_state.comp_feedback[i])

                                    st.markdown("")  # Add spacing

                        except json.JSONDecodeError:
                            pass

                    st.markdown("---")

                    # Dialogue Section
                    if "dialogue" in st.session_state.results:
                        st.markdown("### 💬 Dialogue")
                        try:
                            dialogue_data = json.loads(st.session_state.results["dialogue"])

                            if "title" in dialogue_data:
                                st.markdown(f"**{dialogue_data['title']}**")

                            # Display dialogue lines
                            if "lines" in dialogue_data:
                                for line in dialogue_data["lines"]:
                                    speaker = line.get("speaker", "")
                                    text = line.get("es", "")
                                    st.markdown(f"**{speaker}:** {text}")

                        except json.JSONDecodeError:
                            pass

                    st.markdown("---")
        except json.JSONDecodeError:
            pass

