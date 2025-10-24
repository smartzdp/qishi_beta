import React, { useState } from 'react'
import { UI_TEXT, UI_CONFIG } from '../config/constants'

function CodeBlock({ code, language = 'python' }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), UI_CONFIG.COPY_FEEDBACK_DURATION)
  }

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-language">{language}</span>
        <button className="btn-copy" onClick={handleCopy}>
          {copied ? UI_TEXT.CODE_BLOCK.COPIED : UI_TEXT.CODE_BLOCK.COPY}
        </button>
      </div>
      <pre className="code-content">
        <code>{code}</code>
      </pre>
    </div>
  )
}

export default CodeBlock

