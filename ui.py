import streamlit as st
import requests

st.set_page_config(
    page_title="LexAI · Legal Advisor",
    page_icon="⚖️",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #212121 !important;
    color: #ececec !important;
    font-family: 'DM Sans', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stMainBlockContainer"] {
    max-width: 760px !important;
    padding: 0 1rem 7rem !important;
    margin: 0 auto !important;
}

/* ── Header ── */
.lex-header {
    text-align: center;
    padding: 2.5rem 0 1.8rem;
    margin-bottom: 0.5rem;
}
.lex-logo {
    font-family: 'Instrument Serif', serif;
    font-size: 2rem;
    font-weight: 400;
    color: #ececec;
    letter-spacing: -0.02em;
}
.lex-logo span { color: #10a37f; }
.lex-tagline {
    font-size: 0.78rem;
    color: #8e8ea0;
    margin-top: 0.3rem;
    font-weight: 300;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #8e8ea0;
}
.empty-icon { font-size: 2.4rem; margin-bottom: 0.8rem; }
.empty-text {
    font-size: 1rem;
    line-height: 1.6;
    color: #8e8ea0;
    font-weight: 300;
}

/* ── Suggestion pills ── */
.pill-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
    margin: 1.5rem 0 2rem;
}
.pill {
    background: #2f2f2f;
    border: 1px solid #3d3d3d;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #ececec;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    text-align: left;
    line-height: 1.4;
}
.pill:hover {
    background: #3a3a3a;
    border-color: #10a37f;
}

/* ── Message rows ── */
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    animation: fadeUp 0.25s ease;
}
.msg-row.user { flex-direction: row-reverse; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Avatars ── */
.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 500;
    flex-shrink: 0;
    margin-top: 2px;
}
.avatar.user {
    background: #10a37f;
    color: #fff;
}
.avatar.agent {
    background: #2f2f2f;
    border: 1px solid #3d3d3d;
    color: #10a37f;
    font-size: 1rem;
}

/* ── Bubbles ── */
.bubble {
    max-width: 85%;
    padding: 0.85rem 1.1rem;
    border-radius: 16px;
    font-size: 0.95rem;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
}
.bubble.user {
    background: #2f2f2f;
    color: #ececec;
    border: 1px solid #3d3d3d;
    border-top-right-radius: 4px;
}
.bubble.agent {
    background: transparent;
    color: #ececec;
    border: none;
    padding-left: 0;
}

/* ── Thinking dots ── */
.thinking {
    display: flex;
    gap: 5px;
    align-items: center;
    padding: 0.6rem 0;
}
.dot {
    width: 7px;
    height: 7px;
    background: #10a37f;
    border-radius: 50%;
    animation: pulse 1.4s infinite ease-in-out;
    opacity: 0.4;
}
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
    40% { transform: scale(1.1); opacity: 1; }
}

/* ── Divider between messages ── */
.msg-divider {
    height: 1px;
    background: #2f2f2f;
    margin: 0.5rem 0 1.5rem;
}

/* ── Input area ── */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 100% !important;
    max-width: 760px !important;
    padding: 0.8rem 1rem 1.2rem !important;
    background: #212121 !important;
    border-top: 1px solid #2f2f2f !important;
    z-index: 999 !important;
}
[data-testid="stChatInput"] > div {
    background: #2f2f2f !important;
    border: 1px solid #3d3d3d !important;
    border-radius: 12px !important;
    box-shadow: 0 0 0 1px transparent !important;
    transition: border-color 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #10a37f !important;
}
[data-testid="stChatInput"] textarea {
    color: #ececec !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    background: transparent !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8e8ea0 !important;
}
[data-testid="stChatInput"] button {
    background: #10a37f !important;
    border-radius: 8px !important;
    color: white !important;
}
[data-testid="stChatInput"] button:hover {
    background: #0d8f6e !important;
}

/* ── Clear button ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #3d3d3d !important;
    color: #8e8ea0 !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    padding: 0.3rem 0.8rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: #ff4444 !important;
    color: #ff4444 !important;
    background: transparent !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3d3d3d; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lex-header">
    <div class="lex-logo">⚖ Lex<span>AI</span></div>
    <div class="lex-tagline">AI-Powered Legal Advisor · Constitution · BNS · CrPC · IDA · MVA</div>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

SUGGESTIONS = [
    "📜 What is IPC Section 302?",
    "🏛 Explain Article 21 of the Constitution",
    "⚖ What is bail and how to apply?",
    "🔒 Rights of an arrested person in India",
]

# ── Suggestion pills ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🏛️</div>
        <div class="empty-text">Ask any legal question about Indian law,<br>IPC sections, constitutional rights, and more.</div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"pill_{i}", use_container_width=True):
            st.session_state.pending = s
            st.rerun()

# ── Render chat history ────────────────────────────────────────────────────────
def render_messages():
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        # Escape HTML in content
        import html
        safe_content = html.escape(content).replace("\n", "<br>")

        if role == "user":
            st.markdown(f"""
            <div class="msg-row user">
                <div class="bubble user">{safe_content}</div>
                <div class="avatar user">You</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row agent">
                <div class="avatar agent">⚖</div>
                <div class="bubble agent">{safe_content}</div>
            </div>
            <div class="msg-divider"></div>""", unsafe_allow_html=True)

render_messages()

# ── Handle API call ────────────────────────────────────────────────────────────
def ask(query: str):
    # Strip pill emoji prefix if from suggestion button
    clean_query = query.lstrip("📜🏛⚖🔒 ")

    st.session_state.messages.append({"role": "user", "content": clean_query})

    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("""
    <div class="msg-row agent">
        <div class="avatar agent">⚖</div>
        <div class="thinking">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>""", unsafe_allow_html=True)

    try:
        res = requests.post(
            "http://localhost:8001/chat",
            json={"message": clean_query},
            timeout=120
        )
        answer = res.json().get("response", "Sorry, I could not get a response.")
    except requests.exceptions.Timeout:
        answer = "⚠️ Request timed out. Please try again."
    except Exception as e:
        answer = f"⚠️ Error connecting to server: {str(e)}"

    thinking_placeholder.empty()
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Process pending ────────────────────────────────────────────────────────────
if st.session_state.pending:
    query = st.session_state.pending
    st.session_state.pending = None
    ask(query)

# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Message LexAI..."):
    ask(prompt)

# ── Clear button ───────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑 Clear conversation"):
        st.session_state.messages = []
        st.rerun()