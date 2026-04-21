import asyncio
from cachetools import TTLCache
from app.services.retriever import retrieve
from langchain_mistralai import ChatMistralAI


# 🔹 LLM
llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0.3,
    max_tokens=200,
    
)

# 🔥 LIMIT CONCURRENCY (VERY IMPORTANT)
semaphore = asyncio.Semaphore(5)

# 🔥 CACHE (better than dict)
cache = TTLCache(maxsize=100, ttl=300)


# 🔹 Prompt builder
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
- Keep answer short (max 4-5 lines)
- Avoid unnecessary explanation
"""


# 🔥 FINAL FUNCTION
async def generate_answer(query):
    key = query.lower().strip()

    # ✅ CACHE CHECK
    if key in cache:
        print("[CACHE HIT]")
        return cache[key]

    async with semaphore:  # 🔥 RATE CONTROL
        retries = 3

        for attempt in range(retries):
            try:
                # 🔹 Retrieve (non-blocking)
                context_chunks = await asyncio.to_thread(retrieve, key)
                context_chunks = context_chunks[:3]

                if not context_chunks:
                    return "No relevant legal information found."

                # 🔹 Build prompt
                prompt = build_prompt(key, context_chunks)

                # 🔹 Async LLM call
                response = await llm.ainvoke(prompt)
                answer = response.content

                # ✅ SAVE TO CACHE
                cache[key] = answer

                return answer

            except Exception as e:
                # 🔥 HANDLE RATE LIMIT
                if "429" in str(e):
                    wait = 2
                    print(f"[RETRY] Rate limited. Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    import traceback
                    print("ERROR:", traceback.format_exc())
                    return f"Error: {str(e)}"

        return "⚠️ Rate limit exceeded. Please try again later."