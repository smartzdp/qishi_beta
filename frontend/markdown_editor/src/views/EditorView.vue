<template>
  <div class="editor-container">
    <el-container class="editor-layout">
      <!-- 顶部标题区域 -->
      <el-header class="editor-header">
        <div class="header-content">
          <div class="title-section">
            <h1 class="main-title">
              <el-icon class="title-icon"><Document /></el-icon>
              Markdown 编辑器
            </h1>
          </div>
          <div class="header-actions">
            <el-button @click="clearContent" :icon="Delete" circle />
            <el-dropdown @command="handleExport">
              <el-button :icon="Download" circle />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="html">导出 HTML</el-dropdown-item>
                  <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="toggleFullscreen" :icon="FullScreen" circle />
          </div>
        </div>
      </el-header>


      <!-- 主编辑区域 -->
      <el-main class="editor-main">
        <div class="editor-wrapper">
          <!-- 编辑面板 -->
          <div v-if="currentMode !== 'preview-only'" class="editor-panel" :class="{ 'full-width': currentMode !== 'split' }">
            <div class="panel-header">
              <h3>编辑</h3>
              <el-button 
                v-if="currentMode === 'split'" 
                @click="showEditorOnly" 
                :icon="Edit" 
                size="small"
              >
                仅编辑
              </el-button>
              <el-button 
                v-if="currentMode === 'editor-only'" 
                @click="togglePreview" 
                :icon="View" 
                size="small"
              >
                显示预览
              </el-button>
            </div>
            <div class="editor-content">
              <el-input
                v-model="markdownContent"
                type="textarea"
                :rows="20"
                placeholder="开始编写您的 Markdown 文档..."
                class="markdown-input"
                @input="handleInput"
              />
            </div>
          </div>

          <!-- 预览面板 -->
          <div v-if="currentMode === 'split' || currentMode === 'preview-only'" class="preview-panel">
            <div class="panel-header">
              <h3>预览</h3>
              <el-button 
                v-if="currentMode === 'split'"
                @click="showPreviewOnly" 
                :icon="View" 
                size="small"
              >
                仅预览
              </el-button>
              <el-button 
                v-if="currentMode === 'preview-only'"
                @click="togglePreview" 
                :icon="Edit" 
                size="small"
              >
                显示编辑
              </el-button>
            </div>
            <div class="preview-content" v-html="renderedMarkdown"></div>
          </div>
        </div>
      </el-main>
    </el-container>

    <!-- 加载提示 -->
    <el-loading
      v-if="isExporting"
      text="正在导出，请稍候..."
      background="rgba(0, 0, 0, 0.7)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEditorStore } from '../stores/editor'
import { parseMarkdown } from '../utils/markdown'
import { downloadHTML, downloadPDF } from '../utils/export'
import { 
  FullScreen, 
  Delete, 
  Download, 
  View, 
  Edit,
  Document
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const editorStore = useEditorStore()

// 编辑器状态
const markdownContent = ref('')
const showPreview = ref(true)
const isExporting = ref(false)
const currentMode = ref('split') // 'split', 'editor-only', 'preview-only'

const renderedMarkdown = computed(() => {
  return parseMarkdown(markdownContent.value)
})

onMounted(() => {
  markdownContent.value = editorStore.markdownContent
})

// 内容处理
const handleInput = () => {
  editorStore.updateContent(markdownContent.value)
}

// 模式切换
const togglePreview = () => {
  showPreview.value = !showPreview.value
  currentMode.value = showPreview.value ? 'split' : 'editor-only'
}

const showEditorOnly = () => {
  showPreview.value = false
  currentMode.value = 'editor-only'
}

const showPreviewOnly = () => {
  showPreview.value = false
  currentMode.value = 'preview-only'
}

// 界面控制
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 内容管理
const clearContent = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有内容吗？此操作不可撤销。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    markdownContent.value = ''
    editorStore.clearContent()
    ElMessage.success('内容已清空')
  } catch {
    // 用户取消
  }
}

// 导出功能
const handleExport = async (command: string) => {
  if (!markdownContent.value.trim()) {
    ElMessage.warning('请先输入一些内容')
    return
  }

  isExporting.value = true
  
  try {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    
    if (command === 'html') {
      await downloadHTML(markdownContent.value, `markdown-${timestamp}.html`)
      ElMessage.success('HTML 文件导出成功')
    } else if (command === 'pdf') {
      await downloadPDF(markdownContent.value, `markdown-${timestamp}.pdf`)
      ElMessage.success('PDF 文件导出成功')
    }
  } catch (error) {
    ElMessage.error('导出失败，请重试')
    console.error('Export error:', error)
  } finally {
    isExporting.value = false
  }
}
</script>

