import json
import os
import re
from pathlib import Path


def _expand_home(path_str):
    if path_str.startswith("~"):
        return str(Path.home() / path_str.lstrip("~\\/"))
    return path_str


def resolve_file_ref(value, base_dir):
    if not isinstance(value, str):
        return value
    m = re.match(r"^\{(file|env):(.+)\}$", value.strip())
    if not m:
        return value
    kind, ref = m.group(1), m.group(2)
    if kind == "env":
        return os.getenv(ref, "")
    candidates = []
    stripped = ref.lstrip("~\\/")
    if ref.startswith("~"):
        candidates.append(_expand_home(ref))
        base = Path(base_dir)
        try:
            idx = base.parts.index(".config")
            derived_home = Path(*base.parts[:idx])
            candidates.append(str(derived_home / stripped))
        except ValueError:
            pass
        candidates.append(str(base / stripped))
    else:
        p = Path(ref)
        candidates.append(str(p) if p.is_absolute() else str(Path(base_dir) / p))
    for c in candidates:
        try:
            if Path(c).exists():
                return Path(c).read_text(encoding="utf-8").strip()
        except Exception:
            continue
    return ""


def load_opencode_providers(config_dir):
    cfg = None
    for name in ("opencode.json", "opencode.jsonc"):
        p = Path(config_dir) / name
        if p.exists():
            cfg = p
            break
    if cfg is None:
        return []
    text = cfg.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except Exception:
        return []
    providers = []
    for name, provider in (data.get("provider") or {}).items():
        opts = provider.get("options") or {}
        base = (opts.get("baseURL") or "").rstrip("/")
        key = opts.get("apiKey") or ""
        key = resolve_file_ref(key, config_dir) if key else ""
        models = list((provider.get("models") or {}).keys())
        npm = (provider.get("npm") or "").lower()
        if npm and npm != "@ai-sdk/openai-compatible":
            continue
        if not base or not models:
            continue
        providers.append(
            {
                "name": name,
                "base_url": base,
                "api_key": key,
                "models": models,
                "preferred_model": models[0],
            }
        )
    return providers