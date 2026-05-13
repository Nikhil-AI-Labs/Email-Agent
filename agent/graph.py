from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from .tools import send_email, send_bulk_emails

# Setup persistent memory
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    import sqlite3
    # Check_same_thread=False is needed for Streamlit since it runs across multiple threads
    conn = sqlite3.connect("chat_memory.db", check_same_thread=False)
    memory = SqliteSaver(conn)
except ImportError:
    # Fallback if sqlite saver is not installed
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()

def get_agent(llm_cfg, system_prompt):
    """Initializes and returns the conversational ReAct agent."""
    llm = ChatOpenAI(
        model=llm_cfg["model"],
        base_url=llm_cfg["base_url"],
        api_key=llm_cfg["api_key"],
        temperature=llm_cfg["temperature"]
    )
    
    # Handle version differences in LangGraph API
    try:
        # LangGraph >= 1.0.x
        return create_react_agent(
            llm, 
            tools=[send_email, send_bulk_emails], 
            checkpointer=memory,
            prompt=system_prompt
        )
    except TypeError:
        try:
            # LangGraph 0.2.x (newer)
            return create_react_agent(
                llm, 
                tools=[send_email, send_bulk_emails], 
                checkpointer=memory,
                state_modifier=system_prompt
            )
        except TypeError:
            # LangGraph 0.1.x (older)
            return create_react_agent(
                llm, 
                tools=[send_email, send_bulk_emails], 
                checkpointer=memory,
                messages_modifier=system_prompt
            )
