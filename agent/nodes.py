import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import AgentState

def _get_llm(state: AgentState):
    """Initializes the LLM based on state config."""
    cfg = state.get("llm_config", {})
    return ChatOpenAI(
        model=cfg.get("model", "sarvam-105b"),
        base_url=cfg.get("base_url", "https://api.sarvam.ai/v1"),
        api_key=cfg.get("api_key", ""),
        temperature=cfg.get("temperature", 0.3)
    )

def generate_node(state: AgentState) -> Dict[str, Any]:
    """Generates the initial email draft."""
    try:
        llm = _get_llm(state)
        
        target = state.get("target", {})
        target_info = "\n".join([f"{k}: {v}" for k, v in target.items() if v])
        
        system_msg = "You are a professional academic assistant helping a student write research internship request emails to professors. Keep the email concise, polite, and directly address the professor's research area if provided. Do NOT include placeholders; make it a complete email ready to send."
        
        user_msg = f"""
Global Instructions from User:
{state.get('global_instructions', 'Draft an email requesting a research internship.')}

Professor/Target Details:
{target_info}

Please draft the email.
"""
        response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=user_msg)])
        
        # Initialize chat history with the draft
        chat_history = state.get("chat_history", []) + [AIMessage(content=response.content)]
        
        return {
            "draft_email": response.content,
            "status": "reviewing",
            "chat_history": chat_history
        }
    except Exception as e:
        return {"status": "failed", "error_log": state.get("error_log", []) + [f"Generate error: {str(e)}"]}

def self_review_node(state: AgentState) -> Dict[str, Any]:
    """LLM self-reviews and refines the drafted email."""
    try:
        llm = _get_llm(state)
        draft = state.get("draft_email", "")
        
        system_msg = "You are an expert editor. Review the following email draft. Fix any grammatical errors, ensure it sounds highly professional and academic, and make sure it is concise. Return ONLY the refined email text."
        
        response = llm.invoke([SystemMessage(content=system_msg), HumanMessage(content=draft)])
        
        return {
            "draft_email": response.content,
            "status": "hitl"
        }
    except Exception as e:
        return {"status": "failed", "error_log": state.get("error_log", []) + [f"Review error: {str(e)}"]}

def refine_node(state: AgentState) -> Dict[str, Any]:
    """Refines the draft based on human chat feedback."""
    try:
        llm = _get_llm(state)
        history = state.get("chat_history", [])
        feedback = state.get("user_feedback", "")
        
        if not feedback:
            return {} # No feedback provided
            
        history.append(HumanMessage(content=feedback))
        
        system_msg = SystemMessage(content="You are an AI assistant refining an email draft based on user feedback. The conversation history contains the previous draft. Output ONLY the complete refined email text.")
        
        messages = [system_msg] + history
        response = llm.invoke(messages)
        
        history.append(AIMessage(content=response.content))
        
        return {
            "draft_email": response.content,
            "chat_history": history,
            "user_feedback": "", # Clear feedback after processing
            "status": "hitl"
        }
    except Exception as e:
        return {"status": "failed", "error_log": state.get("error_log", []) + [f"Refine error: {str(e)}"]}

def send_node(state: AgentState) -> Dict[str, Any]:
    """Sends the email using SMTP."""
    try:
        email = state.get("smtp_email")
        password = state.get("smtp_password")
        target = state.get("target", {})
        recipient = target.get("email")
        body = state.get("draft_email", "")
        
        if not email or not password:
            raise ValueError("SMTP credentials missing.")
        if not recipient:
            raise ValueError("Recipient email address missing.")
            
        # Extract a subject line if possible, otherwise generic
        subject = "Application for Research Internship"
        lines = body.split('\n')
        for line in lines:
            if line.lower().startswith("subject:"):
                subject = line.replace("Subject:", "").replace("subject:", "").strip()
                # Remove subject line from body to avoid redundancy
                body = body.replace(line, "").strip()
                break
                
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach files
        attachments = state.get("attachments", [])
        for att in attachments:
            mime_type = att.get("mime_type", "application/octet-stream")
            maintype, _, subtype = mime_type.partition('/')
            if not subtype:
                subtype = "octet-stream"
                
            part = MIMEBase(maintype, subtype)
            part.set_payload(att.get("bytes", b""))
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{att.get("filename", "attachment")}"')
            msg.attach(part)
        
        # Connect to Gmail SMTP (Assuming Gmail, can be generalized later)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.send_message(msg)
        server.quit()
        
        return {
            "final_email": body,
            "status": "sent"
        }
    except Exception as e:
        return {"status": "failed", "error_log": state.get("error_log", []) + [f"SMTP error: {str(e)}"]}
