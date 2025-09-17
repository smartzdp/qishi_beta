#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import re
import json
import regex
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# —————— 配置你的 Facebook 会话信息 ——————
cookies = {
    'sb': 'VzrqZ-9BFsRFdMVO56-feW_5',
    'ps_l': '1',
    'ps_n': '1',
    'locale': 'zh_CN',
    'ar_debug': '1',
    'datr': '0HM1aAuymweekAZ9kjaix9Iw',
    'c_user': '61554221451396',
    'xs': '22%3AFdw0gP4Z5KW-_g%3A2%3A1748333568%3A-1%3A-1',
    'fr': '1lqS5IfWdn7a9kjYo.AWc9Twto43sYWNRPPLrQj9FITqpDQigL59T9g2XejZNuiuQSzDs.BoNV0m..AAA.0.0.BoNXZU.AWeKVOp_lsvxfL0Z2HkVUupV7YQ',
    'wd': '676x723',
    'presence': 'C%7B%22t3%22%3A%5B%5D%2C%22utc3%22%3A1748334352075%2C%22v%22%3A1%7D',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'max-age=0',
    # 'referer': 'https://bluelinxco.com/',
    'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0',
}

GRAPHQL_URL = 'https://www.facebook.com/api/graphql/'
DOC_ID = '24137441009173208'
REQ_NAME = 'ProfileCometTimelineFeedRefetchQuery'


def _get(d: dict, path: list, default=None):
    """ 安全取值，避免 KeyError/IndexError """
    cur = d
    for key in path:
        if isinstance(cur, dict):
            cur = cur.get(key, default)
        elif isinstance(cur, list) and isinstance(key, int) and 0 <= key < len(cur):
            cur = cur[key]
        else:
            return default
    return cur


def extract_hashtags(text: str) -> list[str]:
    return [w for w in text.split() if w.startswith("#")]


def extract_post_info(node: dict) -> dict | None:
    """ 从单个 node 提取所需字段 """
    # 链接
    post_url = (
            node.get("wwwURL")
            or _get(node, ["feedback", "url"])
            or (f"https://www.facebook.com/{node.get('post_id')}" if node.get("post_id") else None)
    )
    if not post_url:
        return None

    # 正文
    text = _get(node, ["comet_sections", "content", "story", "message", "text"], "")

    # 点赞/评论/分享
    likes = _get(node, [
        "comet_sections", "feedback", "story",
        "story_ufi_container", "story",
        "feedback_context", "feedback_target_with_context",
        "comet_ufi_summary_and_actions_renderer",
        "feedback", "reaction_count", "count"
    ]) or _get(node, ["feedback", "reaction_count", "count"], 0)

    comments = _get(node, [
        "comet_sections", "feedback", "story",
        "story_ufi_container", "story",
        "feedback_context", "feedback_target_with_context",
        "comet_ufi_summary_and_actions_renderer",
        "feedback", "comment_rendering_instance", "comments", "total_count"
    ]) or _get(node, ["feedback", "comment_rendering_instance", "comments", "total_count"], 0)

    shares = _get(node, [
        "comet_sections", "feedback", "story",
        "story_ufi_container", "story",
        "feedback_context", "feedback_target_with_context",
        "comet_ufi_summary_and_actions_renderer",
        "feedback", "share_count", "count"
    ]) or _get(node, ["feedback", "share_count", "count"], 0)

    # 多封面
    subs = _get(node, [
        "comet_sections", "content", "story",
        "attachments", 0, "styles", "attachment",
        "all_subattachments", "nodes"
    ], []) or []
    cover_urls = []
    if subs:
        for item in subs:
            uri = _get(item, ["media", "image", "uri"])
            if uri:
                cover_urls.append(uri)
    else:
        single = _get(node, [
            "comet_sections", "content", "story",
            "attachments", 0, "styles", "attachment", "media",
            "placeholder_image", "uri"
        ])
        if single:
            cover_urls = [single]

    # 作者
    author = _get(node, ["actors", 0, "name"])

    # 时间戳（优先 context_layout）
    timestamp = _get(node, [
        "comet_sections", "context_layout", "story",
        "comet_sections", "metadata", 0,
        "story", "creation_time"
    ])
    if timestamp is None:
        for item in _get(node, ["comet_sections", "metadata"], []) or []:
            if item.get("__typename") == "CometFeedStoryMinimizedTimestampStrategy":
                timestamp = _get(item, ["story", "creation_time"])
                break

    # 标签
    hashtags = extract_hashtags(text)
    formatted_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
    return {
        "post_url": post_url,
        "text": text,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "cover_urls": cover_urls,
        "author": author,
        "timestamp": timestamp,
        "formatted_time": formatted_time,
        "hashtags": hashtags,
    }


