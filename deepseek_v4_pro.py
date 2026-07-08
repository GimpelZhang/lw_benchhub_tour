#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek v4-pro CLI 问答脚本

通过 DeepSeek 的 Anthropic 兼容端点访问 deepseek-v4-pro 模型，
回答命令行输入的问题，并把回答输出到 terminal。

用法:
    python3 deepseek_v4_pro.py "你的问题"
    python3 deepseek_v4_pro.py 请告诉我2026年世界杯7月4日的赛程信息
    echo "你的问题" | python3 deepseek_v4_pro.py        # 从 stdin 读取
    python3 deepseek_v4_pro.py                          # 交互式输入

依赖: 仅使用 Python 标准库 (urllib)，无需 pip install。

注意: 本脚本强制使用 deepseek-v4-pro 模型，绝不退化到 deepseek-chat 等旧模型。
      回答前会在 stderr 打印实际响应的模型名，方便核对。
"""

import json
import os
import sys
import urllib.request
import urllib.error

# ---- 配置 ----
BASE_URL = "https://api.deepseek.com/anthropic"
# 优先从环境变量读取；不内嵌密钥（从 deepseek_v4pro_env.sh 注入 DEEPSEEK_API_KEY）。
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY not set. Source /mnt/robot/deepseek_v4pro_env.sh first.")
# 强制使用 deepseek-v4-pro，不接受旧模型
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
MAX_TOKENS = 4096
TIMEOUT = 180


def ask(question: str) -> dict:
    """向 deepseek-v4-pro 提问，返回原始 JSON 响应 (dict)。"""
    url = f"{BASE_URL}/v1/messages"
    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": question},
        ],
    }
    body = json.dumps(payload).encode("utf-8")

    # 同时携带 x-api-key (Anthropic 风格) 与 Authorization: Bearer (DeepSeek 原生风格)，
    # 提高兼容端点的鉴权成功率，二者共存无害。
    headers = {
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason}\n响应内容:\n{detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络错误: {e.reason}") from None

    return json.loads(raw)


def extract_text(data: dict) -> str:
    """从 Anthropic Messages 响应里抽取纯文本。"""
    parts = []
    for block in data.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def main() -> int:
    # 1) 获取问题：命令行参数 > stdin > 交互输入
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
    else:
        if not sys.stdin.isatty():
            question = sys.stdin.read().strip()
        else:
            try:
                question = input("请输入你的问题: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n已取消。", file=sys.stderr)
                return 130

    if not question:
        print("错误: 未提供问题。", file=sys.stderr)
        print('用法: python3 deepseek_v4_pro.py "你的问题"', file=sys.stderr)
        return 1

    # 2) 调用模型
    try:
        data = ask(question)
    except RuntimeError as e:
        print(f"调用失败: {e}", file=sys.stderr)
        return 2

    # 3) 核对实际响应模型 —— 防止退化到旧模型
    actual_model = data.get("model", "未知")
    print(f"[请求模型: {MODEL} | 实际响应模型: {actual_model}]", file=sys.stderr)
    if actual_model and MODEL not in actual_model:
        # 端点把模型名改写了，明确告警而不是静默退化
        print(f"⚠️  警告: 实际响应模型 ({actual_model}) 与请求 ({MODEL}) 不一致！",
              file=sys.stderr)

    # 4) 输出回答
    answer = extract_text(data)
    if not answer:
        # 兜底：直接打印原始结构，便于排查
        print("（未解析到文本，原始响应如下）", file=sys.stderr)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 3

    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
