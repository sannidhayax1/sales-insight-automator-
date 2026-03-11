'use client';

import { useState } from 'react';
import FileUploader from '../components/FileUploader';
import StatusMessage from '../components/StatusMessage';
import '../styles/page.css';

export default function Home() {
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleUpload = (message, type) => {
    setStatus({ message, type });
  };

  const handleLoading = (loading) => {
    setIsLoading(loading);
  };

  return (
    <main className="container">
      <div className="header">
        <h1>Sales Insight Automator</h1>
        <p>Transform your sales data into executive summaries with AI</p>
      </div>

      <div className="content">
        <FileUploader 
          onUpload={handleUpload} 
          onLoading={handleLoading}
          disabled={isLoading}
        />
        
        {status && (
          <StatusMessage 
            message={status.message} 
            type={status.type}
          />
        )}
      </div>

      <footer className="footer">
        <p>Powered by Gemini AI | Sales Insight Automator v1.0</p>
      </footer>
    </main>
  );
}