def init_session(url):
    """ 抓首页 JS，提取 fb_dtsg、初始 end_cursor 和 variables """
    print("初始化会话，抓取首页 JS")
    session = requests.Session()
    resp = session.get(url, cookies=cookies, headers=headers, allow_redirects=True)
    # 检查是否发生跳转
    if resp.url != url:
        print(f"检测到跳转，从 {url} 跳转到 {resp.url}")
        resp = session.get(resp.url, cookies=cookies, headers=headers)
    text = resp.text

    soup = BeautifulSoup(text, "html.parser")

    token = None
    end_cursor = None
    variables_list = []

    for script in soup.find_all("script"):
        if not script.string:
            continue
        text = script.string

        # 提取 token
        if '"dtsg"' in text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                match = re.search(r"({.*\"dtsg\".*})", text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                else:
                    continue

            data_str = json.dumps(data)
            match = regex.search(r'"dtsg"\s*:\s*(\{(?:[^{}]|(?1))*\})', data_str)
            if match:
                json_data = json.loads(match.group(1))
                token = json_data.get('token')
                print(f"提取到 token: {token}")

        # 提取 end_cursor
        if '"end_cursor"' in text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                match = re.search(r"({.*\"end_cursor\".*})", text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                else:
                    continue

            data_str = json.dumps(data)
            match = regex.search(r'"page_info"\s*:\s*(\{(?:[^{}]|(?1))*\})', data_str)
            if match:
                json_data = json.loads(match.group(1))
                end_cursor_ = json_data.get('end_cursor')
                if json_data.get('has_next_page') and len(end_cursor_) > 5:
                    end_cursor = end_cursor_
                    print(f"提取到 end_cursor: {end_cursor}")

        # 提取 variables
        if '"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider"' in text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                match = re.search(r"({.*\"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider\".*})", text,
                                  re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                else:
                    continue

            data_str = json.dumps(data)
            matches = regex.finditer(r'"variables"\s*:\s*(\{(?:[^{}]|(?1))*\})', data_str)

            for i, match in enumerate(matches, start=1):
                try:
                    variables = json.loads(match.group(1))
                    if "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider" in variables:
                        variables_list.append(variables)
                        print(f"提取到 variables: {variables}")
                except Exception as e:
                    print(f"[Match {i}] JSON 解析失败：{e}")

    vars0 = variables_list[0]
    vars0['cursor'] = end_cursor
    vars0['beforeTime'] = None
    if 'userID' in vars0:
        vars0['id'] = vars0.pop('userID')
    if 'count' in vars0:
        vars0['count'] = 3

    return token, vars0, session


def fetch_page(token: str, variables: dict, session: requests.Session):
    """ 发一次 GraphQL 请求，返回本页 posts 列表和下一游标 """
    print("发送 GraphQL 请求")
    payload = {
        '__a': '1',
        '__comet_req': '15',
        'fb_dtsg': token,
        'fb_api_caller_class': 'RelayModern',
        'fb_api_req_friendly_name': REQ_NAME,
        'variables': json.dumps(variables),
        'server_timestamps': 'true',
        'doc_id': DOC_ID,
    }
    resp = session.post(GRAPHQL_URL, headers=headers, cookies=cookies, data=payload)
    text = resp.text
    posts, next_cursor = [], None

    for line in text.splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        # page_info
        if obj.get("label", "").endswith("$page_info"):
            pi = obj.get("data", {}).get("page_info", {})
            next_cursor = pi.get("end_cursor")
            print(f"提取到下一页游标: {next_cursor}")
            continue
        # 流式 node
        if obj.get("label", "").startswith(
                "ProfileCometTimelineFeed_user$stream$ProfileCometTimelineFeed_user_timeline_list_feed_units"
        ) and _get(obj, ["data", "node"]):
            node = obj["data"]["node"]
            p = extract_post_info(node)
            if p: 
                posts.append(p)
                print(f"提取到帖子信息: {p}")
        # edges 列表
        elif _get(obj, ["data", "node", "timeline_list_feed_units", "edges"]):
            for edge in obj["data"]["node"]["timeline_list_feed_units"]["edges"]:
                node = edge.get("node")
                if node:
                    p = extract_post_info(node)
                    if p: 
                        posts.append(p)
                        print(f"提取到帖子信息: {p}")

    return posts, next_cursor


def facebook_main(N, url):
    print(f"开始抓取 Facebook 数据，目标 URL: {url}")
    pages = math.ceil(N / 3)
    token, variables, session = init_session(url)
    all_posts = []
    post_info_data = {'posts': []}
    for i in range(pages):
        print(f"抓取第 {i+1} 页")
        page_posts, next_cursor = fetch_page(token, variables, session)
        all_posts.extend(page_posts)
        post_info_data['posts'].extend(page_posts)
        if not next_cursor:
            print("没有更多页面可抓取")
            break
        variables['cursor'] = next_cursor
    print(f"抓取完成，共获取 {len(all_posts)} 条帖子")
    print(all_posts)
    return all_posts, post_info_data

if __name__ == "__main__":
    url = 'https://www.facebook.com/bluelinx/'
    # url = 'https://www.facebook.com/Tradeling-107554627574491'
    facebook_main(3, url)
