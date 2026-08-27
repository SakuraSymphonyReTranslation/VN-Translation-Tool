import json
import os
import shutil
import re
from . import config_manager, excel_manager, furigana_service

def _looks_like_romaji(text):
    """
    Determine if a text string looks like romaji that should be converted to kana for search.
    Returns True if the text appears to be romaji (Latin letters, numbers, and common separators).
    """
    if not text:
        return False
    
    has_latin_chars = bool(re.search(r'[a-zA-Z]', text))
    has_japanese_chars = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
    
    if has_latin_chars and not has_japanese_chars:
        return True
    
    latin_ratio = len(re.findall(r'[a-zA-Z]', text)) / len(text) if text else 0
    if latin_ratio > 0.6 and not has_japanese_chars:
        return True
        
    return False

def ensure_json_extension(filename):
    if not filename.endswith('.json'):
        return filename + '.json'
    return filename

# Known speaker names to wrap in brackets
SPEAKER_NAMES = ["一登", "ちよ子", "詩名", "未羽", "諳子有里栖", "ひより", "二乃", "叶方", "杉並", "有里咲"]
TRANSLATION_EXPORT_PRIORITY = ("polished", "best", "better", "initial", "machine")

def _message_from_game_item(item):
    if isinstance(item, dict):
        value = item.get("message", "")
        return value if isinstance(value, str) else str(value)
    return item if isinstance(item, str) else str(item)

def _sync_external_game_edits(project_data, trans_path):
    """Merge direct edits from the game JSON into the matching project column."""
    if not os.path.exists(trans_path):
        return 0

    try:
        with open(trans_path, 'r', encoding='utf-8-sig') as f:
            translated_data = json.load(f)
    except Exception as e:
        print(f"Error reading translated file for sync {trans_path}: {e}")
        return 0

    changed = 0
    for index, item in enumerate(project_data):
        if index >= len(translated_data) or not isinstance(item, dict):
            break

        translations = item.setdefault('translations', {})
        active_key = next(
            (key for key in TRANSLATION_EXPORT_PRIORITY if translations.get(key)),
            'initial',
        )
        current_text = translations.get(active_key, '')
        external_text = _message_from_game_item(translated_data[index])

        if external_text != current_text:
            translations[active_key] = external_text
            changed += 1

    return changed

def _auto_heal_original_raw_text(project_data, orig_path):
    """If project_data has empty original text but orig_path exists, heal it automatically."""
    if not os.path.exists(orig_path):
        return 0

    try:
        with open(orig_path, 'r', encoding='utf-8-sig') as f:
            original_data = json.load(f)
    except Exception as e:
        print(f"Error reading orig file for auto-heal {orig_path}: {e}")
        return 0

    healed = 0
    for index, item in enumerate(project_data):
        if index >= len(original_data) or not isinstance(item, dict):
            break

        current_orig = item.get('original', '')
        if not current_orig:
            raw_orig = _message_from_game_item(original_data[index])
            if raw_orig:
                item['original'] = raw_orig
                item['reading'] = furigana_service.get_reading(raw_orig)
                healed += 1

    return healed

def process_imported_text(text):
    if text in SPEAKER_NAMES:
        return f"「{text}」"
    return text

