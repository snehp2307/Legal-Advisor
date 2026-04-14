import html
import markdown as mdlib
import streamlit as st
import requests

st.set_page_config(
    page_title="LexAI · Legal Advisor",
    page_icon="⚖️",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Syne:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-base:        #0e0f13;
    --bg-surface:     #161820;
    --bg-elevated:    #1e2028;
    --bg-input:       #1a1c24;
    --border-subtle:  #2a2d3a;
    --border-active:  #c9a84c;
    --accent-gold:    #c9a84c;
    --accent-gold-dim:#a8893e;
    --accent-teal:    #2dd4bf;
    --text-primary:   #f0ede6;
    --text-secondary: #9a9db0;
    --text-muted:     #5a5d70;
    --user-bubble:    #1a1c24;
    --agent-bubble:   transparent;
    --danger:         #e55757;
    --font-display:   'Cormorant Garamond', Georgia, serif;
    --font-body:      'Syne', sans-serif;
    --font-mono:      'JetBrains Mono', monospace;
}

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stMainBlockContainer"] {
    max-width: 780px !important;
    padding: 0 1.25rem 7rem !important;
    margin: 0 auto !important;
}

/* ── Decorative top border ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    display: block;
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent-gold), var(--accent-teal), var(--accent-gold), transparent);
    z-index: 9999;
}

/* ── Header ── */
.lex-header {
    text-align: center;
    padding: 3rem 0 2rem;
    margin-bottom: 0.25rem;
    position: relative;
}
.lex-header::after {
    content: '';
    display: block;
    width: 60px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-gold), transparent);
    margin: 1.25rem auto 0;
}
.lex-logo {
    font-family: var(--font-display);
    font-size: 2.8rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: 0.04em;
    line-height: 1;
}
.lex-logo span {
    color: var(--accent-gold);
    font-style: italic;
}
.lex-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.7rem;
    font-size: 0.7rem;
    color: var(--text-muted);
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-family: var(--font-body);
}
.lex-badge::before,
.lex-badge::after {
    content: '·';
    color: var(--accent-gold);
    font-size: 0.85rem;
}
.lex-scope {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.8rem;
}
.scope-chip {
    background: transparent;
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 0.2rem 0.55rem;
    font-size: 0.65rem;
    color: var(--text-muted);
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
}
.empty-gavel {
    font-size: 2.8rem;
    filter: drop-shadow(0 0 16px rgba(201,168,76,0.25));
    margin-bottom: 1rem;
}
.empty-headline {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.4rem;
}
.empty-sub {
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.7;
    font-weight: 400;
}

/* ── Suggestion pills ── */
.pill-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem;
    margin: 1.8rem 0 2.5rem;
}

/* Override Streamlit button inside pill grid */
div[data-testid="column"] .stButton > button {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    padding: 0.85rem 1rem !important;
    font-size: 0.82rem !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-weight: 400 !important;
    text-align: left !important;
    line-height: 1.45 !important;
    transition: border-color 0.18s, background 0.18s, color 0.18s !important;
    width: 100% !important;
    cursor: pointer !important;
    letter-spacing: 0.01em !important;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: var(--accent-gold) !important;
    background: rgba(201,168,76,0.06) !important;
    color: var(--accent-gold) !important;
}

/* ── Message rows ── */
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    margin-bottom: 1.2rem;
    animation: fadeUp 0.22s ease;
}
.msg-row.user { flex-direction: row-reverse; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Avatars ── */
.avatar {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-top: 3px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    font-family: var(--font-body);
}
.avatar.user {
    background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold-dim));
    color: var(--bg-base);
    font-size: 0.65rem;
    text-transform: uppercase;
}
.avatar.agent {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    font-size: 1.05rem;
}

/* ── Bubbles ── */
.bubble {
    max-width: 82%;
    font-size: 0.92rem;
    line-height: 1.7;
    word-break: break-word;
}
.bubble.user {
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
    border-radius: 14px 4px 14px 14px;
    padding: 0.85rem 1.15rem;
    white-space: pre-wrap;
}
.bubble.agent {
    background: transparent;
    color: var(--text-primary);
    border: none;
    padding: 0.1rem 0;
}

