/**
 * Application constants and configuration
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
  ENDPOINTS: {
    FILES: '/api/files',
    QUERY: '/api/query',
    UPLOAD: '/api/ingest/upload',
    CODE: '/api/code',
    STT: '/ws/stt',
    TTS: '/ws/tts'
  }
}

// UI Text Constants
export const UI_TEXT = {
  APP: {
    TITLE: '📊 Excel Agent',
    SUBTITLE: '智能Excel分析助手',
    FOOTER: 'Excel Agent v1.0 | GenAI Class Project'
  },
  
  QUERY_PANEL: {
    TITLE: '🔍 提问分析',
    PLACEHOLDER: '输入你的问题，或点击上方示例问题...',
    AI_OPTION_LABEL: '🤖 使用AI生成个性化代码',
    AI_OPTION_HINT: '（根据实际数据和问题智能生成）',
    BUTTONS: {
      START: '🚀 开始分析',
      VOICE_START: '🎤 语音',
      VOICE_STOP: '🔴 停止'
    },
    ERRORS: {
      EMPTY_QUESTION: '请输入问题',
      QUERY_FAILED: '查询失败',
      STT_FAILED: '语音识别失败',
      MICROPHONE_DENIED: '无法访问麦克风',
      STT_INIT_FAILED: '语音功能初始化失败'
    }
  },
  
  UPLOAD_PANEL: {
    TITLE: '📁 上传Excel文件',
    ACCEPTED_TYPES: '.xlsx,.xls',
    BUTTONS: {
      UPLOAD: '上传并处理',
      UPLOADING: '上传中...'
    },
    ERRORS: {
      NO_FILE: '请选择文件',
      UPLOAD_FAILED: '上传失败'
    }
  },
  
  STREAM_VIEW: {
    TITLE: '📊 分析过程',
    PROCESSING: '正在处理...',
    SECTIONS: {
      INTENT: '🎯 意图解析',
      CANDIDATES: '📁 候选文件',
      PLAN: '📋 执行计划',
      PROMPT: '📝 生成代码的Prompt（调试信息）',
      CODE: '💻 生成代码',
      EXEC_LOG: '📝 执行日志',
      RESULT: '📊 分析结果',
      LINEAGE: '🔍 数据追溯',
      SUMMARY: '📝 总结',
      ERROR: '❌ 错误'
    },
    INTENT_TAGS: {
      AGGREGATION: '聚合分析',
      GROUPBY: '分组统计',
      TREND: '趋势分析',
      RANKING: '排名分析',
      GROWTH: '增长分析',
      TEXT_ANALYSIS: '文本分析',
      PRICE_ANALYSIS: '价格分析'
    }
  },
  
  SAMPLE_FILES: {
    TITLE: '📚 示例数据库',
    HINT: '💡 无需上传，可直接提问分析',
    LOADING: '加载文件中...',
    ERROR: '加载文件失败'
  },
  
  UPLOADED_FILES: {
    TITLE: '已上传文件'
  },
  
  CODE_BLOCK: {
    COPY: '📋 复制',
    COPIED: '✓ 已复制'
  },
  
  COMMON: {
    ERROR_PREFIX: '❌',
    LOADING_SPINNER: '加载中...'
  }
}

// Example Questions (can be made dynamic later)
export const EXAMPLE_QUESTIONS = [
  "统计各个工作表的数据量",
  "显示产品清仓价格排名", 
  "分析学生答辩意见的关键词",
  "比较各地区的销售趋势"
]

// Audio Configuration
export const AUDIO_CONFIG = {
  SAMPLE_RATE: 16000,  // Use 16kHz for browser compatibility, will resample to 24kHz
  BUFFER_SIZE: 4096,   // ≈256 ms at 16 kHz
  CHANNELS: 1
}

// File Configuration
export const FILE_CONFIG = {
  MAX_SIZE_MB: 10,
  ACCEPTED_TYPES: ['.xlsx', '.xls'],
  ACCEPTED_MIME_TYPES: [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel'
  ]
}

// UI Configuration
export const UI_CONFIG = {
  QUERY_TEXTAREA_ROWS: 4,
  COPY_FEEDBACK_DURATION: 2000,
  DEBOUNCE_DELAY: 300
}