def load_project_data(filename):
    """
    Loads project data if exists, otherwise creates initial structure from game files.
    Returns: List of dicts { "id": int, "original": str, "translations": { "initial": "...", ... } }
    """
    filename = ensure_json_extension(filename)
    
    project_dir = config_manager.get_path("project_data_dir")
    original_dir = config_manager.get_path("original_dir")
    translated_dir = config_manager.get_path("translated_dir")
    
    # Ensure project_dir exists
    if project_dir:
        os.makedirs(project_dir, exist_ok=True)
        
    project_path = os.path.join(project_dir, filename) if project_dir else ""
    orig_path = os.path.join(original_dir, filename) if original_dir else ""
    trans_path = os.path.join(translated_dir, filename) if translated_dir else ""
    
    # Try loading existing project data
    if project_path and os.path.exists(project_path):
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                modified = False
                
                # 1. Auto-heal original text if missing
                healed_orig = _auto_heal_original_raw_text(data, orig_path)
                if healed_orig:
                    print(f"Auto-healed {healed_orig} original Japanese texts from {orig_path}")
                    modified = True
                
                # 2. Ensure reading field exists (backfill for Kanji search)
                for item in data:
                    if 'reading' not in item and 'original' in item and item['original']:
                        item['reading'] = furigana_service.get_reading(item['original'])
                        modified = True

                # 3. Sync external game edits
                external_changes = _sync_external_game_edits(data, trans_path)
                if external_changes:
                    print(f"Imported {external_changes} external game JSON edits into {project_path}")
                    modified = True

                if modified:
                    with open(project_path, 'w', encoding='utf-8') as project_file:
                        json.dump(data, project_file, indent=4, ensure_ascii=False)
                return data
        except Exception as e:
            print(f"Error reading project data {project_path}: {e}")
            
    # If no project data, load from game files
    original_data = []
    translated_data = []
    
    if orig_path and os.path.exists(orig_path):
        try:
            with open(orig_path, 'r', encoding='utf-8-sig') as f:
                original_data = json.load(f)
        except Exception as e:
            print(f"Error reading original file {orig_path}: {e}")
            
    if trans_path and os.path.exists(trans_path):
        try:
            with open(trans_path, 'r', encoding='utf-8-sig') as f:
                translated_data = json.load(f)
        except Exception as e:
            print(f"Error reading translated file {trans_path}: {e}")
            
    # Merge into rich structure
    merged = []
    max_len = max(len(original_data), len(translated_data))
    
    for i in range(max_len):
        orig_text = ""
        trans_text = ""
        
        if i < len(original_data):
            item = original_data[i]
            if isinstance(item, dict):
                orig_text = item.get('message', '')
            else:
                orig_text = str(item)
                
        if i < len(translated_data):
            item = translated_data[i]
            if isinstance(item, dict):
                trans_text = item.get('message', '')
            else:
                trans_text = str(item)
        
        merged.append({
            "id": i,
            "original": orig_text,
            "reading": furigana_service.get_reading(orig_text) if orig_text else "",
            "translations": {
                "initial": trans_text,
                "machine": "",
                "better": "",
                "best": "",
                "polished": ""
            }
        })
        
    # Auto save initial rich project data if we merged files
    if merged and project_path:
        try:
            with open(project_path, 'w', encoding='utf-8') as project_file:
                json.dump(merged, project_file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Could not auto-cache project data: {e}")
            
    return merged

def save_project_data(filename, data):
    """
    Saves the rich project data and updates the game file with the 'best' (or fallback) translation.
    """
    filename = ensure_json_extension(filename)
    
    project_dir = config_manager.get_path("project_data_dir")
    translated_dir = config_manager.get_path("translated_dir")
    
    if project_dir:
        os.makedirs(project_dir, exist_ok=True)
        project_path = os.path.join(project_dir, filename)
        try:
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving project data {project_path}: {e}")
            return False
            
    # 2. Save Game File (Export)
    if translated_dir and os.path.exists(translated_dir):
        trans_path = os.path.join(translated_dir, filename)
        output_data = []
        for item in data:
            translations = item.get('translations', {})
            text = next(
                (translations.get(key, '') for key in TRANSLATION_EXPORT_PRIORITY if translations.get(key)),
                '',
            )
            output_data.append({"message": text})
            
        try:
            with open(trans_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving game file {trans_path}: {e}")
            return False
            
    return True

def search_project_data(query: str, is_regex: bool = False, search_in_keys: list = None, scenario_modes: list = None, first_match_only: bool = False, match_case: bool = False, search_romaji: bool = False):
    import re
    
    project_dir = config_manager.get_path("project_data_dir")
    original_dir = config_manager.get_path("original_dir")
    translated_dir = config_manager.get_path("translated_dir")
    
    results = []
    
    project_files = set()
    if project_dir and os.path.exists(project_dir):
        project_files = {f for f in os.listdir(project_dir) if f.endswith(".json")}
        
    original_files = set()
    if original_dir and os.path.exists(original_dir):
        original_files = {f for f in os.listdir(original_dir) if f.endswith(".json")}
    
    translated_files = set()
    if translated_dir and os.path.exists(translated_dir):
        translated_files = {f for f in os.listdir(translated_dir) if f.endswith(".json")}

    all_files = project_files.union(original_files).union(translated_files)
    
    if scenario_modes:
        allowed_files = excel_manager.get_files_by_modes(scenario_modes)
        if allowed_files:
            allowed_json_files = {f if f.endswith('.json') else f + '.json' for f in allowed_files}
            all_files = all_files.intersection(allowed_json_files)

    try:
        if is_regex:
            flags = 0 if match_case else re.IGNORECASE
            pattern = re.compile(query, flags)
        else:
            if match_case:
                query_compare = query
            else:
                query_lower = query.lower()

            query_kana = ""
            query_kata = ""
            if search_romaji and _looks_like_romaji(query):
                try:
                    converted = furigana_service.romaji_to_kana(query)
                    if converted and converted != query.lower():
                        query_kana = converted
                        query_kata = furigana_service._hira_to_kata(converted)
                except Exception:
                    pass

        for filename in sorted(all_files):
            is_project_data = filename in project_files
            is_translated_file = filename in translated_files and not is_project_data
            
            filepath = ""
            if is_project_data:
                filepath = os.path.join(project_dir, filename)
            elif is_translated_file:
                filepath = os.path.join(translated_dir, filename)
            else:
                filepath = os.path.join(original_dir, filename)

            try:
                encoding = 'utf-8'
                if not is_project_data and not is_translated_file:
                    encoding = 'utf-8-sig'
                
                with open(filepath, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    
                if is_project_data:
                    for item in data:
                        row_id = item.get('id')
                        original = item.get('original', '')
                        translations = item.get('translations', {})
                        
                        if search_in_keys is None or "Original" in search_in_keys:
                            match_found = False
                            matched_text = ""
                            
                            if is_regex:
                                if pattern.search(original):
                                    match_found = True
                                    matched_text = original
                            else:
                                if match_case:
                                    if query_compare in original:
                                        match_found = True
                                        matched_text = original
                                else:
                                    original_lower = original.lower()
                                    if query_lower in original_lower:
                                        match_found = True
                                        matched_text = original
                                    elif query_kana and query_kana in original:
                                        match_found = True
                                        matched_text = original
                                    elif query_kana and query_kana in furigana_service.get_reading(original):
                                        match_found = True
                                        matched_text = original
                                    elif query_kata and query_kata in original:
                                        match_found = True
                                        matched_text = original
                            
                            if match_found:
                                results.append({
                                    "file": filename.replace(".json", ""),
                                    "id": row_id,
                                    "key": "Original",
                                    "text": matched_text
                                })

                        for key, text in translations.items():
                            if not text: continue
                            if search_in_keys is not None and key not in search_in_keys:
                                continue
                            
                            match_found = False
                            if is_regex:
                                if pattern.search(text):
                                    match_found = True
                            else:
                                if match_case:
                                    if query_compare in text:
                                        match_found = True
                                else:
                                    text_lower = text.lower()
                                    if query_lower in text_lower:
                                        match_found = True
                                    elif query_kana and query_kana in text:
                                        match_found = True
                                    elif query_kata and query_kata in text:
                                        match_found = True
                            
                            if match_found:
                                results.append({
                                    "file": filename.replace(".json", ""),
                                    "id": row_id,
                                    "key": key,
                                    "text": text
                                })
                else:
                    target_key = "Original" if not is_translated_file else "initial"

                    if search_in_keys is None or target_key in search_in_keys:
                        for i, item in enumerate(data):
                            text = item.get('message', '') if isinstance(item, dict) else str(item)
                                
                            match_found = False
                            if is_regex:
                                if pattern.search(text):
                                    match_found = True
                            else:
                                if match_case:
                                    if query_compare in text:
                                        match_found = True
                                else:
                                    text_lower = text.lower()
                                    if query_lower in text_lower:
                                        match_found = True
                                    elif query_kana and query_kana in text:
                                        match_found = True
                                    elif query_kana and query_kana in furigana_service.get_reading(text):
                                        match_found = True
                                    elif query_kata and query_kata in text:
                                        match_found = True
                                    
                            if match_found:
                                results.append({
                                    "file": filename.replace(".json", ""),
                                    "id": i,
                                    "key": target_key, 
                                    "text": text
                                })

            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Search error: {e}")
    
    if first_match_only and results:
        seen_files = set()
        filtered_results = []
        for result in results:
            if result["file"] not in seen_files:
                seen_files.add(result["file"])
                filtered_results.append(result)
        return filtered_results
        
    return results

def _apply_preserve_case(original_match: str, replacement: str) -> str:
    if original_match.isupper():
        return replacement.upper()
    elif original_match.islower():
        return replacement.lower()
    elif original_match and original_match[0].isupper() and original_match[1:].islower():
        return replacement.capitalize()
    return replacement

def replace_in_project_data(query: str, replacement: str, is_regex: bool = False, 
                            match_case: bool = False, preserve_case: bool = False,
                            search_in_keys: list = None, scenario_modes: list = None, search_romaji: bool = False):
    import re
    
    project_dir = config_manager.get_path("project_data_dir")
    translated_dir = config_manager.get_path("translated_dir")
    
    if not project_dir or not os.path.exists(project_dir):
        return {"replaced_count": 0, "file_count": 0}
    
    project_files = [f for f in os.listdir(project_dir) if f.endswith(".json")]
    
    if scenario_modes:
        allowed_files = excel_manager.get_files_by_modes(scenario_modes)
        if allowed_files:
            allowed_json_files = {f if f.endswith('.json') else f + '.json' for f in allowed_files}
            project_files = [f for f in project_files if f in allowed_json_files]
    
    if is_regex:
        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(query, flags)
    
    total_replaced = 0
    files_modified = 0
    
    for filename in sorted(project_files):
        filepath = os.path.join(project_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_changed = False
            
            for item in data:
                translations = item.get('translations', {})
                
                for key, text in translations.items():
                    if not text:
                        continue
                    
                    query_kana = ""
                    query_kata = ""
                    if search_romaji and _looks_like_romaji(query):
                        try:
                            converted = furigana_service.romaji_to_kana(query)
                            if converted and converted != query.lower():
                                query_kana = converted
                                query_kata = furigana_service._hira_to_kata(converted)
                        except Exception:
                            pass

                    new_text = text
                    if is_regex:
                        if preserve_case:
                            def _repl(m):
                                return _apply_preserve_case(m.group(0), replacement)
                            new_text = pattern.sub(_repl, text)
                        else:
                            new_text = pattern.sub(replacement, text)
                    else:
                        match_found = False
                        if match_case:
                            if query in text:
                                match_found = True
                        else:
                            if query.lower() in text.lower():
                                match_found = True
                            elif query_kana and query_kana in text:
                                match_found = True
                            elif query_kata and query_kata in text:
                                match_found = True
                        
                        if match_found:
                            if match_case:
                                if preserve_case:
                                    result = []
                                    idx = 0
                                    while idx < len(text):
                                        pos = text.find(query, idx)
                                        if pos == -1:
                                            result.append(text[idx:])
                                            break
                                        result.append(text[idx:pos])
                                        result.append(_apply_preserve_case(text[pos:pos+len(query)], replacement))
                                        idx = pos + len(query)
                                    new_text = ''.join(result)
                                else:
                                    new_text = text.replace(query, replacement)
                            else:
                                ci_pattern = re.compile(re.escape(query), re.IGNORECASE)
                                if preserve_case:
                                    def _repl_ci(m):
                                        return _apply_preserve_case(m.group(0), replacement)
                                    new_text = ci_pattern.sub(_repl_ci, text)
                                else:
                                    new_text = ci_pattern.sub(replacement, text)
                    
                    if new_text != text:
                        translations[key] = new_text
                        total_replaced += text.count(query) if (match_case and not is_regex) else (len(new_text) != len(text) and 1 or 1)
                        file_changed = True
                
                item['translations'] = translations
            
            if file_changed:
                files_modified += 1
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                if translated_dir and os.path.exists(translated_dir):
                    trans_path = os.path.join(translated_dir, filename)
                    output_data = []
                    for item in data:
                        translations = item.get('translations', {})
                        text = next(
                            (translations.get(k, '') for k in TRANSLATION_EXPORT_PRIORITY if translations.get(k)),
                            '',
                        )
                        output_data.append({"message": text})
                    try:
                        with open(trans_path, 'w', encoding='utf-8') as f:
                            json.dump(output_data, f, indent=4, ensure_ascii=False)
                    except Exception as e:
                        print(f"Error updating game file {trans_path}: {e}")
                        
        except Exception as e:
            print(f"Error replacing in file {filename}: {e}")
            continue
    
    return {"replaced_count": total_replaced, "file_count": files_modified}

def save_as(current_filename, new_filename, data):
    new_filename = ensure_json_extension(new_filename)
    return save_project_data(new_filename, data)

def scan_for_modified_files(columns: list = None):
    if columns is None:
        columns = ['better', 'best']
        
    project_dir = config_manager.get_path("project_data_dir")
    modified_files = []
    
    if not project_dir or not os.path.exists(project_dir):
        return modified_files
        
    for filename in os.listdir(project_dir):
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(project_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            has_changes = False
            for item in data:
                translations = item.get('translations', {})
                for col in columns:
                    if translations.get(col):
                        has_changes = True
                        break
                if has_changes:
                    break
            
            if has_changes:
                modified_files.append(filename.replace(".json", ""))
                
        except Exception as e:
            print(f"Error scanning {filename}: {e}")
            
    return modified_files