<style scoped>
/* 主容器 */
.editor-container {
  height: 100vh;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
}

.editor-layout {
  height: 100vh;
}

/* 标题区域 */
.editor-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-content {
  color: white;
  padding: 0.3rem 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 60px;
  width: 100%;
}

.title-section {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-right: 20px;
}

.main-title {
  font-size: clamp(1.5rem, 4vw, 2.5rem);
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(0.5rem, 2vw, 1rem);
  flex-wrap: nowrap;
  white-space: nowrap;
}

.title-icon {
  font-size: clamp(1.8rem, 4.5vw, 2.8rem);
}

/* 编辑区域 */
.editor-main {
  padding: 15px;
  height: calc(100vh - 80px);
  overflow: hidden;
}

.editor-wrapper {
  display: flex;
  height: 100%;
  gap: 10px;
  background: transparent;
}

.editor-panel {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.editor-panel.full-width {
  flex: 1;
}

.preview-panel {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #e4e7ed;
  border-radius: 8px;
  margin: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  border-bottom: 1px solid #e4e7ed;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2c3e50;
}

.editor-content {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  background: white;
  border-radius: 0 0 8px 8px;
}

.markdown-input {
  height: 100%;
}

.markdown-input :deep(.el-textarea__inner) {
  height: 100% !important;
  resize: none;
  border: 2px solid #e4e7ed;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 12px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.markdown-input :deep(.el-textarea__inner):focus {
  border-color: #ff9a9e;
  background: white;
  box-shadow: 0 0 0 2px rgba(255, 154, 158, 0.2);
}

.preview-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  background: white;
  border-radius: 0 0 8px 8px;
}

.preview-content :deep(h1) {
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 10px;
  margin-top: 0;
}

.preview-content :deep(h2) {
  color: #2c3e50;
  border-bottom: 1px solid #ecf0f1;
  padding-bottom: 5px;
}

.preview-content :deep(h3),
.preview-content :deep(h4),
.preview-content :deep(h5),
.preview-content :deep(h6) {
  color: #2c3e50;
}

.preview-content :deep(code) {
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.preview-content :deep(pre) {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
  border-left: 4px solid #3498db;
}

.preview-content :deep(blockquote) {
  border-left: 4px solid #3498db;
  margin: 0;
  padding-left: 20px;
  color: #666;
}

.preview-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.preview-content :deep(th) {
  background: #f8f9fa;
  font-weight: 600;
}

.preview-content :deep(img) {
  max-width: 100%;
  height: auto;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .main-title {
    flex-direction: row;
    gap: 0.3rem;
    font-size: clamp(1.2rem, 3.5vw, 2rem);
  }
  
  .header-content {
    padding: 0.2rem 0;
    min-height: 50px;
    flex-direction: column;
    gap: 8px;
  }
  
  .title-section {
    order: 1;
  }
  
  .header-actions {
    order: 2;
    justify-content: center;
    padding-right: 0;
    gap: 8px;
  }
  
  .header-actions .el-button {
    width: 36px;
    height: 36px;
  }
  
  .editor-wrapper {
    flex-direction: column;
  }
  
  .editor-panel,
  .preview-panel {
    flex: none;
    height: 50%;
  }
  
  .preview-panel {
    border-left: none;
    border-top: 1px solid #e4e7ed;
  }
  
  .panel-header {
    padding: 10px 15px;
  }
  
  .editor-content,
  .preview-content {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: clamp(1rem, 3vw, 1.2rem);
    flex-direction: row;
    gap: 0.2rem;
  }
  
  .title-icon {
    font-size: clamp(1.2rem, 3.5vw, 1.5rem);
  }
  
  .header-content {
    padding: 0.1rem 0;
    min-height: 45px;
    gap: 6px;
  }
  
  .header-actions {
    gap: 6px;
  }
  
  .header-actions .el-button {
    width: 32px;
    height: 32px;
  }
  
  .editor-main {
    padding: 10px;
    height: calc(100vh - 70px);
  }
  
  .editor-content,
  .preview-content {
    padding: 12px;
  }
}
</style>

