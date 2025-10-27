# FILE: chatbot_schemas.py (MODIFIED)

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatQuery(BaseModel):
    """Schema for the input query from a user to any chatbot."""
    query: str
    session_id: Optional[str] = None

class ApiKeyChatQuery(BaseModel):
    """Schema for a query that includes user-provided API keys."""
    query: str
    session_id: Optional[str] = None
    # Google API Key remains MANDATORY for the LLM itself
    google_api_key: str = Field(..., description="User's Google API Key")
    # Cohere and Tavily keys are now OPTIONAL (defaulting to empty string)
    cohere_api_key: str = Field("", description="User's Cohere API Key (mandatory for RAG, checked in service)")
    tavily_api_key: str = Field("", description="User's Tavily API Key (optional for Web Search)")

class SourceDocument(BaseModel):
    """Schema for a single source document used in the response."""
    source: str = Field(description="The name of the source document, e.g., 'constitution_of_india.pdf'.")
    page_content: str = Field(description="The relevant text chunk from the document.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata, e.g., page number.")

class AdaptiveResponse(BaseModel):
    """Schema for flexible chatbot responses that adapt to user needs."""
    response: str = Field(description="The AI's natural response to the user query")
    session_id: str = Field(description="Session identifier for conversation tracking")
    response_type: str = Field(description="Type of response: adaptive, legal, general, or error")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")

class LegalResponse(BaseModel):
    """Legacy structured response - kept for compatibility."""
    explanation: str = Field(description="A clear and detailed explanation of the legal concept.")
    relevant_sections: List[str] = Field(description="A list of relevant legal acts or sections, e.g., 'Section 302 of IPC'.")
    summary: str = Field(description="A simple, one or two-sentence summary for quick understanding.")
    disclaimer: str = Field(description="The mandatory legal disclaimer.")
    sources: List[SourceDocument] = Field(default_factory=list, description="A list of source documents used to generate the answer.")

# --- Schemas for Chat History Management ---

class ChatHistoryResponse(BaseModel):
    """Response schema for chat history operations."""
    session_id: str
    messages: List[Dict[str, Any]]
    count: int

class DeleteResponse(BaseModel):
    """Response schema for deletion operations."""
    message: str
    success: bool
    session_id: Optional[str] = None

class SessionInfo(BaseModel):
    """Schema for basic information about a single chat session."""
    id: str
    title: str

class SessionsResponse(BaseModel):
    """Response schema for listing all sessions."""
    sessions: List[SessionInfo]
    count: int