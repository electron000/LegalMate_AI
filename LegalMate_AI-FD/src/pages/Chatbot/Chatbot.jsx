import React, { useState, useEffect, useRef } from 'react';
import { Send, CornerDownLeft, Loader } from 'lucide-react';
// --- PATHS FIXED ---
import Sidebar from '../../components/SideBar/SideBar.jsx';
import MessageRenderer from '../../components/MessageRenderer/MessageRenderer.jsx';
import { askAdaptive, getHistory, deleteCurrentSession, getAllSessions, clearAllHistories } from '../../api/LegalAPI.js';
import { getSessionId, clearAndResetSession } from '../../api/SessionManager.js';
import './Chatbot.css'; 


const formatResponse = (apiResponse) => {
  if (apiResponse.response) {
    return {
      type: 'structured',
      explanation: apiResponse.response,
      metadata: apiResponse.metadata || {},
    };
  }
  return { type: 'simple', content: 'Could not parse the API response.' };
};

// Renamed from Chatbot to Chatbot, accepts `onResetKeys` prop
const Chatbot = ({ onResetKeys }) => {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);
  
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(getSessionId());
  const [showDeleteModal, setShowDeleteModal] = useState({ visible: false, type: null, id: null });
  
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null); // <-- *** ADDED ***

  // Check for 'new=true' in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has('new')) {
      createNewSession();
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Fetch all sessions on initial load
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const sessionData = await getAllSessions();
        setSessions(sessionData.sessions);
      } catch (error) {
        console.error("Failed to load sessions:", error);
      }
    };
    loadSessions();
  }, []);

  // Load chat history when the active session changes
  useEffect(() => {
    const loadHistory = async () => {
      if (!activeSessionId) return;
      setIsLoading(true);
      try {
        const historyData = await getHistory(activeSessionId);
        const formattedMessages = historyData.messages.map(msg => ({
          role: msg.type === 'human' ? 'user' : msg.type,
          content: msg.type === 'ai' ? formatResponse({ response: msg.content }) : msg.content,
        }));
        setMessages(formattedMessages);
      } catch (error) {
        if (error.message.includes("not found")) {
            setMessages([]);
        } else {
            console.error("Failed to load chat history:", error);
        }
      } finally {
        setIsLoading(false);
      }
    };
    loadHistory();
  }, [activeSessionId]);
  
  // Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;

    const userMessage = { role: 'user', content: userInput };
    // Update session title on first message
    if (messages.length === 0) {
        const currentId = getSessionId();
        // Add new session to list if it's not already there
        if (!sessions.some(s => s.id === currentId)) {
            setSessions(prev => [{ id: currentId, title: userInput.substring(0, 40) + '...' }, ...prev]);
        }
    }
    setMessages(prev => [...prev, userMessage]);
    
    const tempInput = userInput;
    setUserInput('');
    setIsLoading(true);

    // <-- *** ADDED *** Reset textarea height after sending
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      // MODIFIED: askAdaptive now only needs the query.
      // The API service handles session ID and API keys.
      const apiResponse = await askAdaptive(tempInput); 
      const formattedResponse = formatResponse(apiResponse);
      const aiMessage = { role: 'ai', content: formattedResponse };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage = { role: 'error', content: { type: 'error', message: err.message } };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // <-- *** ADDED *** New handler for textarea changes
  const handleInputChange = (e) => {
    setUserInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // Reset height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // Set to scroll height
    }
  };
  
  const createNewSession = () => {
    clearAndResetSession();
    const newId = getSessionId();
    setActiveSessionId(newId);
    setMessages([]);
  };

  const handleDelete = async () => {
    const { type, id } = showDeleteModal;
    
    try {
        if (type === 'single') {
            await deleteCurrentSession(id);
            // If we deleted the active chat, start a new one
            if (id === activeSessionId) {
                createNewSession();
            }
            // Refresh session list
            const sessionData = await getAllSessions();
            setSessions(sessionData.sessions);

        } else if (type === 'all') {
            await clearAllHistories();
            setSessions([]);
            createNewSession(); // Start fresh
        }
    } catch (error) {
        console.error("Failed during delete operation:", error);
    } finally {
        setShowDeleteModal({ visible: false, type: null, id: null });
    }
  };

  // This is the modal for DELETING chats (unchanged)
  const DeleteModal = () => {
    if (!showDeleteModal.visible) return null;
    const isSingle = showDeleteModal.type === 'single';
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <h3>{isSingle ? 'Delete Chat?' : 'Delete All Chats?'}</h3>
          <p>{isSingle ? 'This will permanently delete this chat session.' : 'This will permanently clear all your chat histories.'}</p>
          <div className="modal-buttons">
            <button className="btn-cancel" onClick={() => setShowDeleteModal({ visible: false, type: null, id: null })}>Cancel</button>
            <button className="btn-delete" onClick={handleDelete}>Delete</button>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className={`chatbot-page ${isSidebarExpanded ? 'sidebar-expanded' : ''}`}>
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={setActiveSessionId}
        onDeleteSession={(id) => setShowDeleteModal({ visible: true, type: 'single', id })}
        onClearAllSessions={() => setShowDeleteModal({ visible: true, type: 'all', id: null })}
        createNewSession={createNewSession}
        isExpanded={isSidebarExpanded}
        onMouseEnter={() => setIsSidebarExpanded(true)}
        onMouseLeave={() => setIsSidebarExpanded(false)}
        onResetKeys={onResetKeys} // <-- PROP IS CORRECTLY PASSED
      />
      <main className="chat-main">
        <div className="chat-header">
            <div className="model-selector">
                <span>LegalMate AI</span>
                <span className="model-version">1.0</span>
            </div>
        </div>
        <div className="chat-messages">
          {messages.length === 0 && !isLoading ? (
            <div className="welcome-message">
              {/* <div className="welcome-logo"><img src={legalLogo} alt="Legal Logo" /></div> */}
              <h1>LegalMate AI</h1>
              <p>Your intelligent legal assistant for Indian law queries. Ask me anything about legal concepts.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <MessageRenderer message={message} />
              </div>
            ))
          )}
          {isLoading && (
            <div className="message ai">
              <div className="loading-indicator">
                <Loader size={16} className="spinner" />Analyzing your legal query...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <div className="input-area">
          <form className="input-form" onSubmit={handleSendMessage}>
            <div className="input-container">
              <textarea
                ref={textareaRef} // <-- *** MODIFIED ***
                className="message-input"
                value={userInput}
                onChange={handleInputChange} // <-- *** MODIFIED ***
                placeholder="Ask me about Indian law..."
                disabled={isLoading}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(e); }}}
                rows={1}
              />
              <button type="submit" className="send-button" disabled={isLoading || !userInput.trim()}>
                {isLoading ? <Loader size={16} /> : <Send size={16} />}
              </button>
            </div>
          </form>
          <div className="input-footer">
            <p>Press <kbd><CornerDownLeft size={12} /></kbd> to send, <kbd>Shift + ↵</kbd> for new line</p>
          </div>
        </div>
      </main>
      <DeleteModal />
    </div>
  );
};

export default Chatbot;
