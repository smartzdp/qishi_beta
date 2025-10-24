import React, { useState, useRef } from 'react'
import { queryStream, connectSTT } from '../api/client'
import { UI_TEXT, EXAMPLE_QUESTIONS, AUDIO_CONFIG, UI_CONFIG } from '../config/constants'

function QueryPanel({ onQueryStart, onQueryComplete, onStreamData, disabled }) {
  const [question, setQuestion] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const sttRef = useRef(null)
  const streamDataRef = useRef({})

  const handleQuery = () => {
    if (!question.trim()) {
      setError(UI_TEXT.QUERY_PANEL.ERRORS.EMPTY_QUESTION)
      return
    }

    setError(null)
    onQueryStart()
    streamDataRef.current = {}

    queryStream(question, {
      use_llm_codegen: true, // 始终使用AI生成代码
      onEvent: (eventType, data) => {
        
        // Accumulate stream data
        streamDataRef.current[eventType] = data
        onStreamData({ ...streamDataRef.current })
      },
      onError: (err) => {
        setError(err.message || UI_TEXT.QUERY_PANEL.ERRORS.QUERY_FAILED)
        onQueryComplete()
      },
      onComplete: () => {
        onQueryComplete()
      }
    })
  }

  const handleVoiceToggle = () => {
    if (isRecording) {
      // Stop recording
      if (sttRef.current) {
        // Send stop signal before closing
        if (sttRef.current.ws && sttRef.current.ws.readyState === WebSocket.OPEN) {
          sttRef.current.ws.send(JSON.stringify({ type: 'stop' }))
          // Wait a bit for final transcription before closing
          setTimeout(() => {
            if (sttRef.current) {
              sttRef.current.close()
              sttRef.current = null
            }
          }, 3000) // Wait 3 seconds for final transcription
        } else {
          sttRef.current.close()
          sttRef.current = null
        }
      }
      setIsRecording(false)
    } else {
      // Start recording
      setIsRecording(true)
      
      try {
        sttRef.current = connectSTT(
          (data) => {
            if (data.type === 'partial_text') {
              // Show partial text with indicator
              setQuestion(prev => {
                const cleanPrev = prev.replace(/\s*\[正在识别...\]\s*$/, '')
                return cleanPrev + data.text + ' [正在识别...]'
              })
            } else if (data.type === 'final_text') {
              // Final transcription - append to previous text
              setQuestion(prev => {
                const cleanPrev = prev.replace(/\s*\[正在识别...\]\s*$/, '')
                return cleanPrev + (cleanPrev ? ' ' : '') + data.text
              })
            }
          },
          (err) => {
            console.error('STT error:', err)
            setError(UI_TEXT.QUERY_PANEL.ERRORS.STT_FAILED)
            setIsRecording(false)
          }
        )

        // Start capturing audio with basic configuration
        navigator.mediaDevices.getUserMedia({ 
          audio: {
            sampleRate: AUDIO_CONFIG.SAMPLE_RATE,
            channelCount: AUDIO_CONFIG.CHANNELS
          }
        })
          .then(stream => {
            const audioContext = new AudioContext({ 
              sampleRate: AUDIO_CONFIG.SAMPLE_RATE,
              latencyHint: 'interactive'
            })
            const source = audioContext.createMediaStreamSource(stream)
            const processor = audioContext.createScriptProcessor(AUDIO_CONFIG.BUFFER_SIZE, AUDIO_CONFIG.CHANNELS, AUDIO_CONFIG.CHANNELS)

            source.connect(processor)
            processor.connect(audioContext.destination)

            processor.onaudioprocess = (e) => {
              const audioData = e.inputBuffer.getChannelData(0)

              // Convert to 16-bit PCM with proper scaling
              const pcm16 = new Int16Array(audioData.length)
              for (let i = 0; i < audioData.length; i++) {
                // Apply proper scaling and clamping
                const sample = Math.max(-1, Math.min(1, audioData[i]))
                pcm16[i] = Math.round(sample * 32767)
              }
              
              if (sttRef.current && sttRef.current.ws && sttRef.current.ws.readyState === WebSocket.OPEN) {
                // Send as binary data (bytes)
                sttRef.current.ws.send(pcm16.buffer)
              }
            }
          })
          .catch(err => {
            console.error('Microphone access denied:', err)
            setError(UI_TEXT.QUERY_PANEL.ERRORS.MICROPHONE_DENIED)
            setIsRecording(false)
          })
      } catch (err) {
        setError(UI_TEXT.QUERY_PANEL.ERRORS.STT_INIT_FAILED)
        setIsRecording(false)
      }
    }
  }

  // 示例问题 - 现在从配置文件获取
  const exampleQuestions = EXAMPLE_QUESTIONS

  const handleExampleClick = (example) => {
    setQuestion(example)
  }

  return (
    <div className="query-panel">
      <h2>{UI_TEXT.QUERY_PANEL.TITLE}</h2>
      
      <div className="example-questions">
        <span className="example-label">💡 试试这些问题：</span>
        {exampleQuestions.map((example, idx) => (
          <button
            key={idx}
            className="example-question-btn"
            onClick={() => handleExampleClick(example)}
            disabled={disabled}
          >
            {example}
          </button>
        ))}
      </div>

      <div className="query-input-container">
        <textarea
          className="query-input"
          placeholder={UI_TEXT.QUERY_PANEL.PLACEHOLDER}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={UI_CONFIG.QUERY_TEXTAREA_ROWS}
          disabled={disabled}
        />
        
        {/* AI选项已移除，始终使用AI生成代码 */}
        
        <div className="query-actions">
          <button
            className="btn btn-primary"
            onClick={handleQuery}
            disabled={disabled || !question.trim()}
          >
            {UI_TEXT.QUERY_PANEL.BUTTONS.START}
          </button>
          
          <button
            className={`btn btn-voice ${isRecording ? 'recording' : ''}`}
            onClick={handleVoiceToggle}
            disabled={disabled}
            title={isRecording ? '停止录音' : '语音输入'}
          >
            {isRecording ? UI_TEXT.QUERY_PANEL.BUTTONS.VOICE_STOP : UI_TEXT.QUERY_PANEL.BUTTONS.VOICE_START}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {UI_TEXT.COMMON.ERROR_PREFIX} {error}
        </div>
      )}
    </div>
  )
}

export default QueryPanel

