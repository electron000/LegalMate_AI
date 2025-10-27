// No changes needed. This file does not make API calls.

import { v4 as uuidv4 } from 'uuid';

const SESSION_ID_KEY = 'ai_legalmate_session_id';

export function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_ID_KEY);

  if (!sessionId) {
    sessionId = uuidv4();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }

  return sessionId;
}

export function clearAndResetSession() {
  localStorage.removeItem(SESSION_ID_KEY);
}
