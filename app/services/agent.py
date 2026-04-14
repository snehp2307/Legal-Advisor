from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langchain_mistralai import ChatMistralAI
from app.services.tools import search_legal_docs, simplify_legal_text

# 🔹 Define tools
tools = [
    Tool(
        name="Legal_Search",          
        func=search_legal_docs,
        description="Search legal documents like IPC, Constitution, etc."
    ),
    Tool(
        name="Simplify_Legal_Text",  
        func=simplify_legal_text,
        description="Simplify complex legal language into easy explanation"
    )
]
# 🔹 LLM
llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
)

# 🔹 System prompt (replaces PromptTemplate in LangGraph)
system_prompt = """You are a legal assistant AI. Help users understand legal concepts, 
search legal documents like IPC and Constitution, and simplify complex legal language 
into easy explanations. Always be accurate and cite relevant sections when possible."""

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt
)

async def ask_agent(query: str):
    result = agent.invoke({
        "messages": [("user", query)]
    })
    return result["messages"][-1].content