import React, { useState, useEffect } from 'react';
import Chatbot from './pages/Chatbot/Chatbot.jsx';
import ApiKeyModal from './components/ApiKeyModal/ApiKeyModal.jsx';
import { getApiKeys, saveApiKeys, clearApiKeys } from './api/LegalAPI.js'

function App() {
  // State to hold the API keys. Starts by checking localStorage.
  const [apiKeys, setApiKeys] = useState(getApiKeys());
  // State to ensure we've checked localStorage before rendering.
  const [isLoading, setIsLoading] = useState(true);

  // On initial component mount, check for keys.
  useEffect(() => {
    const keys = getApiKeys();
    if (keys) {
      setApiKeys(keys);
    }
    setIsLoading(false); // Finished loading
  }, []);

  /**
   * Callback for the ApiKeyModal.
   * Saves the submitted keys to localStorage and updates the state.
   */
  const handleKeysSubmit = (keys) => {
    saveApiKeys(keys);
    setApiKeys(keys);
  };


  const handleResetKeys = () => {
    clearApiKeys();
    setApiKeys(null);
  };

  // While checking localStorage, show nothing to prevent flicker
  if (isLoading) {
    return null;
  }

  // If we have keys, show the main chat app.
  // Otherwise, show the modal to get the keys.
  return (
    <div className="App">
      {apiKeys ? (
        <Chatbot onResetKeys={handleResetKeys} />
      ) : (
        <ApiKeyModal onKeysSubmit={handleKeysSubmit} />
      )}
    </div>
  );
}

export default App;
