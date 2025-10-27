# FILE: llm.py

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

# --- MODIFIED ---
# 'google_api_key' (no default) now comes before arguments with defaults
def get_gemini(google_api_key: str, model_name="gemini-2.5-flash", temperature=0.1):
    """
    Initializes and returns a LangChain ChatGoogleGenerativeAI model instance
    configured with the specified model name, temperature, and API key.
    """
    if not google_api_key:
        raise ValueError("A Google API Key must be provided to initialize the model.")

    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=google_api_key)
    return llm

# Optional: Add a specialized function for different chatbot needs
# --- MODIFIED ---
def get_gemini_for_routing(google_api_key: str, temperature=0.0):
    """
    Get a more deterministic model instance for query classification/routing.
    Lower temperature for consistent classification results.
    """
    # Updated call to use keyword arguments for clarity
    return get_gemini(google_api_key=google_api_key, temperature=temperature)

# --- MODIFIED ---
def get_gemini_for_conversation(google_api_key: str, temperature=0.7):
    """
    Get a slightly more creative model instance for general conversation.
    Higher temperature for more natural, varied responses.
    """
    # Updated call to use keyword arguments for clarity
    return get_gemini(google_api_key=google_api_key, temperature=temperature)