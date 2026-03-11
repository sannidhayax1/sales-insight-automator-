'use client';

import { useState, useRef } from 'react';
import axios from 'axios';
import '../styles/file-uploader.css';

export default function FileUploader({ onUpload, onLoading, disabled }) {
  const [email, setEmail] = useState('');
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx'].includes(ext)) {
        setFileName(file.name);
        onUpload(null, null);
      } else {
        onUpload('Please upload a CSV or XLSX file', 'error');
        setFileName('');
      }
    }
  };

  const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !fileName) {
      onUpload('Please fill in all fields and select a file', 'error');
      return;
    }

    if (!validateEmail(email)) {
      onUpload('Please enter a valid email address', 'error');
      return;
    }

    onLoading(true);
    onUpload('Processing your file...', 'loading');

    try {
      const formData = new FormData();
      formData.append('file', fileInputRef.current.files[0]);
      formData.append('recipient_email', email);

      const response = await axios.post(
        `${apiUrl}/api/v1/upload-and-summarize`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000,
        }
      );

      if (response.data.status === 'success') {
        onUpload(
          `✓ Success! Summary sent to ${email}. Summary ID: ${response.data.summary_id}`,
          'success'
        );
        setEmail('');
        setFileName('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'Failed to process file. Please try again.';
      onUpload(`Error: ${errorMessage}`, 'error');
    } finally {
      onLoading(false);
    }
  };

  return (
    <div className="uploader-card">
      <form onSubmit={handleSubmit} className="uploader-form">
        <div className="form-group">
          <label htmlFor="email">Recipient Email</label>
          <input
            id="email"
            type="email"
            placeholder="executive@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={disabled}
            required
            className="input-field"
          />
          <small>The generated summary will be sent to this email</small>
        </div>

        <div className="form-group">
          <label htmlFor="file">Sales Data File</label>
          <div className="file-input-wrapper">
            <input
              id="file"
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileChange}
              disabled={disabled}
              required
              className="file-input"
            />
            <span className="file-input-label">
              {fileName ? `📎 ${fileName}` : '📁 Choose CSV or XLSX'}
            </span>
          </div>
          <small>Supported formats: CSV, XLSX (Max 10MB)</small>
        </div>

        <button
          type="submit"
          disabled={disabled}
          className={`submit-btn ${disabled ? 'disabled' : ''}`}
        >
          {disabled ? '⏳ Processing...' : '🚀 Generate & Send Summary'}
        </button>
      </form>

      <div className="info-box">
        <h3>How it works:</h3>
        <ol>
          <li>Upload your sales CSV or Excel file</li>
          <li>Provide recipient email address</li>
          <li>AI analyzes the data and generates insights</li>
          <li>Summary is automatically emailed</li>
        </ol>
      </div>
    </div>
  );
}
