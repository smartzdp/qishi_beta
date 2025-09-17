import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEditorStore = defineStore('editor', () => {
  const markdownContent = ref(`# 欢迎使用 Markdown 编辑器

这是一个功能强大的在线 Markdown 编辑器，支持：

## 功能特性

- **实时预览** - 所见即所得
- **语法高亮** - 代码块语法高亮
- **导出功能** - 支持导出 PDF 和 HTML
- **响应式设计** - 完美适配移动端

## 代码示例

\`\`\`javascript
function hello() {
  console.log('Hello, Markdown Editor!')
}
\`\`\`

## 表格支持

| 功能 | 状态 | 描述 |
|------|------|------|
| 实时预览 | ✅ | 支持实时渲染 |
| 导出PDF | ✅ | 高质量PDF导出 |
| 导出HTML | ✅ | 完整HTML文档 |

> 开始编辑您的 Markdown 文档吧！`)

  const updateContent = (content: string) => {
    markdownContent.value = content
  }

  const clearContent = () => {
    markdownContent.value = ''
  }

  return {
    markdownContent,
    updateContent,
    clearContent
  }
})

