"""
LLM Service for retranslation and polishing.
Uses OpenAI-compatible API (works with Ollama, LM Studio, text-generation-webui, etc.)
"""
import httpx
import json
import re
from . import config_manager

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


def get_llm_config():
    """Get LLM-specific config values."""
    cfg = config_manager.load_config()
    return {
        "api_url": cfg.get("llm_api_url", "http://localhost:11434/v1"),
        "model": cfg.get("llm_model", ""),
        "temperature": cfg.get("llm_temperature", 0.3),
        "max_tokens": cfg.get("llm_max_tokens", 1024),
        "context_window": cfg.get("llm_context_window", 5),
        "glossary": cfg.get("llm_glossary", []),
        "retranslate_prompt": cfg.get("llm_retranslate_prompt") or DEFAULT_RETRANSLATE_PROMPT,
        "polish_prompt": cfg.get("llm_polish_prompt") or DEFAULT_POLISH_PROMPT,
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
    """
    Build context from surrounding rows.
    
    Args:
        rows: List of dicts with 'original' key
        target_index: Index of current row being processed
        window_size: Number of lines before/after to include
    
    Returns:
        String with context lines formatted for the prompt
    """
    if window_size <= 0 or not rows:
        return ""
    
    start = max(0, target_index - window_size)
    end = min(len(rows), target_index + window_size + 1)
    
    context_lines = []
    for i in range(start, end):
        if i == target_index:
            continue  # Skip the target line itself
        text = rows[i].get("original", "")
        if text.strip():
            marker = "BEFORE" if i < target_index else "AFTER"
            context_lines.append(f"[{marker} line {abs(i - target_index)}]: {text}")
    
    if not context_lines:
        return ""
    
    return "Surrounding context for reference (do NOT translate these, only the target):\n" + "\n".join(context_lines) + "\n"


def extract_translation(raw_text):
    """
    Extract just the translation text from LLM response.
    Tries JSON parsing first, then falls back to aggressive text cleanup.
    """
    text = raw_text.strip()
    
    # Try to parse as JSON directly
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "translation" in data:
            return data["translation"].strip()
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON block in markdown code fence
    json_match = re.search(r'```(?:json)?\s*\n?({.*?})\s*\n?```', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict) and "translation" in data:
                return data["translation"].strip()
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON object in the text (even surrounded by explanation)
    json_match = re.search(r'\{\s*"translation"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', text, re.DOTALL)
    if json_match:
        result = json_match.group(1)
        result = result.replace('\\"', '"').replace('\\n', '\n')
        return result.strip()
    
    # Aggressive fallback: try to extract just the translation
    # Split into lines and filter out obvious explanation text
    lines = text.split('\n')
    clean_lines = []
    
    # Patterns that indicate explanation/commentary (not translation)
    skip_patterns = [
        r'^\s*#',           # Markdown headers
        r'^\s*\*\*',        # Bold text (usually labels)
        r'^\s*\*',          # Italic/bullet
        r'^\s*---',         # Horizontal rule
        r'^\s*>',           # Blockquote
        r'Apakah Anda',     # Indonesian "Would you like..."
        r'Berikut',         # Indonesian "Here is..."
        r'Mengapa',         # Indonesian "Why..."
        r'Catatan',         # Indonesian "Note..."
        r'Penjelasan',      # Indonesian "Explanation..."
        r'Perubahan',       # Indonesian "Changes..."
        r'Alasan',          # Indonesian "Reason..."
        r'\?\s*$',          # Lines ending with question mark
        r'^\s*\(',          # Lines starting with parentheses
        r'^\s*\d+\.',       # Numbered lists
        r'^\s*-\s+\w',      # Bullet points with text
    ]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check if line matches any skip pattern
        should_skip = False
        for pattern in skip_patterns:
            if re.search(pattern, stripped):
                should_skip = True
                break
        
        if not should_skip:
            # Strip markdown bold/italic markers from actual content
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)
            cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
            clean_lines.append(cleaned)
    
    # If we filtered everything, just take the first non-empty line
    if not clean_lines:
        for line in lines:
            if line.strip():
                return line.strip()
        return text
    
    return '\n'.join(clean_lines).strip()


