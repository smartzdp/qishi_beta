import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import { exportToHTML } from './markdown'

export const downloadHTML = (markdown: string, filename: string = 'markdown-document.html') => {
  const html = exportToHTML(markdown)
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export const downloadPDF = async (markdown: string, filename: string = 'markdown-document.pdf') => {
  try {
    // 创建临时容器
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = exportToHTML(markdown)
    tempDiv.style.position = 'absolute'
    tempDiv.style.left = '-9999px'
    tempDiv.style.top = '0'
    tempDiv.style.width = '800px'
    tempDiv.style.padding = '20px'
    document.body.appendChild(tempDiv)

    // 使用 html2canvas 渲染
    const canvas = await html2canvas(tempDiv, {
      scale: 2,
      useCORS: true,
      allowTaint: true
    })

    // 清理临时元素
    document.body.removeChild(tempDiv)

    // 创建 PDF
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210
    const pageHeight = 295
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight

    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft >= 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    pdf.save(filename)
  } catch (error) {
    console.error('PDF 导出失败:', error)
    throw new Error('PDF 导出失败，请重试')
  }
}

