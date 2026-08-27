"""
Hybrid LLM & Gemini Web Service for retranslation and polishing.
Supports:
1. Direct Google Gemini Web API (using browser __Secure-1PSID & __Secure-1PSIDTS cookies) - No server required!
2. OpenAI-compatible API (Ollama, LM Studio, vLLM, WebAI-to-API, etc.)
"""
import httpx
import json
import re
import asyncio
from typing import Optional, Dict, Any, List
from . import config_manager
from . import webai_service

# Default prompts
DEFAULT_RETRANSLATE_PROMPT = """You are a professional Japanese to Indonesian translator specializing in visual novel translation.
Translate the given Japanese text to natural Indonesian.
- Maintain the tone and style appropriate for the context (dialogue, narration, etc.)
- Keep character names as-is (do not translate names).
- If text contains speaker tags like 「name」, preserve them.
- You MUST respond in JSON format: {"translation": "your translated text here"}
- Do NOT include any explanation, commentary, or anything other than the JSON."""

DEFAULT_POLISH_PROMPT = """You are a professional editor for Japanese to Indonesian visual novel translations.
Given the original Japanese text and an existing Indonesian translation, improve the translation quality.
- Fix awkward phrasing and make it sound natural in Indonesian.
- Maintain accuracy to the original Japanese meaning.
- Keep the same tone and style.
- Keep character names as-is.
- You MUST respond in JSON format: {"translation": "your improved translation here"}
- Do NOT include any explanation, commentary, or anything other than the JSON."""

# Model aliases for Gemini Web
GEMINI_WEB_MODEL_MAP = {
    "gemini-3.7-flash": "gemini-3.0-flash",
    "gemini-3.5-flash": "gemini-3.0-flash",
    "gemini-3.0-flash": "gemini-3.0-flash",
    "gemini-2.5-flash": "gemini-3.0-flash",
    "gemini-2.0-flash": "gemini-3.0-flash",
    "flash": "gemini-3.0-flash",
    
    "gemini-3.7-flash-thinking": "gemini-3.0-flash-thinking",
    "gemini-3.7-flash-high": "gemini-3.0-flash-thinking",
    "gemini-3.0-flash-thinking": "gemini-3.0-flash-thinking",
    "thinking": "gemini-3.0-flash-thinking",
    
    "gemini-3.1-pro": "gemini-3.0-pro",
    "gemini-3.0-pro": "gemini-3.0-pro",
    "pro": "gemini-3.0-pro",
    
    "gemini-3.5-flash-lite": "gemini-3.0-flash",
    "gemini-3.1-flash-lite": "gemini-3.0-flash",
}

# Singleton Gemini Web Client
_gemini_client = None
_gemini_client_lock = asyncio.Lock()

def get_llm_config():
    """Get LLM-specific config values."""
    cfg = config_manager.load_config()
    cookies = webai_service.get_gemini_cookies()
    provider = cfg.get("llm_provider", "auto")
    
    # In auto mode: if cookies are present, default to direct gemini_web
    if provider == "auto":
        if cookies.get("has_cookies"):
            resolved_provider = "gemini_web"
        else:
            resolved_provider = "openai"
    else:
        resolved_provider = provider

    return {
        "provider": resolved_provider,
        "api_url": cfg.get("llm_api_url", "http://localhost:6969/v1"),
        "model": cfg.get("llm_model", "gemini-3.7-flash"),
        "temperature": cfg.get("llm_temperature", 0.7),
        "max_tokens": cfg.get("llm_max_tokens", 1024),
        "context_window": cfg.get("llm_context_window", 5),
        "glossary": cfg.get("llm_glossary", []),
        "retranslate_prompt": cfg.get("llm_retranslate_prompt") or DEFAULT_RETRANSLATE_PROMPT,
        "polish_prompt": cfg.get("llm_polish_prompt") or DEFAULT_POLISH_PROMPT,
        "cookies": cookies,
    }


def format_glossary(glossary_entries):
    """Format glossary entries into a prompt-friendly string."""
    if not glossary_entries:
        return ""
    
    lines = ["Use the following glossary for consistent terminology:"]
    for entry in glossary_entries:
        src = entry.get("src", "")
        dst = entry.get("dst", "")
        info = entry.get("info", "")
        if src and dst:
            line = f"  {src} → {dst}"
            if info:
                line += f"  ({info})"
            lines.append(line)
    
    return "\n".join(lines) + "\n"