async def call_llm(messages, config=None):
    """
    Call an OpenAI-compatible LLM API.
    
    Args:
        messages: List of message dicts [{"role": "system"/"user", "content": "..."}]
        config: LLM config dict (from get_llm_config)
    
    Returns:
        The assistant's response text, or raises an exception.
    """
    if config is None:
        config = get_llm_config()
    
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
    
    # Extract the assistant message
    choices = data.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "").strip()
    
    raise ValueError("No response from LLM")


async def retranslate(original_text, all_rows=None, target_index=0, config=None):
    """
    Retranslate Japanese text to Indonesian using LLM.
    
    Args:
        original_text: Japanese text to translate
        all_rows: All rows for context (list of dicts)
        target_index: Index of current row
        config: LLM config dict
    
    Returns:
        Translated text string
    """
    if config is None:
        config = get_llm_config()
    
    system_prompt = config["retranslate_prompt"]
    
    # Add glossary
    glossary_text = format_glossary(config["glossary"])
    if glossary_text:
        system_prompt += "\n\n" + glossary_text
    
    # Build user message with context
    user_parts = []
    
    # Include system instructions in user message (some proxies drop system role)
    user_parts.append(system_prompt)
    user_parts.append("")  # blank line separator
    
    if all_rows:
        context = build_context_block(all_rows, target_index, config["context_window"])
        if context:
            user_parts.append(context)
    
    user_parts.append(f"Translate this text:\n{original_text}")
    user_parts.append('\nIMPORTANT: Respond ONLY with JSON: {"translation": "your text"}')
    
    messages = [
        {"role": "user", "content": "\n".join(user_parts)},
    ]
    
    raw = await call_llm(messages, config)
    return extract_translation(raw)


async def polish(original_text, translated_text, all_rows=None, target_index=0, config=None):
    """
    Polish/improve an existing translation using LLM.
    
    Args:
        original_text: Original Japanese text
        translated_text: Existing translation to improve
        all_rows: All rows for context
        target_index: Index of current row
        config: LLM config dict
    
    Returns:
        Improved translation text string
    """
    if config is None:
        config = get_llm_config()
    
    system_prompt = config["polish_prompt"]
    
    # Add glossary
    glossary_text = format_glossary(config["glossary"])
    if glossary_text:
        system_prompt += "\n\n" + glossary_text
    
    # Build user message with context
    user_parts = []
    
    # Include system instructions in user message (some proxies drop system role)
    user_parts.append(system_prompt)
    user_parts.append("")  # blank line separator
    
    if all_rows:
        context = build_context_block(all_rows, target_index, config["context_window"])
        if context:
            user_parts.append(context)
    
    user_parts.append(f"Original Japanese:\n{original_text}\n\nCurrent translation:\n{translated_text}\n\nProvide the improved translation:")
    user_parts.append('\nIMPORTANT: Respond ONLY with JSON: {"translation": "your text"}')
    
    messages = [
        {"role": "user", "content": "\n".join(user_parts)},
    ]
    
    raw = await call_llm(messages, config)
    return extract_translation(raw)


async def test_connection(api_url_override=None, model_override=None):
    """
    Test the LLM connection by listing models or sending a small request.
    Returns dict with status info.
    """
    config = get_llm_config()
    api_url = (api_url_override or config["api_url"]).rstrip("/")
    model = model_override or config["model"]
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try /models endpoint first
            try:
                res = await client.get(f"{api_url}/models")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("id", "unknown") for m in data.get("data", [])]
                    return {
                        "status": "connected",
                        "api_url": api_url,
                        "models": models[:10],  # Limit to 10
                        "model_configured": model,
                    }
            except Exception:
                pass
            
            # Fallback: send a tiny chat request
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }
            res = await client.post(f"{api_url}/chat/completions", json=payload)
            res.raise_for_status()
            return {
                "status": "connected",
                "api_url": api_url,
                "models": [model],
                "model_configured": model,
            }
    
    except httpx.ConnectError:
        return {"status": "error", "message": f"Cannot connect to {api_url}. Is the LLM server running?"}
    except httpx.TimeoutException:
        return {"status": "error", "message": f"Connection to {api_url} timed out."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
