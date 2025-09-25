import base64
import logging
import mimetypes
import os
import time
import traceback

import fitz
from openai import OpenAI

from config import IMAGE_MODEL_URL, IMAGE_MODEL_API_KEY


def context_augmentation(page_context, image_description):
    prompt = f"""
目标：通过图片的上下文以及来源文件信息补充图片描述的细节，准确描述出图片在文档中的实际内容和用途含义。

注意事项：
- 上下文中可能会有噪音，请注意甄别。
- 重点关注上下文中的图片caption标注，因为它们通常描述图片的用途和意义。
- 保留图片的意图与重要信息，过滤掉与上下文无关的信息。
- 有时图片描述中会出现重复性的内容，这类内容请视为噪音过滤掉。
- 请直接输出答案，无需解释。
- 如果图片不包含任何内容，或者为背景图片，输出 0

期望输出：
- 一段精准并且详细的描述，说明图片在上下文中的作用和意义，以及图片中的重要细节。
- 保留图片描述中的文字以及数据，不要遗漏。

输出案例(供参考)：
1. 图片描述了在狭义相对论的框架下，一个闪光事件在不同参考系（S 和 S'）中的观察结果。在参考系 S 中，闪光发生在 M 点，光信号以光速 c 向各个方向传播。在参考系 S' 中，S' 相对于 S 以速度 u 沿着 MB 方向运动。在 S' 参考系中，A' 和 B' 是两个接收器，它们随着 S' 一起运动。闪光发生后，光信号以光速 c 向各个方向传播，由于 A' 比 B' 早接收到光信号，因此在 S' 参考系中，事件1（A' 接收到光信号）先于事件2（B' 接收到光信号）发生。图片中标注了各个事件发生的位置和时间关系，其中 AM' < BM'，说明在 S' 参考系中，A' 比 B' 更靠近闪光发生的位置 M。
2. 图片2.1展示了网络爬虫的工作原理。爬虫程序从互联网上获取数据，经过筛选和清洗，提取出有价值的信息，去除无关数据，最终形成结构化的数据。这一过程体现了爬虫技术在数据采集和处理中的关键作用，尤其是在大数据时代，爬虫技术能够自动化地获取大量信息，为后续的数据分析和应用提供了基础支持。
3. 图片展示了杭州市公安局西湖风景区名胜区分局西湖核心景区监控设施提升完善及安全提升项目的文档统计情况。统计内容包括：考核数38，已提交29；按时提交的文档数15，及时提交的12，未及时提交的2。具体文档包括开工申请、监理工作总结、方案计划报审表、开工令和周报等，以及各自的提交截止日期和实际提交日期。

图片描述：
```
{image_description}
```

上下文：
```
{page_context}
```
"""
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "你是一个智能AI助手，根据图片的上下文对图片描述进行补充，补充后的描述要更加准确，更加详细，更加完整。"},
            {"role": "user", "content": prompt}
        ]
    )
    result = response.choices[0].message.content
    return result

def summarize_image(image_path):
    retry = 0
    while retry <= 5:
        try:
            text = f"""
详细地描述这张图片的内容，不要漏掉细节，并提取图片中的文字。注意只需客观说明图片内容，无需进行任何评价。
"""
            client = OpenAI(api_key=IMAGE_MODEL_API_KEY, base_url=IMAGE_MODEL_URL)

            # Read local image and convert to Base64 data URL
            with open(image_path, "rb") as f:
                content_bytes = f.read()
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
            encoded = base64.b64encode(content_bytes).decode("utf-8")
            data_url = f"data:{mime_type};base64,{encoded}"
            
            resp = client.chat.completions.create(
                model="internvl-internlm2",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text}, 
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }], 
                temperature=0.8, 
                top_p=0.8, 
                max_tokens=2048, 
                stream=False
            )
            
            return resp.choices[0].message.content
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(e)
            time.sleep(1)
            retry += 1
            
    return None


def extract_images_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    logging.info(f"Opened PDF document: {pdf_path}")

    image_dir = "pdf_images/"
    os.makedirs(image_dir, exist_ok=True)
    logging.info(f"Image directory created: {image_dir}")
    
    unique_xrefs = set()
    for p in range(pdf_document.page_count):
        page_images = pdf_document.get_page_images(p)
        for item in page_images:
            xref = item[0]
            unique_xrefs.add(xref)
    total_images = len(unique_xrefs)
    
    if total_images == 0:
        pdf_document.close()
        return []

    results = []
    processed_xrefs = set()

    for page_num in range(pdf_document.page_count):
        try:
            page = pdf_document.load_page(page_num)
            page_width = page.rect.width

            # Extract page text, 作为图片上下文
            page_text = page.get_text("dict", sort=True)
            page_context = ""
            for block in page_text["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            page_context += span["text"] + " "
            
            page_images = pdf_document.get_page_images(page_num)
            for img_index, item in enumerate(page_images):
                try:
                    xref = item[0]
                    if xref in processed_xrefs:
                        continue
                    processed_xrefs.add(xref)

                    image_width = item[2]
                    image_height = item[3]
                    
                    # Skip small images
                    if image_width < page_width / 3 or image_width < 200 or image_height < 100:
                        continue
                    
                    pix = fitz.Pixmap(pdf_document, xref)
                    if pix.colorspace and pix.colorspace.name == "DeviceCMYK":
                        pix = fitz.Pixmap(fitz.csRGB, pix)

                    image_save_path = f"{image_dir}/img_{page_num + 1}_{img_index + 1}.png"
                    pix.save(image_save_path)
                    del pix

                    # Optional filter if available
                    do_filter = globals().get("filter_meaningful_images")
                    if callable(do_filter):
                        if not do_filter(image_save_path):
                            os.remove(image_save_path)
                            continue

                    # Summarize single image
                    summary = summarize_image(image_save_path)
                    context_augmented_summary = context_augmentation(page_context, summary)
                    results.append({
                        "page_num": page_num,
                        "image_index": img_index + 1,
                        "summary": summary,
                        "image_path": image_save_path,
                        "page_context": page_context.strip(),
                        "context_augmented_summary": context_augmented_summary
                    })

                    # Pretty print the latest result for readability
                    # print("\n" + "=" * 60)
                    # print(json.dumps(results[-1], ensure_ascii=False, indent=2))
                    # Remove local copy after summarization
                    try:
                        os.remove(image_save_path)
                    except Exception:
                        pass

                except Exception as e:
                    logging.error(f"Error processing image {img_index + 1} on page {page_num + 1}: {e}")
                    logging.error(traceback.format_exc())

        except Exception as e:
            logging.error(f"Error processing page {page_num + 1}: {e}")
            logging.error(traceback.format_exc())

    pdf_document.close()
    return results
