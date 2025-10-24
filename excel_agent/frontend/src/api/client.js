/**
 * API client with fetch, EventSource, and WebSocket support
 */
import { API_CONFIG } from '../config/constants'

const API_BASE_URL = API_CONFIG.BASE_URL;

/**
 * Get list of available files
 */
export async function getFiles() {
  const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.FILES}/list`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get files');
  }

  return response.json();
}

/**
 * Get file details
 */
export async function getFileDetails(fileName) {
  const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.FILES}/${encodeURIComponent(fileName)}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get file details');
  }

  return response.json();
}

/**
 * Upload a file
 */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.UPLOAD}`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Query with SSE streaming
 */
export function queryStream(question, options = {}) {
  const {
    language = 'zh',
    top_k = 3,
    allow_files = null,
    disallow_files = null,
    use_llm_codegen = false,
    onEvent = () => {},
    onError = () => {},
    onComplete = () => {}
  } = options;

  const requestBody = {
    question,
    language,
    top_k,
    allow_files,
    disallow_files,
    use_llm_codegen
  };

  // EventSource doesn't support POST natively
  // Use fetch with streaming instead
  fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.QUERY}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Query failed with status ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let buffer = '';
      
      function readStream() {
        reader.read().then(({ done, value }) => {
          if (done) {
            onComplete();
            return;
          }
          
          const text = decoder.decode(value, { stream: true });
          buffer += text;
          
          // Process complete events (separated by double newlines)
          const events = buffer.split('\n\n');
          
          // Keep the last incomplete event in buffer
          buffer = events.pop() || '';
          
          for (const event of events) {
            if (!event.trim()) continue;
            
            const lines = event.split('\n');
            let eventType = '';
            let eventData = '';
            
            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventType = line.substring(6).trim();
              } else if (line.startsWith('data:')) {
                eventData = line.substring(5).trim();
              }
            }
            
            if (eventType && eventData) {
              try {
                const data = JSON.parse(eventData);
                onEvent(eventType, data);
              } catch (e) {
                console.error('Failed to parse event data:', e, 'Raw data:', eventData);
              }
            }
          }
          
          readStream();
        });
      }
      
      readStream();
    })
    .catch(error => {
      onError(error);
    });

  return {
    close: () => {
      // No-op for fetch approach
    }
  };
}

/**
 * Execute code directly
 */
export async function executeCode(code, fileName, sheetName, timeout = 10) {
  const response = await fetch(`${API_BASE_URL}${API_CONFIG.ENDPOINTS.CODE}/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      code,
      file_name: fileName,
      sheet_name: sheetName,
      timeout
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Execution failed');
  }

  return response.json();
}

/**
 * WebSocket for STT
 */
export function connectSTT(onMessage = () => {}, onError = () => {}) {
  const ws = new WebSocket(`${API_CONFIG.WS_BASE_URL}${API_CONFIG.ENDPOINTS.STT}`);

  ws.onopen = () => {
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('Failed to parse STT message:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('STT WebSocket error:', error);
    onError(error);
  };

  ws.onclose = () => {
  };

  return {
    send: (data) => ws.send(data),
    close: () => ws.close(),
    readyState: ws.readyState,
    ws: ws  // Expose the WebSocket for direct access
  };
}

/**
 * WebSocket for TTS
 */
export function connectTTS(onAudio = () => {}, onError = () => {}) {
  const ws = new WebSocket(`${API_CONFIG.WS_BASE_URL}${API_CONFIG.ENDPOINTS.TTS}`);

  ws.onopen = () => {
  };

  ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      // Audio data
      onAudio(event.data);
    } else {
      // Control message
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'end') {
        }
      } catch (e) {
        console.error('Failed to parse TTS message:', e);
      }
    }
  };

  ws.onerror = (error) => {
    console.error('TTS WebSocket error:', error);
    onError(error);
  };

  ws.onclose = () => {
  };

  return {
    speak: (text) => ws.send(text),
    close: () => ws.close()
  };
}

