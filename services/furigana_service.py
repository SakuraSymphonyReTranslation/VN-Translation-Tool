"""
Furigana Service - Generates ruby annotations for Japanese text using MeCab + Unidic.
Supports three modes: hiragana, katakana, romaji.
"""
import re
import unicodedata
from . import config_manager

_tagger = None
_tagger_error = None

# Romaji conversion table (hiragana -> romaji)
_HIRA_TO_ROMAJI = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'ゐ': 'wi', 'ゑ': 'we', 'を': 'wo',
    'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
    'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
    'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
    'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
    'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
    'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
    'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
    'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo',
    'っ': '',  # handled specially
    'ー': '-',
}

# Invert table for Romaji -> Hiragana
_ROMAJI_TO_HIRA = {}
for k, v in _HIRA_TO_ROMAJI.items():
    if v:
        _ROMAJI_TO_HIRA[v] = k

# Sort keys by length descending to match longer romaji first (e.g. 'shi' before 'si')
_ROMAJI_KEYS = sorted(_ROMAJI_TO_HIRA.keys(), key=len, reverse=True)


def _is_kanji(char):
    """Check if a character is a CJK kanji."""
    return unicodedata.category(char).startswith('Lo') and '\u4e00' <= char <= '\u9fff'


def _has_kanji(text):
    """Check if text contains any kanji characters."""
    return any(_is_kanji(c) for c in text)


def _is_kana(char):
    """Check if a character is hiragana or katakana."""
    return ('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')


def _has_japanese(text):
    """Check if text contains any Japanese characters (kanji, hiragana, katakana)."""
    return any(_is_kanji(c) or _is_kana(c) for c in text)


def _kata_to_hira(text):
    """Convert katakana to hiragana."""
    result = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(ch)
    return ''.join(result)


def _hira_to_kata(text):
    """Convert hiragana to katakana."""
    result = []
    for ch in text:
        code = ord(ch)
        if 0x3041 <= code <= 0x3096:
            result.append(chr(code + 0x60))
        else:
            result.append(ch)
    return ''.join(result)


def _hira_to_romaji(text):
    """Convert hiragana string to romaji."""
    result = []
    i = 0
    while i < len(text):
        # Check for っ (double consonant)
        if text[i] == 'っ' and i + 1 < len(text):
            # Look ahead for the next kana's romaji
            if i + 2 < len(text) and (text[i+1:i+3] in _HIRA_TO_ROMAJI):
                next_romaji = _HIRA_TO_ROMAJI[text[i+1:i+3]]
                if next_romaji:
                    result.append(next_romaji[0])
                i += 1
                continue
            elif text[i+1] in _HIRA_TO_ROMAJI:
                next_romaji = _HIRA_TO_ROMAJI[text[i+1]]
                if next_romaji:
                    result.append(next_romaji[0])
                i += 1
                continue

        # Check two-char combinations first (e.g. きゃ)
        if i + 1 < len(text) and text[i:i+2] in _HIRA_TO_ROMAJI:
            result.append(_HIRA_TO_ROMAJI[text[i:i+2]])
            i += 2
            continue

        # Single character
        if text[i] in _HIRA_TO_ROMAJI:
            result.append(_HIRA_TO_ROMAJI[text[i]])
            i += 1
            continue

        # Pass through anything else
        result.append(text[i])
        i += 1

    return ''.join(result)


def romaji_to_kana(text):
    """
    Convert Romaji string to Hiragana.
    Useful for searching Japanese text using Romaji input.
    """
    if not text:
        return ""
    
    text = text.lower()
    result = []
    i = 0
    while i < len(text):
        # 1. Try to match from _ROMAJI_TO_HIRA (sorted by length)
        matched = False
        for romaji in _ROMAJI_KEYS:
            if text.startswith(romaji, i):
                result.append(_ROMAJI_TO_HIRA[romaji])
                i += len(romaji)
                matched = True
                break
        
        if matched:
            continue

        # 2. Check for double consonants (gemination) -> 'っ'
        # e.g. 'k' in 'kKA', 'p' in 'pPA'
        # But NOT 'n' (which might be 'n' or 'nn')
        if i + 1 < len(text) and text[i] == text[i+1] and text[i] not in 'aeioun':
            result.append('っ')
            i += 1
            continue
        
        # 3. Handle 'n' edge cases (n vs nn)
        if text[i] == 'n':
            result.append('ん')
            i += 1
            continue
            
        # 4. Pass through anything else
        result.append(text[i])
        i += 1
    
    return "".join(result)


