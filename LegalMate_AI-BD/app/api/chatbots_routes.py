# FILE: app/api/chatbots_routes.py

from fastapi import APIRouter, HTTPException, Depends, Request
import uuid
import logging
from app.schemas.chatbot_schemas import (
    # --- IMPORT THE NEW SCHEMA ---
    ApiKeyChatQuery, 
    AdaptiveResponse, 
    LegalResponse,
    ChatHistoryResponse, 
    SessionsResponse, 
    DeleteResponse
)
from app.services.legalchatbot import AdaptiveLegalChatbot, LegalChatbot

router = APIRouter(prefix="/chat")

# --- MODIFIED DEPENDENCIES ---
# Updated to get the ..._service from app.state, as defined in main.py

def get_adaptive_chatbot(request: Request) -> AdaptiveLegalChatbot:
    """Dependency to get the shared adaptive chatbot service instance."""
    service = request.app.state.adaptive_chatbot_service
    if not service:
        raise HTTPException(status_code=503, detail="Chatbot service is not available.")
    return service

def get_legacy_chatbot(request: Request) -> LegalChatbot:
    """Dependency to get the shared legacy chatbot service instance."""
    service = request.app.state.legacy_chatbot_service
    if not service:
        raise HTTPException(status_code=503, detail="Legacy chatbot service is not available.")
    return service

# --- MODIFIED CHAT ENDPOINTS ---

@router.post("/legal_assistant", response_model=AdaptiveResponse)
async def ask_adaptive_chatbot(
    # Use the new schema to accept API keys
    request_data: ApiKeyChatQuery, 
    chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)
):
    """Modern endpoint that returns adaptive, ChatGPT-style responses."""
    session_id = request_data.session_id or str(uuid.uuid4())
    try:
        # Pass all keys to the service method
        response = await chatbot.ask_structured(
            query=request_data.query,
            session_id=session_id,
            google_api_key=request_data.google_api_key,
            cohere_api_key=request_data.cohere_api_key,
            tavily_api_key=request_data.tavily_api_key
        )
        if response.response_type == "error":
             raise HTTPException(status_code=400, detail=response.response)
        return response
    except Exception as e:
        logging.error(f"Error in ask_adaptive_chatbot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/legal_assistant/simple")
async def ask_simple_chatbot(
    # Use the new schema to accept API keys
    request_data: ApiKeyChatQuery,
    chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)
):
    """Simplified endpoint that returns just the response text."""
    session_id = request_data.session_id or str(uuid.uuid4())
    try:
        # Pass all keys to the service method
        response_text = await chatbot.ask(
            query=request_data.query,
            session_id=session_id,
            google_api_key=request_data.google_api_key,
            cohere_api_key=request_data.cohere_api_key,
            tavily_api_key=request_data.tavily_api_key
        )
        if "I apologize, but I encountered an issue" in response_text:
             raise HTTPException(status_code=400, detail=response_text)
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        logging.error(f"Error in ask_simple_chatbot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/legal_assistant/legacy", response_model=LegalResponse)
async def ask_legacy_chatbot(
    # Use the new schema to accept API keys
    request_data: ApiKeyChatQuery,
    chatbot: LegalChatbot = Depends(get_legacy_chatbot)
):
    """Legacy endpoint for backward compatibility with structured responses."""
    session_id = request_data.session_id or str(uuid.uuid4())
    try:
        # Pass all keys to the service method
        structured_response = await chatbot.ask(
            query=request_data.query,
            session_id=session_id,
            google_api_key=request_data.google_api_key,
            cohere_api_key=request_data.cohere_api_key,
            tavily_api_key=request_data.tavily_api_key
        )
        if "Error" in structured_response.summary:
             raise HTTPException(status_code=400, detail=structured_response.explanation)
        return structured_response
    except Exception as e:
        logging.error(f"Error in ask_legacy_chatbot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Session & History Management Endpoints (no changes needed) ---
# These endpoints only interact with the history store, so they are fine.

@router.get("/sessions", response_model=SessionsResponse)
async def get_all_sessions(chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)):
    """Get all active session IDs with their titles."""
    sessions = chatbot.get_sessions_with_titles()
    return SessionsResponse(sessions=sessions, count=len(sessions))

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)):
    """Get chat history for a specific session."""
    messages = chatbot.get_session_messages(session_id)
    if not messages and not chatbot.get_session_history(session_id):
         raise HTTPException(status_code=404, detail="Session not found")
    return ChatHistoryResponse(session_id=session_id, messages=messages, count=len(messages))

@router.delete("/sessions/{session_id}", response_model=DeleteResponse)
async def delete_session(session_id: str, chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)):
    """Completely remove a session and its history."""
    if not chatbot.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse(message=f"Session {session_id} completely deleted", success=True, session_id=session_id)

@router.delete("/history/all", response_model=DeleteResponse)
async def clear_all_chat_histories(chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)):
    """Clears all message histories from all sessions."""
    chatbot.clear_all_histories()
    return DeleteResponse(message="All session histories cleared.", success=True)

@router.delete("/history/{session_id}", response_model=DeleteResponse)
async def clear_chat_history(session_id: str, chatbot: AdaptiveLegalChatbot = Depends(get_adaptive_chatbot)):
    """Clear all chat messages for a specific session, but keep the session."""
    if not chatbot.clear_session_history(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return DeleteResponse(message=f"Chat history cleared for session {session_id}", success=True, session_id=session_id)

# --- Health Check (no changes needed) ---
@router.get("/health")
async def chatbot_health(request: Request):
    """Health check endpoint to verify chatbot initialization."""
    return {
        "status": "healthy" if hasattr(request.app.state, 'adaptive_chatbot_service') and request.app.state.adaptive_chatbot_service else "unavailable",
        "adaptive_chatbot_service_initialized": hasattr(request.app.state, 'adaptive_chatbot_service') and request.app.state.adaptive_chatbot_service is not None,
        "legacy_chatbot_service_initialized": hasattr(request.app.state, 'legacy_chatbot_service') and request.app.state.legacy_chatbot_service is not None
    }