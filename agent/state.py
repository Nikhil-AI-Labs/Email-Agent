from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # Global Config
    global_instructions: str
    attachments: List[Dict[str, Any]]
    smtp_email: str
    smtp_password: str
    llm_config: Dict[str, Any]
    
    # Target Data
    target: Dict[str, Any]
    
    # Output Data
    draft_email: str
    review_feedback: str
    final_email: str
    
    # Conversational HITL
    chat_history: List[BaseMessage]
    user_feedback: str  # Populated when user sends chat from UI
    
    # Control Flags
    hitl_approved: bool
    status: str  # "drafting", "reviewing", "hitl", "sending", "sent", "failed"
    error_log: List[str]
