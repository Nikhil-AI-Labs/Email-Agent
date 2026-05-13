import streamlit as st
import os
from langchain_core.messages import HumanMessage, AIMessage
from utils.parsers import parse_file
from config import PROVIDERS, get_llm_config
from agent.graph import get_agent

st.set_page_config(page_title="Email Agent Chat", page_icon="💬", layout="wide")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "user_session_1"

# --- Sidebar: Configuration & Uploads ---
st.sidebar.title("Configuration ⚙️")

provider_choice = st.sidebar.selectbox("LLM Provider", list(PROVIDERS.keys()))
api_key = st.sidebar.text_input(f"{PROVIDERS[provider_choice]['env_var']} (API Key)", type="password")

st.sidebar.markdown("---")
st.sidebar.subheader("SMTP Credentials")
smtp_email = st.sidebar.text_input("Sender Email")
smtp_password = st.sidebar.text_input("App Password", type="password")

hitl_enabled = st.sidebar.checkbox("Enable Human-In-The-Loop (HITL)", value=True, help="If checked, the agent will ask for your approval before sending emails.")

st.sidebar.markdown("---")
st.sidebar.subheader("1. Target Data & Context")
st.sidebar.caption("Upload lists of contacts, context info, papers, etc. (Read by agent, NOT attached).")
target_files = st.sidebar.file_uploader("Upload Target Data", accept_multiple_files=True, key="target_files")

st.sidebar.subheader("2. Email Attachments")
st.sidebar.caption("Files uploaded here WILL be physically attached to outgoing emails.")
attachment_files = st.sidebar.file_uploader("Upload Attachments", accept_multiple_files=True, key="attachment_files")

attachments = []
file_context = ""

if target_files:
    for f in target_files:
        ext = f.name.split('.')[-1].lower()
        if ext in ['csv', 'xlsx', 'xls', 'txt', 'pdf']:
            parsed = parse_file(f, ext)
            # Truncate if too long to prevent context overflow
            parsed_str = str(parsed)
            if len(parsed_str) > 20000:
                parsed_str = parsed_str[:20000] + "\n... [TRUNCATED DUE TO LENGTH]"
            file_context += f"\n--- Target Data Context: {f.name} ---\n{parsed_str}\n"

if attachment_files:
    for f in attachment_files:
        bytes_data = f.getvalue()
        attachments.append({
            "filename": f.name,
            "bytes": bytes_data,
            "mime_type": f.type
        })
        file_context += f"\n--- Attachment Uploaded: {f.name} (This is already loaded into your tools and will be sent automatically with emails) ---\n"

# --- Main App ---
st.title("Email Automation Chatbot 🤖📧")
st.caption("Chat with me! I can answer questions, read your uploaded files, draft any type of email, and send them for you.")

if not api_key:
    st.warning("👈 Please provide your LLM API Key in the sidebar to start chatting.")
    st.stop()

# Build the system prompt dynamically based on UI state
system_prompt = f"""You are a highly capable, generalized Email Automation Assistant and Chatbot.
You are excellent at natural conversation, answering general questions, and performing automated tasks.
Your primary capability is drafting and sending ANY type of email (e.g., outreach, follow-ups, newsletters, personal messages).

Current State:
- HITL (Human-in-the-loop): {hitl_enabled}
- If HITL is True: You MUST show the drafted email(s) to the user in chat and explicitly ask "Should I send this?" before executing any tool.
- If HITL is False: You can draft and immediately use the tools to send the email without waiting for approval.

Context & Data:
The user has provided the following data files (Target Data) and Email Attachments:
{file_context if file_context else 'No files uploaded yet.'}

Important Instructions:
1. "Target Data Context" files contain information for you to read (like lists of emails, background context, or instructions). DO NOT attempt to attach these.
2. "Attachment Uploaded" files are physically loaded into your tools already. Any email you send using `send_email` or `send_bulk_emails` will automatically include these specific files as attachments.
3. OPTIMIZATION FOR MULTIPLE EMAILS: If the user asks you to send emails to multiple people, you MUST construct the arrays and use the `send_bulk_emails` tool. Do NOT call `send_email` multiple times in a loop, as it is extremely slow. `send_bulk_emails` handles everything in one fast connection.
"""

llm_cfg = get_llm_config(provider_choice, api_key)
agent_executor = get_agent(llm_cfg, system_prompt)

config = {"configurable": {
    "thread_id": st.session_state.thread_id,
    "smtp_email": smtp_email,
    "smtp_password": smtp_password,
    "attachments": attachments
}}

# Fetch state to render history
state = agent_executor.get_state(config)
messages = state.values.get("messages", []) if state.values else []

# Render chat history
for msg in messages:
    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    elif isinstance(msg, AIMessage):
        if msg.content:
            st.chat_message("assistant").write(msg.content)
        if msg.tool_calls:
            for tc in msg.tool_calls:
                st.chat_message("assistant").info(f"🛠️ Using tool: `{tc['name']}`")
    elif msg.type == "tool":
        st.chat_message("assistant").success(f"✅ Tool result: {msg.content}")

# Chat input processing
if user_input := st.chat_input("Type your message here... (e.g. 'Send an outreach email to the professors in the CSV')"):
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent_executor.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
            
            # Print only the new messages generated in this turn
            new_messages = result["messages"][len(messages):]
            for msg in new_messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        st.write(msg.content)
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            st.info(f"🛠️ Using tool: `{tc['name']}`")
                elif msg.type == "tool":
                    st.success(f"✅ Tool result: {msg.content}")
