import json
import requests
from openai import OpenAI

from config import BOCHAAI_URL, BOCHAAI_API_KEY, ARK_URL, ARK_API_KEY


def bocha_web_search(web_query):
    key = BOCHAAI_API_KEY
    url = BOCHAAI_URL

    payload = json.dumps({
        "query": web_query,
        "count": 10,
        "summary": True,
    })

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())
    web_pages = response.json().get("data", {}).get("webPages", {}).get("value", [])

    top_results = []
    for page in web_pages:
        result = {
            "title": page.get("name"),
            "url": page.get("url"),
            "date": page.get("dateLastCrawled"),
            "source": page.get("siteName"),
            "logo": page.get("siteIcon"),
            "summary": page.get("summary"),
            "snippet": page.get("snippet")
        }
        top_results.append(result)
        
    web_articles_text = "\n\n```\n".join(
        f"标题：{web.get('title', '无标题')}\n"
        f"日期：{web.get('date', '未知日期')}\n"
        f"内容：{web.get('summary', '')}"
        for web in top_results
    )
    return web_articles_text


def ask_llm(query, websearch=None):
    if ARK_API_KEY:
        client = OpenAI(
            base_url=ARK_URL,
            api_key=ARK_API_KEY,
        )
        response = client.chat.completions.create(
            model="deepseek-v3-250324",
            messages=[
                {"role": "user", "content": f"{query}\n\n参考资料：\n{websearch}" if websearch is not None else query}
            ],
            max_tokens=4000,
            timeout=60
        )
    else:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": f"{query}\n\n参考资料：\n{websearch}" if websearch is not None else query}
            ],
            max_completion_tokens=4000,
            timeout=60
        )
    
    return response.choices[0].message.content


