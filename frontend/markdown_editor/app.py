#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 编辑器后端服务器
提供 PDF 导出等后端功能
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import markdown
import tempfile
import os
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

app = Flask(__name__)
CORS(app)

# 配置字体
font_config = FontConfiguration()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'Markdown 编辑器后端服务运行正常'
    })

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """导出 PDF 接口"""
    try:
        data = request.get_json()
        markdown_content = data.get('content', '')
        title = data.get('title', 'Markdown Document')
        
        if not markdown_content:
            return jsonify({'error': '内容不能为空'}), 400
        
        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['codehilite', 'fenced_code', 'tables', 'toc']
        )
        
        # 创建完整的 HTML 文档
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #fff;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 2em;
                    margin-bottom: 1em;
                }}
                h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                }}
                pre {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                    border-left: 4px solid #3498db;
                }}
                blockquote {{
                    border-left: 4px solid #3498db;
                    margin: 0;
                    padding-left: 20px;
                    color: #666;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    text-align: left;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                @page {{
                    margin: 2cm;
                    size: A4;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # 生成 PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            HTML(string=full_html).write_pdf(
                tmp_file.name,
                font_config=font_config
            )
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'{title}.pdf',
                mimetype='application/pdf'
            )
            
    except Exception as e:
        return jsonify({'error': f'PDF 导出失败: {str(e)}'}), 500

@app.route('/api/export/html', methods=['POST'])
def export_html():
    """导出 HTML 接口"""
    try:
        data = request.get_json()
        markdown_content = data.get('content', '')
        title = data.get('title', 'Markdown Document')
        
        if not markdown_content:
            return jsonify({'error': '内容不能为空'}), 400
        
        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['codehilite', 'fenced_code', 'tables', 'toc']
        )
        
        # 创建完整的 HTML 文档
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #fff;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 2em;
                    margin-bottom: 1em;
                }}
                h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                h2 {{ border-bottom: 1px solid #ecf0f1; padding-bottom: 5px; }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                }}
                pre {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                    border-left: 4px solid #3498db;
                }}
                blockquote {{
                    border-left: 4px solid #3498db;
                    margin: 0;
                    padding-left: 20px;
                    color: #666;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    text-align: left;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return jsonify({
            'html': full_html,
            'filename': f'{title}.html'
        })
        
    except Exception as e:
        return jsonify({'error': f'HTML 导出失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 启动 Markdown 编辑器后端服务器...")
    print("📡 服务地址: http://localhost:5000")
    print("🛑 按 Ctrl+C 停止服务器")
    print("")
    app.run(debug=True, host='0.0.0.0', port=5000)

