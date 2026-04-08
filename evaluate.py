from app.services.retriever import retrieve
from langchain_mistralai import ChatMistralAI


# 🔹 Initialize LLM
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
)

test_cases = [
    # --- existing ---
    {
        "query": "What is punishment for murder?",
        "expected": "Section 103"
    },
    {
        "query": "What is cheating?",
        "expected": "Section 318"
    },
    {
        "query": "Right to life comes under which article?",
        "expected": "Article 21"
    },

    # --- hard: indirect / conceptual ---
    {
        "query": "Can a person be arrested without a warrant?",
        "expected": "Section 35"   # CrPC arrest without warrant
    },
    {
        "query": "What are the grounds for anticipatory bail?",
        "expected": "Section 482"  # CrPC anticipatory bail
    },
    {
        "query": "What happens if a person dies during a strike?",
        "expected": "Section 103"  # BNS murder / culpable homicide overlap
    },

    # --- hard: multi-hop reasoning ---
    {
        "query": "Is sedition still a valid offense in India?",
        "expected": "Section 152"  # BNS replaced IPC 124A
    },
    {
        "query": "What protection does the constitution give against double jeopardy?",
        "expected": "Article 20"
    },
    {
        "query": "Can a person be forced to be a witness against himself?",
        "expected": "Article 20"   # self-incrimination, same article different clause
    },

    # --- hard: vocabulary mismatch ---
    {
        "query": "What is the law on consensual physical relationships under false promise of marriage?",
        "expected": "Section 69"   # BNS sexual intercourse by deceit
    },
    {
        "query": "What is the penalty for a company that illegally terminates workers?",
        "expected": "Section 25"   # IDA retrenchment
    },
    {
        "query": "Who has the power to pardon a death sentence in India?",
        "expected": "Article 72"   # President's pardon power
    },

    # --- hard: negative / trick questions ---
    {
        "query": "Can a minor be given death penalty?",
        "expected": "Section 103"  # BNS — should clarify no death for minors
    },
    {
        "query": "What is the maximum speed limit on highways?",
        "expected": "Section 112"  # MVA — speed limits
    },
]
    
# 🔹 Simple RAG answer (no agent)
def generate_answer(query):
    context_chunks = retrieve(query)

    context_text = ""
    for chunk in context_chunks:
        context_text += f"{chunk['id']} - {chunk['title']}\n{chunk['text']}\n\n"

    prompt = f"""
You are a legal assistant AI.

Use the following legal context to answer clearly.

Context:
{context_text}

Question:
{query}

Instructions:
- Answer based only on context
- Mention article/section number
"""

    response = llm.invoke(prompt)
    return response.content


# 🔹 Evaluate retrieval accuracy
def evaluate_retrieval():
    correct = 0

    for case in test_cases:
        results = retrieve(case["query"])

        found = any(case["expected"] in r["id"] for r in results)

        print("\nQuery:", case["query"])
        print("Expected:", case["expected"])
        print("Retrieved IDs:", [r["id"] for r in results])
        print("Found:", found)

        if found:
            correct += 1

    accuracy = correct / len(test_cases)
    print(f"\n✅ Retrieval Accuracy: {accuracy:.2f}")


# 🔹 Evaluate answer quality
def evaluate_answers():
    for case in test_cases:
        answer = generate_answer(case["query"])

        print("\n==============================")
        print("Query:", case["query"])
        print("Expected:", case["expected"])
        print("Answer:", answer)


# 🔹 Run everything
if __name__ == "__main__":
    print("\n🚀 Running Retrieval Evaluation...\n")
    evaluate_retrieval()

    print("\n🚀 Running Answer Evaluation...\n")
    evaluate_answers()