def _get_tagger():
    """Lazily initialize the MeCab tagger with unidic."""
    global _tagger, _tagger_error

    if _tagger is not None:
        return _tagger
    if _tagger_error is not None:
        return None

    try:
        import fugashi
        import os

        config = config_manager.load_config()
        unidic_dir = config.get('unidic_dir', '').strip()

        # On Windows, MeCab looks for c:\mecab\mecabrc which may not exist.
        # Use '-r NUL' to skip the config file lookup.
        rcfile = 'NUL' if os.name == 'nt' else '/dev/null'

        if unidic_dir:
            _tagger = fugashi.GenericTagger(f'-r {rcfile} -d "{unidic_dir}"')
        else:
            try:
                import unidic
                dic_dir = unidic.DICDIR
                _tagger = fugashi.GenericTagger(f'-r {rcfile} -d "{dic_dir}"')
            except Exception:
                _tagger = fugashi.GenericTagger(f'-r {rcfile}')

        return _tagger
    except Exception as e:
        _tagger_error = str(e)
        print(f"[Furigana] Failed to initialize MeCab tagger: {e}")
        return None


def reset_tagger():
    """Reset the tagger so it reloads on next use (e.g. after config change)."""
    global _tagger, _tagger_error
    _tagger = None
    _tagger_error = None


def _get_reading(word):
    """Extract the reading from a MeCab word's features."""
    reading = None
    try:
        if hasattr(word, 'feature') and word.feature:
            features = word.feature
            # Handle tuple features (GenericTagger with UniDic)
            # UniDic feature layout: pos1,pos2,pos3,pos4,cType,cForm,kana,lemma,orth,pron,...
            if isinstance(features, tuple):
                # Index 6 = kana reading, index 9 = pronunciation
                for idx in (6, 9):
                    if idx < len(features):
                        val = features[idx]
                        if val and val != '*' and _is_all_kana(str(val)):
                            reading = str(val)
                            break
            elif hasattr(features, 'kana'):
                reading = features.kana
            elif hasattr(features, 'pron'):
                reading = features.pron
            elif isinstance(features, str):
                parts = features.split(',')
                # Try known UniDic positions first (6, 9)
                for idx in (6, 9):
                    if idx < len(parts):
                        val = parts[idx].strip()
                        if val and val != '*' and _is_all_kana(val):
                            reading = val
                            break
                # Fallback: scan all fields
                if not reading:
                    for i in range(len(parts) - 1, -1, -1):
                        val = parts[i].strip()
                        if val and val != '*' and _is_all_kana(val):
                            reading = val
                            break
    except Exception:
        pass
    return reading


