import React from 'react'; // <-- THE FIX IS HERE
import ReactMarkdown from 'react-markdown';
import { AlertTriangle } from 'lucide-react';
import './MessageRenderer.css';

const MessageRenderer = ({ message }) => {
  if (message.role === 'user') {
    return <p>{message.content}</p>;
  }

  if (message.role === 'error') {
    return (
      <div className="error-header">
        <AlertTriangle size={20} />
        <div>
          <h3>Error occurred</h3>
          <p>{message.content.message}</p>
        </div>
      </div>
    );
  }

  if (message.role === 'ai') {
    const { content } = message;

    if (content.type === 'structured') {
      return (
        <div className="ai-response-card">
          <ReactMarkdown
            components={{
              h2: ({node, ...props}) => <h2 className="ai-response-heading" {...props} />,
              h3: ({node, ...props}) => <h3 className="ai-subheading" {...props} />,
              p: ({node, ...props}) => <p className="ai-paragraph" {...props} />,
              strong: ({node, ...props}) => <strong className="ai-bold" {...props} />,
              ul: ({node, ...props}) => <ul className="ai-list" {...props} />,
              li: ({node, ...props}) => <li className="ai-list-item" {...props} />,
            }}
          >
            {content.explanation}
          </ReactMarkdown>
        </div>
      );
    }
    return <div className="ai-response-simple"><ReactMarkdown>{content.content}</ReactMarkdown></div>;
  }

  return null;
};

export default MessageRenderer;