/* ── Markdown inside agent bubble ── */
.bubble.agent h1,
.bubble.agent h2,
.bubble.agent h3 {
    font-family: var(--font-display);
    color: var(--text-primary);
    font-weight: 500;
    margin: 1.1rem 0 0.45rem;
    line-height: 1.25;
}
.bubble.agent h1 { font-size: 1.5rem; }
.bubble.agent h2 { font-size: 1.25rem; color: var(--accent-gold); }
.bubble.agent h3 { font-size: 1.05rem; color: var(--accent-teal); }
.bubble.agent p  { margin-bottom: 0.7rem; }
.bubble.agent p:last-child { margin-bottom: 0; }
.bubble.agent strong { color: var(--text-primary); font-weight: 600; }
.bubble.agent em { color: var(--text-secondary); font-style: italic; }
.bubble.agent hr {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 0.8rem 0;
}
.bubble.agent ul,
.bubble.agent ol {
    padding-left: 1.5rem;
    margin-bottom: 0.7rem;
}
.bubble.agent li { margin-bottom: 0.35rem; }
.bubble.agent li::marker { color: var(--accent-gold); }
.bubble.agent code {
    background: var(--bg-elevated);
    border: 1px solid var(--border-subtle);
    border-radius: 4px;
    padding: 0.12rem 0.4rem;
    font-size: 0.85em;
    color: var(--accent-teal);
    font-family: var(--font-mono);
}
.bubble.agent pre {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-left: 3px solid var(--accent-gold);
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    overflow-x: auto;
    margin-bottom: 0.7rem;
}
.bubble.agent pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: var(--text-primary);
    font-size: 0.88rem;
}
.bubble.agent blockquote {
    border-left: 3px solid var(--accent-gold);
    padding-left: 1rem;
    color: var(--text-secondary);
    margin: 0.6rem 0;
    font-style: italic;
    font-family: var(--font-display);
    font-size: 1rem;
}
.bubble.agent table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 0.7rem;
    font-size: 0.88rem;
}
.bubble.agent th {
    background: var(--bg-elevated);
    color: var(--accent-gold);
    padding: 0.5rem 0.9rem;
    border: 1px solid var(--border-subtle);
    text-align: left;
    font-weight: 600;
    font-family: var(--font-body);
    letter-spacing: 0.05em;
    font-size: 0.78rem;
    text-transform: uppercase;
}
.bubble.agent td {
    padding: 0.45rem 0.9rem;
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
}
.bubble.agent tr:nth-child(even) td { background: rgba(255,255,255,0.02); }

/* ── Section label above agent reply ── */
.agent-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    font-family: var(--font-body);
}

/* ── Thinking dots ── */
.thinking {
    display: flex;
    gap: 5px;
    align-items: center;
    padding: 0.55rem 0;
}
.dot {
    width: 6px;
    height: 6px;
    background: var(--accent-gold);
    border-radius: 50%;
    animation: pulse 1.5s infinite ease-in-out;
    opacity: 0.35;
}
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.35; }
    40%            { transform: scale(1.2); opacity: 1; }
}

/* ── Divider ── */
.msg-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 0.25rem 0 1.2rem;
    opacity: 0.5;
}

/* ── Disclaimer strip ── */
.disclaimer {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    background: rgba(201,168,76,0.06);
    border: 1px solid rgba(201,168,76,0.18);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.5;
}
.disclaimer-icon {
    font-size: 0.9rem;
    flex-shrink: 0;
    margin-top: 1px;
}

/* ══════════════════════════════════════
   ── INPUT AREA — HIGH CONTRAST FIX ──
   ══════════════════════════════════════ */

/* Fixed bottom bar */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 100% !important;
    max-width: 780px !important;
    padding: 0.9rem 1.25rem 1.4rem !important;
    background: var(--bg-base) !important;
    border-top: 1px solid var(--border-subtle) !important;
    z-index: 999 !important;
}

/* Outer wrapper — the rounded box */
[data-testid="stChatInput"] > div {
    background: #1e2028 !important;
    border: 1.5px solid #3a3d52 !important;
    border-radius: 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent-gold) !important;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.12) !important;
}

/* The actual textarea — MUST be bright white on dark bg */
[data-testid="stChatInput"] textarea {
    background-color: #1e2028 !important;
    color: #ffffff !important;                    /* ← full white text */
    caret-color: var(--accent-gold) !important;   /* ← gold cursor */
    font-family: var(--font-body) !important;
    font-size: 0.92rem !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
    padding: 0.75rem 1rem !important;
    border: none !important;
    outline: none !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #6b6e85 !important;                    /* ← visible but dim placeholder */
    font-style: italic !important;
    font-size: 0.87rem !important;
}
/* Remove any inner box-shadow / outline Streamlit injects */
[data-testid="stChatInput"] textarea:focus {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}

