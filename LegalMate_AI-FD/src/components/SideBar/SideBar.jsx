import React from 'react';
import { Plus, Menu, Trash2, ShieldX } from 'lucide-react';
// --- PATH FIXED ---
// Assumes 'legal-logo.png' is in the 'public' folder.
import legalLogo from '/legal-logo.png'; 
import './SideBar.css';

/**
 * The sidebar component now manages displaying chat sessions and provides
 * controls for creating, selecting, and deleting them.
 */
const SideBar = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  onClearAllSessions, // New prop for clearing all chats
  createNewSession,
  isExpanded,
  onMouseEnter,
  onMouseLeave
}) => {
  return (
    <div 
      className={`sidebar ${isExpanded ? 'expanded' : ''}`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="sidebar-content-wrapper">
        {/* Collapsed View */}
        <div className="sidebar-view collapsed-view">
          <button className="sidebar-icon-btn menu-btn" aria-label="Menu" onClick={onMouseEnter}>
            <Menu size={20} />
          </button>
          <button className="sidebar-icon-btn new-chat-icon-btn" onClick={createNewSession} aria-label="New Legal Query">
            <Plus size={24} />
          </button>
        </div>

        {/* Expanded View */}
        <div className="sidebar-view expanded-view">
          <div className="sidebar-header">
            <img src={legalLogo} alt="Legal Logo" className="logo" />
            <span className="brand-name">LegalMate AI</span>
          </div>
          <button className="new-chat-btn" onClick={createNewSession}>
            <Plus size={16} />New Legal Query
          </button>
          
          {/* --- MODIFICATION: Threads section to display chat history --- */}
<div className="threads-section">
            <div className="threads-header">Recent Chats</div>
            <div className="threads-list">
              {/* --- MODIFICATION: Ensure key is on the top-level element --- */}
              {sessions.map((session) => (
                <div key={session.id} className="thread-item-container">
                  <button
                    className={`thread-item ${session.id === activeSessionId ? 'active' : ''}`}
                    onClick={() => onSelectSession(session.id)}
                  >
                    <span className="thread-title">{session.title || 'New Chat'}</span>
                  </button>
                  <button 
                    className="delete-session-btn" 
                    aria-label={`Delete chat ${session.title}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* --- MODIFICATION: Button to clear all chat histories --- */}
          <button className="new-chat-btn clear-all-btn" onClick={onClearAllSessions}>
            <ShieldX size={16} />Clear All Chats
          </button>
        </div>
      </div>
    </div>
  );
};

export default SideBar;
