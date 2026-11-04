import requests
from pathlib import Path

key = Path(r"C:\Users\eusun\.config\opencode\deepseek-key").read_text(encoding="utf-8").strip()
print("key len:", len(key))

for model in ("deepseek-v4-flash", "deepseek-chat"):
    try:
        r = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "spune 'ok'"}], "max_tokens": 5},
            timeout=30,
        )
        print(model, "->", r.status_code, r.text[:200])
    except Exception as e:
        print(model, "-> EXC", e)