/* Send button */
[data-testid="stChatInput"] button[kind="primaryFormSubmit"],
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, var(--accent-gold), var(--accent-gold-dim)) !important;
    border: none !important;
    border-radius: 9px !important;
    color: var(--bg-base) !important;
    font-weight: 600 !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
[data-testid="stChatInput"] button:hover {
    opacity: 0.88 !important;
    transform: scale(1.04) !important;
}

/* Input hint below bar */
.input-hint {
    text-align: center;
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-top: 0.35rem;
    letter-spacing: 0.04em;
}

/* ── Clear button ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-family: var(--font-body) !important;
    padding: 0.35rem 0.9rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: rgba(229,87,87,0.06) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-subtle); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-gold-dim); }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lex-header">
    <div class="lex-logo">⚖ Lex<span>AI</span></div>
    <div class="lex-badge">AI-Powered Legal Advisor</div>
    <div class="lex-scope">
        <span class="scope-chip">Constitution</span>
        <span class="scope-chip">BNS / IPC</span>
        <span class="scope-chip">CrPC / BNSS</span>
        <span class="scope-chip">IDA</span>
        <span class="scope-chip">MVA</span>
        <span class="scope-chip">Civil Law</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

SUGGESTIONS = [
    "📜 What is IPC Section 302 (Murder)?",
    "🏛 Explain Article 21 — Right to Life",
    "⚖ How to apply for bail in India?",
    "🔒 Rights of an arrested person",
]

# ── Suggestion pills (empty state) ────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-gavel">⚖️</div>
        <div class="empty-headline">How can I assist you today?</div>
        <div class="empty-sub">Ask any question about Indian law — constitutional rights,<br>criminal provisions, civil remedies, and more.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer">
        <span class="disclaimer-icon">ℹ️</span>
        <span>LexAI provides general legal information only. This is not legal advice.
        For specific legal issues, please consult a qualified advocate.</span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, key=f"pill_{i}", use_container_width=True):
            st.session_state.pending = s
            st.rerun()

# ── Render chat history ────────────────────────────────────────────────────────
def render_messages():
    for msg in st.session_state.messages:
        role    = msg["role"]
        content = msg["content"]

        if role == "user":
            safe_content = html.escape(content).replace("\n", "<br>")
            st.markdown(f"""
            <div class="msg-row user">
                <div class="bubble user">{safe_content}</div>
                <div class="avatar user">You</div>
            </div>""", unsafe_allow_html=True)
        else:
            rendered = mdlib.markdown(
                content,
                extensions=["nl2br", "tables", "fenced_code"]
            )
            st.markdown(f"""
            <div class="msg-row agent">
                <div class="avatar agent">⚖</div>
                <div style="flex:1; min-width:0;">
                    <div class="agent-label">LexAI · Legal Analysis</div>
                    <div class="bubble agent">{rendered}</div>
                </div>
            </div>
            <div class="msg-divider"></div>""", unsafe_allow_html=True)

render_messages()

# ── Handle API call ────────────────────────────────────────────────────────────
def ask(query: str):
    clean_query = query.lstrip("📜🏛⚖🔒 ")

    st.session_state.messages.append({"role": "user", "content": clean_query})

    thinking_placeholder = st.empty()
    thinking_placeholder.markdown("""
    <div class="msg-row agent">
        <div class="avatar agent">⚖</div>
        <div style="flex:1;">
            <div class="agent-label">LexAI · Analysing</div>
            <div class="thinking">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    try:
        res = requests.post(
            "http://backend:8001/chat",
            json={"message": clean_query},
            timeout=120,
        )
        answer = res.json().get("response", "Sorry, I could not get a response.")

    except requests.exceptions.ConnectionError:
        answer = "⚠️ **Cannot connect to backend.** Is the server running on port 8001?"

    except ValueError:
        answer = "⚠️ **Invalid response from server.** Please try again."

    except Exception as e:
        answer = f"⚠️ **Unexpected error:** {str(e)}"

    thinking_placeholder.empty()

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# ── Process pending suggestion ─────────────────────────────────────────────────
if st.session_state.pending:
    query = st.session_state.pending
    st.session_state.pending = None
    ask(query)

# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask a legal question…"):
    ask(prompt)

# ── Clear button ───────────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        if st.button("🗑 Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()