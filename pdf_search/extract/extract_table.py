import fitz
from openai import OpenAI

from utils import truncate_text


def table_context_augmentation(page_context: str, table_md: str):
    """Augment the table description using page context to clarify meaning and usage."""
    client = OpenAI()
    prompt = f"""
目标：请根据输入的表格和上下文信息以及来源文件信息，生成针对于该表格的一段简短的语言描述

注意：
在描述中尽可能包含以下内容：
- 表格名称：根据上下文或表格内容推测表格的名称。
- 表格内容简介：使用自然语言总结表格的内容，包括主要信息、数据点和结构。
- 表格意图：分析表格的用途或目的，例如是否用于展示、比较、统计等。
你生成的描述需要控制在三句话以内。

输出案例：
1. 该表格详细列出了 Apple Inc. 在 2023 年 12 月 31 日至 2024 年 3 月 30 日期间的股票回购情况，包括回购数量、平均价格、公开计划购买的股票数及剩余可购买股票的价值，以展示其资本回报策略。
2. 该表格记录了用户对商品的评分、评论以及相关用户信息，包含字段如订单编号、评分值、评论文本和用户名等，作为协同过滤推荐系统的核心数据来源。其主要作用是通过用户的评分和评论信息，结合协同过滤算法，优化广告推荐的精准度和个性化效果，使系统能够基于用户历史行为和相似用户的偏好，提高广告投放的匹配度。此外，该表格与用户点击行为数据共同构成了智能广告推荐系统的数据基础，可能存储于 MySQL 数据库，并通过 Django 框架进行管理和操作。

输入表格：
{table_md}

表格上下文：
{page_context}
"""

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "你是一个智能AI助手，根据表格的上下文对表格内容进行补充，补充后的内容要更加准确，更加详细，更加完整。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def extract_tables_from_pdf(pdf_path: str):
    """Extract tables from PDF and generate context-augmented descriptions."""
    pdf_document = fitz.open(pdf_path)
    results = []
    
    for page_num in range(pdf_document.page_count):
        try:
            page = pdf_document.load_page(page_num)
            page_text = page.get_text("text")
            page_tables = page.find_tables()

            for table_index, table in enumerate(page_tables):
                try:
                    md = table.to_markdown()
                    augmented = table_context_augmentation(page_text, md)
                    
                    item = {
                        "page_num": page_num,
                        "table_index": table_index + 1,
                        "table_markdown": md,
                        "page_context": page_text.strip(),
                        "context_augmented_table": augmented
                    }
                    results.append(item)

                    # # Markdown-styled pretty print for readability
                    # md_output = (
                    #     "\n" + "-" * 60 + "\n"
                    #     + f"## 第 {page_num + 1} 页 · 表 {table_index + 1}\n\n"
                    #     + "### 表格 (Markdown)\n"
                    #     + "```markdown\n" + md + "\n```\n\n"
                    #     + "### 上下文 (截断显示)\n"
                    #     + "```text\n" + truncate_text(page_text, 1500) + "\n```\n\n"
                    #     + "### 表格说明\n"
                    #     + augmented + "\n"
                    # )
                    # print(md_output)
                except Exception:
                    pass
        except Exception:
            pass

    pdf_document.close()
    return results

