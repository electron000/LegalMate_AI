# FILE: main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api import chatbots_routes
from app.services.legalchatbot import AdaptiveLegalChatbot, LegalChatbot # <-- This import is correct

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="LegalMate AI - Chatbot Service",
    description="Standalone AI Legal Assistant Chatbot API (Per-Request API Key Model)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """
    Initialize a shared chat history store and the stateless chatbot services.
    The services will be instantiated without API keys.
    """
    logging.info("Application startup: Initializing shared chat history store...")
    try:
        # This store will be shared by all requests
        app.state.chat_history_store = {}
        
        # Initialize the services, passing the shared store to them
        app.state.adaptive_chatbot_service = AdaptiveLegalChatbot(app.state.chat_history_store)
        app.state.legacy_chatbot_service = LegalChatbot(app.state.chat_history_store)
        
        logging.info("✅ Chat history store and stateless chatbot services initialized successfully.")
    except Exception as e:
        app.state.chat_history_store = None
        app.state.adaptive_chatbot_service = None
        app.state.legacy_chatbot_service = None
        logging.critical(f"❌ CRITICAL: Failed to initialize chatbot services on startup: {e}", exc_info=True)

@app.on_event("shutdown")
def shutdown_event():
    """Log application shutdown."""
    logging.info("Chatbot Service shutdown.")

# Include only the chatbots_routes router
app.include_router(chatbots_routes.router)

@app.get("/")
def root():
    return {
        "message": "AI LegalMate - Chatbot Service is running.",
        "docs": "/docs",
        "note": "This service requires API keys to be provided in the request body."
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )