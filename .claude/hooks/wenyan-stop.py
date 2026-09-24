#!/usr/bin/env python3
"""Stop hook：最後回報不是文言文就擋下，請 Claude 以文言文重寫一次。

- stop_hook_active 為真（已被擋過一次）→ 放行，避免無限迴圈
- 最後一則回覆已像文言文 → 放行
- 否則回傳 decision=block，reason 會交給 Claude 當作繼續的指示
"""
import json
import sys

CLASSICAL = "之乎者也矣焉哉耳兮曰乃亦皆其然則故"
MODERN = "的了是我你這那們嗎呢吧"


def last_assistant_text(data: dict) -> str:
    text = data.get("last_assistant_message")
    if isinstance(text, str) and text:
        return text
    path = data.get("transcript_path")
    if not path:
        return ""
    last = ""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                message = entry.get("message") or {}
                if entry.get("type") != "assistant" or message.get("role") != "assistant":
                    continue
                content = message.get("content")
                if isinstance(content, str):
                    parts = [content]
                else:
                    parts = [c.get("text", "") for c in content or [] if c.get("type") == "text"]
                joined = "".join(parts).strip()
                if joined:
                    last = joined
    except OSError:
        return ""
    return last


def looks_classical(text: str) -> bool:
    han = [ch for ch in text if "一" <= ch <= "鿿"]
    if len(han) < 8:
        return False
    classical = sum(ch in CLASSICAL for ch in han)
    modern = sum(ch in MODERN for ch in han)
    return classical >= 3 and classical > modern * 2


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if data.get("stop_hook_active"):
        return
    if looks_classical(last_assistant_text(data)):
        return
    print(json.dumps({
        "decision": "block",
        "reason": (
            "停止前須以文言文回報。請將本輪所為、所得、未竟之事，以文言文重述一則，"
            "簡明為要；路徑、指令、網址、git hash 等技術標記照原樣保留，勿譯。"
            "此則回報之外，勿再動工。"
        ),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
