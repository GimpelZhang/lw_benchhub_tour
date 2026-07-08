#!/usr/bin/env python3
"""DeepSeek-v4-pro caller for Stage 4. Mirrors /mnt/robot/deepseek_v4_pro.py exactly.
Anthropic Messages protocol; STRICTLY deepseek-v4-pro (never deepseek-chat)."""
from __future__ import annotations
import json, os, sys, urllib.error, urllib.request

BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/anthropic")
API_KEY = os.environ.get("DEEPSEEK_API_KEY")  # from deepseek_v4pro_env.sh; never hardcoded
if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY not set. Source /mnt/robot/deepseek_v4pro_env.sh first.")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")   # only v4-pro is allowed
MAX_TOKENS = 32768
TIMEOUT = 180

def ask(messages: list[dict], max_tokens: int = MAX_TOKENS) -> dict:
    url = f"{BASE_URL}/v1/messages"
    payload = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    body = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json", "anthropic-version": "2023-06-01",
               "x-api-key": API_KEY, "Authorization": f"Bearer {API_KEY}"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {e.reason}\n{e.read().decode('utf-8', errors='replace')}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络错误: {e.reason}") from None
    return json.loads(raw)

def extract_text(data: dict) -> str:
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if isinstance(b, dict) and b.get("type") == "text")

def call_deepseek_v4pro(system_prompt: str, user_prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    data = ask([{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}], max_tokens=max_tokens)
    actual = data.get("model", "未知")
    print(f"[请求模型: {MODEL} | 实际响应模型: {actual}]", file=sys.stderr)
    # STRICT anti-degrade guard: response model must equal deepseek-v4-pro exactly.
    if actual != "deepseek-v4-pro":
        print(f"⚠️  警告: 实际响应模型 ({actual}) 与请求 ({MODEL}) 不一致！ABORT.", file=sys.stderr)
        raise RuntimeError(f"model degrade: actual={actual} expected=deepseek-v4-pro")
    text = extract_text(data)
    if not text:
        raise RuntimeError(f"Empty text. Raw: {json.dumps(data, ensure_ascii=False)}")
    return text

if __name__ == "__main__":
    print(call_deepseek_v4pro("You are a helpful assistant.",
                              "Say 'deepseek-v4-pro ready' and nothing else.", max_tokens=64))
