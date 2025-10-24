import React, { useState, useEffect } from 'react'
import UploadPanel from './components/UploadPanel'
import QueryPanel from './components/QueryPanel'
import StreamView from './components/StreamView'
import { getFiles } from './api/client'
import { UI_TEXT } from './config/constants'

function App() {
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [streamData, setStreamData] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [sampleFiles, setSampleFiles] = useState([])
  const [filesLoading, setFilesLoading] = useState(true)
  const [filesError, setFilesError] = useState(null)

  const handleUploadSuccess = (result) => {
    setUploadedFiles(prev => [...prev, result])
  }

  const handleQueryStart = () => {
    setIsProcessing(true)
    setStreamData(null)
  }

  const handleQueryComplete = () => {
    setIsProcessing(false)
    // 不要清空streamData，保持结果显示
  }

  const handleStreamData = (data) => {
    setStreamData(data)
  }

  // Load files on component mount
  useEffect(() => {
    const loadFiles = async () => {
      try {
        setFilesLoading(true)
        setFilesError(null)
        const response = await getFiles()
        
        if (response.success) {
          setSampleFiles(response.files)
        } else {
          setFilesError(response.error || UI_TEXT.SAMPLE_FILES.ERROR)
        }
      } catch (error) {
        console.error('Error loading files:', error)
        setFilesError(error.message || UI_TEXT.SAMPLE_FILES.ERROR)
      } finally {
        setFilesLoading(false)
      }
    }

    loadFiles()
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>{UI_TEXT.APP.TITLE}</h1>
        <p className="subtitle">{UI_TEXT.APP.SUBTITLE}</p>
      </header>

      <main className="app-main">
        <div className="panels-container">
          <div className="left-panel">
            {/* 示例文件区域 */}
            <div className="sample-files">
              <h3>{UI_TEXT.SAMPLE_FILES.TITLE} ({sampleFiles.length} 个文件)</h3>
              <p className="sample-hint">{UI_TEXT.SAMPLE_FILES.HINT}</p>
              
              {filesLoading && (
                <div className="loading-indicator">
                  <div className="spinner"></div>
                  <span>{UI_TEXT.SAMPLE_FILES.LOADING}</span>
                </div>
              )}
              
              {filesError && (
                <div className="error-message">
                  {UI_TEXT.COMMON.ERROR_PREFIX} {filesError}
                </div>
              )}
              
              {!filesLoading && !filesError && sampleFiles.map((file, idx) => (
                <div key={idx} className="file-item sample-file-item">
                  <div className="file-info">
                    <span className="file-name">{file.file_name}</span>
                    <span className="file-description">{file.description}</span>
                  </div>
                  <span className="file-sheets">{file.sheets} 个工作表</span>
                </div>
              ))}
            </div>

            <div className="divider"></div>

            <UploadPanel onUploadSuccess={handleUploadSuccess} />
            
            {uploadedFiles.length > 0 && (
              <div className="uploaded-files">
                <h3>{UI_TEXT.UPLOADED_FILES.TITLE} ({uploadedFiles.length})</h3>
                {uploadedFiles.map((file, idx) => (
                  <div key={idx} className="file-item">
                    <span className="file-name">{file.file_name}</span>
                    <span className="file-sheets">{file.processed_sheets} 个工作表</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="right-panel">
            <QueryPanel
              onQueryStart={handleQueryStart}
              onQueryComplete={handleQueryComplete}
              onStreamData={handleStreamData}
              disabled={isProcessing}
            />
            
            {/* 始终显示StreamView，即使没有数据也显示占位符 */}
            <StreamView data={streamData} isProcessing={isProcessing} />
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>{UI_TEXT.APP.FOOTER}</p>
      </footer>
    </div>
  )
}

export default App

