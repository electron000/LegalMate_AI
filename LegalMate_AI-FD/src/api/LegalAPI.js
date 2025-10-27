import { getSessionId } from './SessionManager';

// Ensure your .env file has VITE_CHATBOT_API_URL
const API_BASE_URL = import.meta.env.VITE_CHATBOT_API_URL || 'http://127.0.0.1:8000'

// --- NEW: Key Management ---
const API_KEYS_STORAGE_KEY = 'legalMateApiKeys';

export const saveApiKeys = (keys) => {
  try {
    // Keys provided are { google, cohere, tavily }
    const keysJson = JSON.stringify(keys);
    localStorage.setItem(API_KEYS_STORAGE_KEY, keysJson);
  } catch (error) {
    console.error("Could not save API keys to localStorage", error);
  }
};

export const getApiKeys = () => {
  try {
    const keysJson = localStorage.getItem(API_KEYS_STORAGE_KEY);
    if (!keysJson) return null;
    const keys = JSON.parse(keysJson);
    
    // Basic validation
    if (keys.google && keys.cohere && keys.tavily) {
      return keys;
    }
    // Clear invalid/incomplete keys
    clearApiKeys();
    return null;
  } catch (error) {
    console.error("Could not retrieve API keys from localStorage", error);
    return null;
  }
};

export const clearApiKeys = () => {
  try {
    localStorage.removeItem(API_KEYS_STORAGE_KEY);
  } catch (error) {
    console.error("Could not clear API keys from localStorage", error);
  }
};

// --- MODIFIED: API Response Handler ---
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
    const detail = errorBody.detail || 'The server returned an error.';

    // CRITICAL: If keys are bad, clear them and force a reload
    if (detail.includes("API Key") || response.status === 400 || response.status === 401 || response.status === 403) {
      clearApiKeys();
      // Use location.reload() to force App.jsx to re-check keys
      window.location.reload(); 
      throw new Error("Invalid API Key provided. Please re-enter your keys.");
    }

    throw new Error(detail);
  }
  return response.json();
};

// --- MODIFIED: Chatbot API Functions ---

export const askAdaptive = async (query) => {
  const sessionId = getSessionId();
  const keys = getApiKeys(); // Get keys from storage

  if (!keys) {
    throw new Error("API keys are not set. Please reset them from the sidebar.");
  }

  const url = `${API_BASE_URL}/chat/legal_assistant`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      query, 
      session_id: sessionId,
      // Add the keys to the request body
      google_api_key: keys.google,
      cohere_api_key: keys.cohere,
      tavily_api_key: keys.tavily
    }),
  });
  return handleResponse(response);
};

export const askSimple = async (query) => {
  const sessionId = getSessionId();
  const keys = getApiKeys(); // Get keys from storage

  if (!keys) {
    throw new Error("API keys are not set. Please reset them from the sidebar.");
  }
  
  const url = `${API_BASE_URL}/chat/legal_assistant/simple`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      query, 
      session_id: sessionId,
      // Add the keys to the request body
      google_api_key: keys.google,
      cohere_api_key: keys.cohere,
      tavily_api_key: keys.tavily
    }),
  });
  return handleResponse(response);
};

// --- History/Session Functions (Unchanged) ---
// These functions do not require API keys to operate.

export const getHistory = async (sessionId) => {
  const url = `${API_BASE_URL}/chat/history/${sessionId}`;
  const response = await fetch(url);
  return handleResponse(response);
};

export const deleteCurrentSession = async (sessionId) => {
  const url = `${API_BASE_URL}/chat/sessions/${sessionId}`;
  const response = await fetch(url, { method: 'DELETE' });
  return handleResponse(response);
};

export const clearCurrentHistory = async (sessionId) => {
  const url = `${API_BASE_URL}/chat/history/${sessionId}`;
  const response = await fetch(url, { method: 'DELETE' });
  return handleResponse(response);
};

export const getAllSessions = async () => {
    const url = `${API_BASE_URL}/chat/sessions`;
    const response = await fetch(url);
    return handleResponse(response);
};

export const clearAllHistories = async () => {
    const url = `${API_BASE_URL}/chat/history/all`;
    const response = await fetch(url, { method: 'DELETE' });
    return handleResponse(response);
};
