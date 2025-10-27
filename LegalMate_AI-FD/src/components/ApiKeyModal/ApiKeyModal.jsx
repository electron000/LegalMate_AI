import React, { useState } from 'react';
import { KeyRound, ExternalLink, TriangleAlert, Eye, EyeOff } from 'lucide-react';
import './ApiKeyModal.css'; // <-- Import the external CSS

// This is a new, self-contained component for the API key modal.
const ApiKeyModal = ({ onKeysSubmit, initialKeys = {} }) => {
  const [keys, setKeys] = useState({
    google: initialKeys.google || '',
    cohere: initialKeys.cohere || '',
    tavily: initialKeys.tavily || '',
  });
  const [error, setError] = useState('');
  const [showKeys, setShowKeys] = useState({ google: false, cohere: false, tavily: false });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setKeys((prev) => ({ ...prev, [name]: value.trim() }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!keys.google || !keys.cohere || !keys.tavily) {
      setError('Please fill in all three API keys to proceed.');
      return;
    }
    setError('');
    onKeysSubmit(keys);
  };

  const toggleShowKey = (keyName) => {
    setShowKeys((prev) => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  return (
    <>
      <div className="api-modal-backdrop" />
      <div className="api-modal-container">
        <div className="api-modal-content">
          <div className="api-modal-header">
            <KeyRound size={24} className="header-icon" />
            <h2>Enter Your API Keys</h2>
          </div>
          <p className="modal-description">
            LegalMate AI requires your personal API keys to function. These keys are stored
            <strong> only in your browser's local storage</strong>.
          </p>
          
          <div className="api-alert">
            <TriangleAlert size={16} />
            <span>All three keys are required for the app to work.</span>
          </div>

          <form onSubmit={handleSubmit} className="api-form">
            {/* --- Google API Key --- */}
            <div className="form-group">
              <label htmlFor="google-key">Google AI Studio Key</label>
              <div className="input-wrapper">
                <input
                  id="google-key"
                  name="google"
                  type={showKeys.google ? 'text' : 'password'}
                  value={keys.google}
                  onChange={handleChange}
                  placeholder="Enter your Google AI API key"
                  className="key-input"
                />
                <button type="button" onClick={() => toggleShowKey('google')} className="eye-icon">
                  {showKeys.google ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="key-link">
                Get your Google key <ExternalLink size={12} />
              </a>
            </div>

            {/* --- Cohere API Key --- */}
            <div className="form-group">
              <label htmlFor="cohere-key">Cohere API Key</label>
              <div className="input-wrapper">
                <input
                  id="cohere-key"
                  name="cohere"
                  type={showKeys.cohere ? 'text' : 'password'}
                  value={keys.cohere}
                  onChange={handleChange}
                  placeholder="Enter your Cohere API key"
                  className="key-input"
                />
                <button type="button" onClick={() => toggleShowKey('cohere')} className="eye-icon">
                  {showKeys.cohere ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <a href="https://dashboard.cohere.com/api-keys" target="_blank" rel="noopener noreferrer" className="key-link">
                Get your Cohere key <ExternalLink size={12} />
              </a>
            </div>

            {/* --- Tavily API Key --- */}
            <div className="form-group">
              <label htmlFor="tavily-key">Tavily API Key</label>
              <div className="input-wrapper">
                <input
                  id="tavily-key"
                  name="tavily"
                  type={showKeys.tavily ? 'text' : 'password'}
                  value={keys.tavily}
                  onChange={handleChange}
                  placeholder="Enter your Tavily API key"
                  className="key-input"
                />
                <button type="button" onClick={() => toggleShowKey('tavily')} className="eye-icon">
                  {showKeys.tavily ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <a href="https://app.tavily.com/sign-in" target="_blank" rel="noopener noreferrer" className="key-link">
                Get your Tavily key <ExternalLink size={12} />
              </a>
            </div>
            
            {error && <p className="form-error">{error}</p>}

            <button type="submit" className="save-keys-button">
              Save and Start Chatting
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

export default ApiKeyModal;
