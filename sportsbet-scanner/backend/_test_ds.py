import sys
sys.path.insert(0, 'backend')
from pathlib import Path
import requests, json

key = Path(r"C:\Users\eusun\.config\opencode\deepseek-key").read_text(encoding="utf-8").strip()

tools = [{
    "type": "function",
    "function": {
        "name": "get_value_bets",
        "description": "Lista value bets detectate",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}]

r = requests.post(
    "https://api.deepseek.com/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": "ce value bets ai?"}],
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": 100,
    },
    timeout=60,
)
print("status:", r.status_code)
body = r.json()
msg = body["choices"][0]["message"]
print("keys:", list(msg.keys()))
print("tool_calls:", json.dumps(msg.get("tool_calls"), ensure_ascii=False)[:300])
print("content:", str(msg.get("content"))[:100])
print("reasoning:", str(msg.get("reasoning_content"))[:100])