import React, { useState } from 'react'
import { uploadFile } from '../api/client'
import { UI_TEXT, FILE_CONFIG } from '../config/constants'

function UploadPanel({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError(UI_TEXT.UPLOAD_PANEL.ERRORS.NO_FILE)
      return
    }

    setUploading(true)
    setError(null)

    try {
      const result = await uploadFile(selectedFile)
      onUploadSuccess(result)
      setSelectedFile(null)
      // Reset file input
      document.getElementById('file-input').value = ''
    } catch (err) {
      setError(err.message || UI_TEXT.UPLOAD_PANEL.ERRORS.UPLOAD_FAILED)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-panel">
      <h2>{UI_TEXT.UPLOAD_PANEL.TITLE}</h2>
      
      <div className="file-input-container">
        <input
          id="file-input"
          type="file"
          accept={FILE_CONFIG.ACCEPTED_TYPES.join(',')}
          onChange={handleFileSelect}
          disabled={uploading}
        />
        
        {selectedFile && (
          <div className="selected-file">
            <span>已选择: {selectedFile.name}</span>
            <span className="file-size">
              ({(selectedFile.size / 1024).toFixed(1)} KB)
            </span>
          </div>
        )}
      </div>

      <button
        className="btn btn-primary"
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
      >
        {uploading ? UI_TEXT.UPLOAD_PANEL.BUTTONS.UPLOADING : UI_TEXT.UPLOAD_PANEL.BUTTONS.UPLOAD}
      </button>

      {error && (
        <div className="error-message">
          {UI_TEXT.COMMON.ERROR_PREFIX} {error}
        </div>
      )}
    </div>
  )
}

export default UploadPanel