def get_furigana_html(text, mode='hiragana'):
    """
    Convert Japanese text to HTML with <ruby> annotations.
    
    Modes:
      - 'hiragana': Show hiragana reading above kanji only
      - 'katakana': Show katakana reading above kanji only
      - 'romaji': Show romaji reading above all Japanese text (kanji, hiragana, katakana)
    """
    if not text:
        return ''

    # For hiragana/katakana modes, skip if no kanji
    if mode in ('hiragana', 'katakana') and not _has_kanji(text):
        return _escape_html(text)

    # For romaji mode, skip if no Japanese at all
    if mode == 'romaji' and not _has_japanese(text):
        return _escape_html(text)

    tagger = _get_tagger()
    if tagger is None:
        return _escape_html(text)

    try:
        words = tagger(text)
        html_parts = []

        for word in words:
            surface = word.surface

            if not surface.strip():
                html_parts.append(_escape_html(surface))
                continue

            reading = _get_reading(word)

            if mode == 'romaji':
                # Romaji mode: annotate ALL Japanese text
                if reading:
                    hira_reading = _kata_to_hira(reading)
                    romaji = _hira_to_romaji(hira_reading)
                elif _is_all_kana(surface):
                    # Surface itself is kana, convert directly
                    hira = _kata_to_hira(surface)
                    romaji = _hira_to_romaji(hira)
                else:
                    romaji = None

                if romaji and _has_japanese(surface):
                    html_parts.append(
                        f'<ruby>{_escape_html(surface)}<rt>{_escape_html(romaji)}</rt></ruby>'
                    )
                else:
                    html_parts.append(_escape_html(surface))

            elif mode == 'katakana':
                # Katakana mode: annotate kanji only with katakana reading
                if reading and _has_kanji(surface):
                    # Ensure reading is in katakana
                    kata_reading = _hira_to_kata(reading) if not any(0x30A1 <= ord(c) <= 0x30F6 for c in reading) else reading
                    if kata_reading != surface:
                        html_parts.append(
                            f'<ruby>{_escape_html(surface)}<rt>{_escape_html(kata_reading)}</rt></ruby>'
                        )
                    else:
                        html_parts.append(_escape_html(surface))
                else:
                    html_parts.append(_escape_html(surface))

            else:
                # Hiragana mode (default): annotate kanji only
                if reading and _has_kanji(surface):
                    hira_reading = _kata_to_hira(reading)
                    if hira_reading != surface:
                        html_parts.append(
                            f'<ruby>{_escape_html(surface)}<rt>{_escape_html(hira_reading)}</rt></ruby>'
                        )
                    else:
                        html_parts.append(_escape_html(surface))
                else:
                    html_parts.append(_escape_html(surface))

        return ''.join(html_parts)

    except Exception as e:
        print(f"[Furigana] Error processing text: {e}")
        return _escape_html(text)


def _is_all_kana(text):
    """Check if text is all hiragana or katakana."""
    for ch in text:
        if not ('\u3040' <= ch <= '\u309f' or '\u30a0' <= ch <= '\u30ff' or ch == 'ー'):
            return False
    return True


def _escape_html(text):
    """Escape HTML special characters, preserving newlines as <br>."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace('\n', '<br>')
    return text


def get_tagger_status():
    """Return the current tagger status for diagnostics."""
    global _tagger, _tagger_error
    if _tagger is not None:
        return {"status": "ready"}
    if _tagger_error is not None:
        return {"status": "error", "message": _tagger_error}
    return {"status": "not_initialized"}


def debug_features(text):
    """Debug: show raw feature data for each word in text."""
    tagger = _get_tagger()
    if tagger is None:
        return {"error": "Tagger not available", "tagger_error": _tagger_error}

    words = tagger(text)
    result = []
    for word in words:
        entry = {
            "surface": word.surface,
            "feature_type": type(word.feature).__name__,
            "feature_raw": str(word.feature),
            "has_kanji": _has_kanji(word.surface),
        }
        if isinstance(word.feature, str):
            parts = word.feature.split(',')
            entry["feature_parts"] = parts
            entry["feature_count"] = len(parts)
        else:
            # Named feature object
            entry["feature_attrs"] = [a for a in dir(word.feature) if not a.startswith('_')]
        result.append(entry)
    return {"words": result}


def get_reading(text):
    """
    Get the reading of the text in Hiragana.
    Useful for search matching (e.g. matching 'suki' to '好き').
    """
    if not text:
        return ""
        
    tagger = _get_tagger()
    if tagger is None:
        return text # Fallback to original if no tagger
        
    try:
        words = tagger(text)
        result = []
        for word in words:
            reading = _get_reading(word)
            if reading:
                # _get_reading usually returns Katakana (UniDic standard)
                # Convert to Hiragana for consistent search
                result.append(_kata_to_hira(reading))
            else:
                # Fallback to surface (e.g. for symbols or unknown words)
                # If surface is Kanji but no reading, it stays Kanji (unmatchable by kana)
                # But usually _get_reading handles it.
                # If surface is Kana, convert to Hiragana just in case
                result.append(_kata_to_hira(word.surface))
                
        return "".join(result)
    except Exception as e:
        print(f"[Furigana] Error getting reading: {e}")
        return text
