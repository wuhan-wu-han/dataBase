"""无需向量数据库的伪 RAG：对项目文档做轻量关键词/字符二元组检索。"""

import os
import re
from functools import lru_cache

from . import config

ALLOWED_EXTENSIONS = {".md", ".txt", ".rst"}
SKIP_PARTS = {"node_modules", ".git", "dist", "target", "__pycache__"}
MAX_FILES = 180
MAX_CHUNK = 900


def _tokens(text):
    lowered = str(text or "").lower()
    words = set(re.findall(r"[a-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}", lowered))
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", lowered))
    words.update(chinese[i:i + 2] for i in range(max(0, len(chinese) - 1)))
    return words


def _candidate_files():
    roots = [
        config._REPO_ROOT,
        os.path.join(config._REPO_ROOT, "alarm-warning-service", "docs"),
        os.path.join(config._REPO_ROOT, "docs"),
    ]
    found = []
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_PARTS and not d.startswith(".")]
            for name in files:
                path = os.path.join(current, name)
                if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS or path in seen:
                    continue
                relative = os.path.relpath(path, config._REPO_ROOT).replace("\\", "/")
                priority = any(k in relative.lower() for k in ("readme", "api", "interface", "plan", "emergency", "应急", "接口", "预案"))
                found.append((0 if priority else 1, path, relative))
                seen.add(path)
    found.sort(key=lambda item: (item[0], item[2]))
    return found[:MAX_FILES]


@lru_cache(maxsize=1)
def _index():
    chunks = []
    for _, path, relative in _candidate_files():
        try:
            text = open(path, "r", encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        sections = re.split(r"\n\s*\n|(?=^#{1,4}\s)", text, flags=re.M)
        for section in sections:
            clean = re.sub(r"\s+", " ", section).strip()
            if len(clean) < 40:
                continue
            for start in range(0, len(clean), MAX_CHUNK):
                piece = clean[start:start + MAX_CHUNK]
                chunks.append({"source": relative, "text": piece, "tokens": _tokens(piece)})
    return chunks


@lru_cache(maxsize=1)
def _dynamic_index():
    """把接口能力清单和应急预案业务数据也作为可检索资料。"""
    chunks = []
    try:
        from . import tools
        for schema in tools.TOOL_SCHEMAS:
            fn = schema.get("function", {})
            text = "接口能力 %s：%s；参数：%s" % (
                fn.get("name", ""), fn.get("description", ""),
                fn.get("parameters", {}).get("properties", {}),
            )
            chunks.append({"source": "平台接口能力清单", "text": text, "tokens": _tokens(text)})
    except Exception:
        pass
    try:
        from plan_api.store import load_plans
        for plan in load_plans().values():
            nodes = plan.get("flow_nodes") or plan.get("nodes") or []
            text = "应急预案：%s；类别：%s；说明：%s；触发条件：%s；流程：%s" % (
                plan.get("plan_name") or plan.get("name") or plan.get("plan_id"),
                plan.get("category_name") or plan.get("category") or "",
                plan.get("description") or "", plan.get("trigger") or "",
                "、".join(str(node.get("title") or node.get("name") or "") for node in nodes[:12]),
            )
            chunks.append({"source": "平台应急预案库", "text": text, "tokens": _tokens(text)})
    except Exception:
        pass
    return chunks


def retrieve(query, limit=4):
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    ranked = []
    for chunk in _index() + _dynamic_index():
        overlap = query_tokens & chunk["tokens"]
        if not overlap:
            continue
        score = sum(3 if len(token) > 2 else 1 for token in overlap)
        ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [{"source": item[1]["source"], "content": item[1]["text"]} for item in ranked[:limit]]
