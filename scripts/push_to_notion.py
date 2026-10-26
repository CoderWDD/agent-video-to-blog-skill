import os
import sys
import json
import argparse
from datetime import datetime
from config_loader import get_config

def markdown_to_notion_blocks(md_text: str) -> list:
    """简易实用的 Markdown 转 Notion 原生 Blocks 解析器"""
    blocks = []
    lines = md_text.split("\n")
    in_code_block = False
    code_lang = "plain text"
    code_lines = []

    for line in lines:
        stripped = line.strip()

        # 处理代码块 (含 Mermaid)
        if stripped.startswith("```"):
            if in_code_block:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "caption": [],
                        "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}],
                        "language": code_lang.lower() if code_lang else "plain text"
                    }
                })
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lang = stripped[3:].strip() or "plain text"
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not stripped:
            continue

        # 标题 1
        if stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]
                }
            })
        # 标题 2
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[3:]}}]
                }
            })
        # 标题 3
        elif stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[4:]}}]
                }
            })
        # 引用 Callout / Quote
        elif stripped.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}],
                    "icon": {"emoji": "💡"}
                }
            })
        # 无序列表
        elif stripped.startswith("- ") or stripped.startswith("* "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": stripped[2:]}}]
                }
            })
        # 普通段落
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": stripped}}]
                }
            })

    return blocks

def push_to_notion(post_data: dict, cfg: dict) -> str:
    """直接使用 requests 调用 Notion REST API 创建文章，轻量稳定无超时问题"""
    import requests

    notion_cfg = cfg.get("notion", {})
    token = notion_cfg.get("token") or os.environ.get("NOTION_TOKEN")
    db_id = notion_cfg.get("database_id") or os.environ.get("NOTION_DATABASE_ID")
    default_status = notion_cfg.get("default_status", "Draft")
    props_mapping = notion_cfg.get("properties", {})

    if not token or "NOTION_TOKEN" in token:
        raise ValueError("缺少有效的 NOTION_TOKEN")
    if not db_id or "NOTION_DATABASE_ID" in db_id:
        raise ValueError("缺少有效的 NOTION_DATABASE_ID")

    timeout_sec = int(notion_cfg.get("timeout_ms", 30000)) // 1000

    title = post_data.get("title", "未命名文章")
    tags = post_data.get("tags", ["学习笔记"])
    slug = post_data.get("slug", f"post-{int(datetime.now().timestamp())}")
    cover_url = post_data.get("cover_url")
    summary = post_data.get("summary", "")
    category = post_data.get("category", "学习笔记")
    post_type = post_data.get("type", "Post")
    markdown_content = post_data.get("content", "")

    # 构建 Notion Properties (针对用户的 CoderWDD Blog 字段)
    properties = {
        props_mapping.get("title", "title"): {
            "title": [{"type": "text", "text": {"content": title}}]
        },
        props_mapping.get("status", "status"): {
            "select": {"name": default_status}
        },
        props_mapping.get("slug", "slug"): {
            "rich_text": [{"type": "text", "text": {"content": slug}}]
        },
        props_mapping.get("date", "date"): {
            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
        },
        props_mapping.get("tags", "tags"): {
            "multi_select": [{"name": tag} for tag in tags]
        },
        props_mapping.get("type", "type"): {
            "select": {"name": post_type}
        },
        props_mapping.get("category", "category"): {
            "select": {"name": category}
        }
    }

    if summary:
        properties[props_mapping.get("summary", "summary")] = {
            "rich_text": [{"type": "text", "text": {"content": summary}}]
        }

    # 解析正文为 Notion Blocks
    children_blocks = markdown_to_notion_blocks(markdown_content)

    # 创建页面参数
    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
        "children": children_blocks[:100] # Notion 单次最大 100 blocks
    }

    if cover_url:
        payload["cover"] = {
            "type": "external",
            "external": {"url": cover_url}
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload, timeout=timeout_sec)
    if res.status_code != 200:
        raise RuntimeError(f"Notion API 错误 ({res.status_code}): {res.text}")

    return res.json().get("url", "")

def main():
    parser = argparse.ArgumentParser(description="Notion 博客自动发布器")
    parser.add_argument("--json", required=True, help="文章完整 JSON Payload 文件路径")
    args = parser.parse_args()

    cfg = get_config()
    with open(args.json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    try:
        page_url = push_to_notion(payload, cfg)
        print(json.dumps({"status": "success", "page_url": page_url}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
