from app.services.retriever import retrieve
from langchain_mistralai import ChatMistralAI


# Initialize LLM
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
)


#Agent
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

def build_prompt(query, context_chunks):
    context_text = ""

    for chunk in context_chunks:
        context_text += f"{chunk['id']} - {chunk['title']}\n{chunk['text']}\n\n"

    return f"""
You are a legal assistant AI.

Use the following legal context to answer the question clearly and accurately.

Context:
{context_text}

Question:
{query}

Instructions:
- Answer based only on the context
- Mention article/section numbers
- Keep answer simple and clear
"""


async def generate_answer(query):
    # 🔹 Step 1 — Retrieve
    context_chunks = retrieve(query)

    # 🔹 Step 2 — Build prompt
    prompt = build_prompt(query, context_chunks)

    # 🔹 Step 3 — Call LLM (LangChain way)
    response = llm.invoke(prompt)

    return response.content