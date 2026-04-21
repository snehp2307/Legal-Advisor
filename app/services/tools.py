from app.services.retriever import retrieve
import asyncio

def search_legal_docs(query:str):
    results = retrieve(query)
    
    if not results:
        return "No relevant legal information found."

    formatted = ""

    for r in results:
        formatted += f"{r['id']} - {r['title']}\n{r['text']}\n\n"

    return formatted

def simplify_legal_text(text: str):
    return f"Explain this legal text in simple words:\n{text}"

async def search_legal_docs_async(query: str):
    return await asyncio.to_thread(search_legal_docs, query)


async def simplify_legal_text_async(text: str):
    return await asyncio.to_thread(simplify_legal_text, text)