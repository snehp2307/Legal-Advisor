from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langchain_mistralai import ChatMistralAI
from app.services.tools import search_legal_docs_async, simplify_legal_text_async

tools = [
    Tool(
        name="Legal_Search",
        coroutine=search_legal_docs_async,
        description="Search legal documents",
        func=lambda x: x,
    ),
    Tool(
        name="Simplify_Legal_Text",
        coroutine=simplify_legal_text_async,
        description="Simplify legal language",
        func=lambda x: x,
    )
]

llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0.3,
    max_tokens=512,
)

system_prompt = """You are a legal assistant AI. Help users understand legal concepts, 
search legal documents like IPC and Constitution, and simplify complex legal language. 
Always cite relevant sections when possible. Keep answers concise."""

# ✅ No prompt/state_modifier kwarg
agent = create_react_agent(
    model=llm,
    tools=tools,
)

async def ask_agent(query: str):
    try:
        result = await agent.ainvoke(
            {
                "messages": [
                    ("system", system_prompt),  # ✅ injected here instead
                    ("user", query)
                ]
            },
            config={"recursion_limit": 6},
        )
        return result["messages"][-1].content
    except Exception as e:
        import traceback
        print("AGENT ERROR:", traceback.format_exc())
        return f"Error: {str(e)}"