def build_context_block(rows, target_index, window_size):
    """Build context from surrounding rows."""
    if window_size <= 0 or not rows:
        return ""
    
    start = max(0, target_index - window_size)
    end = min(len(rows), target_index + window_size + 1)
    
    context_lines = []
    for i in range(start, end):
        if i == target_index:
            continue  # Skip target line
        text = rows[i].get("original", "")
        if text.strip():
            marker = "BEFORE" if i < target_index else "AFTER"
            context_lines.append(f"[{marker} line {abs(i - target_index)}]: {text}")
    
    if not context_lines:
        return ""
    
    return "Surrounding context for reference (do NOT translate these, only the target):\n" + "\n".join(context_lines) + "\n"


def extract_translation(raw_text):
    """
    Extract clean translation text from response.
    Supports JSON object extraction with smart regex and fallbacks.
    """
    text = str(raw_text).strip()
    
    # 1. Try direct JSON parsing
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "translation" in data:
            return data["translation"].strip()
    except Exception:
        pass
    
    # 2. Try JSON in markdown block
    json_match = re.search(r'```(?:json)?\s*\n?({.*?})\s*\n?```', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict) and "translation" in data:
                return data["translation"].strip()
        except Exception:
            pass
            
    # 3. Regex for {"translation": "..."}
    match = re.search(r'\{\s*"translation"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', text, re.DOTALL)
    if match:
        result = match.group(1).replace('\\"', '"').replace('\\n', '\n')
        return result.strip()
        
    # 4. Text cleanup fallback
    lines = text.split('\n')
    clean_lines = []
    skip_patterns = [
        r'^\s*#', r'^\s*\*\*', r'^\s*\*', r'^\s*---', r'^\s*>',
        r'Apakah Anda', r'Berikut', r'Mengapa', r'Catatan', r'Penjelasan',
        r'Perubahan', r'Alasan', r'\?\s*$', r'^\s*\(', r'^\s*\d+\.', r'^\s*-\s+\w'
    ]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.search(pat, stripped) for pat in skip_patterns):
            continue
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)
        cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
        clean_lines.append(cleaned)
        
    if clean_lines:
        return '\n'.join(clean_lines).strip()
    return text


async def _get_or_init_gemini_client(force_reconnect=False):
    """Initialize or reuse direct GeminiClient instance."""
    global _gemini_client
    async with _gemini_client_lock:
        cookies = webai_service.get_gemini_cookies()
        if not cookies.get("has_cookies"):
            raise ValueError("Gemini Web cookies (__Secure-1PSID / __Secure-1PSIDTS) are missing. Please configure them in Settings.")

        from gemini_webapi import GeminiClient

        if _gemini_client is None or force_reconnect:
            if _gemini_client is not None:
                try:
                    await _gemini_client.close()
                except Exception:
                    pass
            
            client = GeminiClient(cookies["psid"], cookies["psidts"])
            await client.init(timeout=30, auto_close=False, close_delay=600)
            _gemini_client = client

        return _gemini_client


async def call_gemini_web(prompt: str, model_name: str = "gemini-3.7-flash") -> str:
    """Call Google Gemini Web directly via gemini_webapi in Python."""
    resolved_model = GEMINI_WEB_MODEL_MAP.get(model_name.lower(), "gemini-3.0-flash")
    
    try:
        client = await _get_or_init_gemini_client()
        res = await client.generate_content(prompt, model=resolved_model)
        return getattr(res, "text", str(res))
    except Exception as e:
        # Retry once with fresh client in case session timed out
        print(f"Gemini Web call failed ({e}), re-initializing client...")
        client = await _get_or_init_gemini_client(force_reconnect=True)
        res = await client.generate_content(prompt, model=resolved_model)
        return getattr(res, "text", str(res))


async def call_openai_compatible(messages: list, config: dict) -> str:
    """Call an OpenAI-compatible HTTP LLM API."""
    api_url = config["api_url"].rstrip("/")
    endpoint = f"{api_url}/chat/completions"
    
    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
        "response_format": {"type": "json_object"},
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "").strip()
    raise ValueError("No response from LLM server")


async def call_hybrid_llm(messages: list, config: Optional[dict] = None) -> str:
    """Route LLM call through direct Gemini Web or OpenAI API based on config."""
    if config is None:
        config = get_llm_config()

    provider = config.get("provider", "openai")

    if provider == "gemini_web":
        # Format messages into a single Gemini prompt
        prompt_parts = []
        for m in messages:
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            if role == "SYSTEM":
                prompt_parts.append(f"[System Instructions]\n{content}\n")
            else:
                prompt_parts.append(f"{content}\n")
        full_prompt = "\n".join(prompt_parts)
        return await call_gemini_web(full_prompt, config.get("model", "gemini-3.7-flash"))
    else:
        return await call_openai_compatible(messages, config)


async def retranslate(original_text: str, all_rows=None, target_index=0, config=None) -> str:
    """Retranslate Japanese text to Indonesian."""
    if config is None:
        config = get_llm_config()
        
    system_prompt = config["retranslate_prompt"]
    glossary_text = format_glossary(config["glossary"])
    if glossary_text:
        system_prompt += "\n\n" + glossary_text
        
    user_parts = [system_prompt, ""]
    if all_rows:
        ctx = build_context_block(all_rows, target_index, config["context_window"])
        if ctx:
            user_parts.append(ctx)
            
    user_parts.append(f"Original Japanese:\n{original_text}\n\nProvide Indonesian translation:")
    user_parts.append('\nIMPORTANT: Respond ONLY with JSON: {"translation": "your text"}')
    
    messages = [{"role": "user", "content": "\n".join(user_parts)}]
    raw = await call_hybrid_llm(messages, config)
    return extract_translation(raw)


async def polish(original_text: str, translated_text: str, all_rows=None, target_index=0, config=None) -> str:
    """Polish and improve Indonesian translation."""
    if config is None:
        config = get_llm_config()
        
    system_prompt = config["polish_prompt"]
    glossary_text = format_glossary(config["glossary"])
    if glossary_text:
        system_prompt += "\n\n" + glossary_text
        
    user_parts = [system_prompt, ""]
    if all_rows:
        ctx = build_context_block(all_rows, target_index, config["context_window"])
        if ctx:
            user_parts.append(ctx)
            
    user_parts.append(f"Original Japanese:\n{original_text}\n\nCurrent translation:\n{translated_text}\n\nProvide improved translation:")
    user_parts.append('\nIMPORTANT: Respond ONLY with JSON: {"translation": "your text"}')
    
    messages = [{"role": "user", "content": "\n".join(user_parts)}]
    raw = await call_hybrid_llm(messages, config)
    return extract_translation(raw)


async def test_connection(api_url_override=None, model_override=None, provider_override=None) -> dict:
    """
    Test connection for active mode (Direct Gemini Web or OpenAI API).
    """
    config = get_llm_config()
    provider = provider_override or config["provider"]
    model = model_override or config["model"]
    api_url = (api_url_override or config["api_url"]).rstrip("/")
    
    # 1. Test Direct Gemini Web API
    if provider == "gemini_web":
        cookies = config.get("cookies", {})
        if not cookies.get("has_cookies"):
            return {
                "status": "error",
                "provider": "gemini_web",
                "message": "Gemini Web cookies are missing! Please paste __Secure-1PSID & __Secure-1PSIDTS in 'Edit Cookies' above and click 'Save Cookies'."
            }
        try:
            client = await _get_or_init_gemini_client(force_reconnect=True)
            res = await client.generate_content('Respond with JSON: {"status": "ok"}', model="gemini-3.0-flash")
            return {
                "status": "connected",
                "provider": "gemini_web",
                "mode_label": "Gemini Web (Direct Web-API - No Server Required)",
                "models": [
                    "gemini-3.7-flash (3.7 Flash - Recommended)",
                    "gemini-3.7-flash-thinking (Extended Thinking)",
                    "gemini-3.1-pro (3.1 Pro)",
                    "gemini-3.5-flash-lite (Flash-Lite)"
                ],
                "model_configured": model,
                "message": "Direct connection to Google Gemini Web is active and working!"
            }
        except Exception as e:
            return {
                "status": "error",
                "provider": "gemini_web",
                "message": f"Gemini Web authentication failed: {str(e)}. Please re-check your __Secure-1PSID cookies."
            }

    # 2. Test OpenAI-compatible HTTP API
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.get(f"{api_url}/models")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("id", "unknown") for m in data.get("data", [])]
                    return {
                        "status": "connected",
                        "provider": "openai",
                        "mode_label": "OpenAI / Local LLM HTTP API",
                        "api_url": api_url,
                        "models": models[:15],
                        "model_configured": model,
                    }
            except Exception:
                pass
                
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }
            res = await client.post(f"{api_url}/chat/completions", json=payload)
            res.raise_for_status()
            return {
                "status": "connected",
                "provider": "openai",
                "mode_label": "OpenAI / Local LLM HTTP API",
                "api_url": api_url,
                "models": [model],
                "model_configured": model,
            }
    except httpx.ConnectError:
        return {"status": "error", "provider": "openai", "message": f"Cannot connect to {api_url}. Is your LLM server running?"}
    except httpx.TimeoutException:
        return {"status": "error", "provider": "openai", "message": f"Connection to {api_url} timed out."}
    except Exception as e:
        return {"status": "error", "provider": "openai", "message": str(e)}
