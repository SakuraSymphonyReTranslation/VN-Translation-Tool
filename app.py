from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional

import os
from services import excel_manager, file_manager, config_manager, furigana_service, llm_service, webai_service

app = FastAPI(title="DC4 Translation Tool")

@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Mount static files
static_dir = os.path.join(config_manager.RESOURCE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount wallpaper directory
wallpaper_dir = os.path.join(config_manager.BASE_DIR, "wallpaper")
os.makedirs(wallpaper_dir, exist_ok=True)
app.mount("/wallpaper", StaticFiles(directory=wallpaper_dir), name="wallpaper")

class TranslationItem(BaseModel):
    id: int
    original: str
    translations: Dict[str, str]

class SaveRequest(BaseModel):
    items: List[TranslationItem]

@app.get("/")
async def index():
    index_path = os.path.join(config_manager.RESOURCE_DIR, "templates/index.html")
    return FileResponse(index_path)

@app.get("/api/scenarios")
async def get_scenarios():
    data = excel_manager.load_scenario_structure()
    return data

@app.get("/api/wallpapers")
async def get_wallpapers():
    """List available wallpaper images."""
    valid_ext = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.mp4', '.webm', '.mkv', '.mpg'}
    files = []
    if os.path.isdir(wallpaper_dir):
        for f in sorted(os.listdir(wallpaper_dir)):
            if os.path.splitext(f)[1].lower() in valid_ext:
                files.append(f)
    return {"wallpapers": files}

@app.get("/api/translation/{filename}")
async def get_translation(filename: str):
    data = file_manager.load_project_data(filename)
    return data

@app.post("/api/translation/{filename}")
async def save_translation(filename: str, request: SaveRequest):
    # Convert Pydantic models to dicts
    data = [item.dict() for item in request.items]
    success = file_manager.save_project_data(filename, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save translation")
    return {"status": "success"}

@app.post("/api/save_as")
async def save_as_translation(payload: dict = Body(...)):
    current_filename = payload.get("current_filename")
    new_filename = payload.get("new_filename")
    items = payload.get("items")
    
    if not current_filename or not new_filename or not items:
         raise HTTPException(status_code=400, detail="Missing required fields")
         
    success = file_manager.save_as(current_filename, new_filename, items)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save as")
    return {"status": "success"}

class BulkSaveRequest(BaseModel):
    files: List[str]
    suffix: str

@app.get("/api/bulk/scan")
async def scan_modified_files():
    # Detect files with 'better' or 'best' translations
    files = file_manager.scan_for_modified_files(['better', 'best'])
    return {"files": files}

@app.post("/api/bulk/save_as")
async def bulk_save_as(request: BulkSaveRequest):
    success_count = 0
    errors = []
    
    for filename in request.files:
        try:
            # Load current data
            data = file_manager.load_project_data(filename)
            # Create new filename
            new_filename = f"{filename}{request.suffix}"
            # Save as copy
            if file_manager.save_as(filename, new_filename, data):
                 success_count += 1
            else:
                 errors.append(filename)
        except Exception as e:
            errors.append(f"{filename} ({str(e)})")
            
    return {"status": "success", "processed": success_count, "errors": errors}

    return {"status": "success"}

class SearchRequest(BaseModel):
    query: str
    is_regex: bool = False
    search_in_initial_only: bool = False
    scenario_modes: Optional[List[str]] = None
    first_match_only: bool = False
    match_case: bool = False
    search_romaji: bool = False


class ReplaceRequest(BaseModel):
    query: str
    replacement: str
    is_regex: bool = False
    match_case: bool = False
    preserve_case: bool = False
    search_in_initial_only: bool = False
    scenario_modes: Optional[List[str]] = None
    search_romaji: bool = False

@app.get("/api/scenario-modes")
async def get_scenario_modes():
    modes = excel_manager.get_all_scenario_modes()
    return {"modes": modes}

@app.post("/api/search")
async def search_scenarios(request: SearchRequest):
    # Map search_in_initial_only to search_in_keys parameter
    search_in_keys = ["initial"] if request.search_in_initial_only else None
    results = file_manager.search_project_data(
        request.query, 
        request.is_regex, 
        search_in_keys,
        request.scenario_modes,
        request.first_match_only,
        request.match_case,
        request.search_romaji
    )
    return {"results": results, "count": len(results)}

@app.post("/api/replace")
async def replace_in_scenarios(request: ReplaceRequest):
    search_in_keys = ["initial"] if request.search_in_initial_only else None
    result = file_manager.replace_in_project_data(
        query=request.query,
        replacement=request.replacement,
        is_regex=request.is_regex,
        match_case=request.match_case,
        preserve_case=request.preserve_case,
        search_in_keys=search_in_keys,
        scenario_modes=request.scenario_modes,
        search_romaji=request.search_romaji
    )
    return {"status": "success", **result}

class FuriganaRequest(BaseModel):
    texts: List[str]
    mode: str = 'hiragana'  # hiragana, katakana, romaji

@app.post("/api/furigana")
async def get_furigana(request: FuriganaRequest):
    results = []
    for text in request.texts:
        html = furigana_service.get_furigana_html(text, mode=request.mode)
        results.append(html)
    return {"results": results}

@app.get("/api/furigana/status")
async def furigana_status():
    return furigana_service.get_tagger_status()

@app.get("/api/furigana/debug")
async def furigana_debug():
    """Debug endpoint to inspect MeCab feature format."""
    return furigana_service.debug_features("今日は良い天気です。")


# ─── Project Management Endpoints ─────────────────────────────────────────────

@app.get("/api/project-data-folders")
async def get_project_data_folders():
    return config_manager.get_available_cache_folders()

@app.get("/api/projects")
async def get_projects():
    cfg = config_manager.load_config()
    active_id = cfg.get("active_project", "dc4_plus_harmony")
    projects_dict = cfg.get("projects", {})
    proj_list = []
    for pid, pdata in projects_dict.items():
        proj_list.append({
            "id": pid,
            "identifier": pdata.get("identifier", pid),
            "name": pdata.get("name", pid.replace("_", " ").title()),
            "original_dir": pdata.get("original_dir", ""),
            "translated_dir": pdata.get("translated_dir", ""),
            "excel_path": pdata.get("excel_path", ""),
            "project_data_dir": pdata.get("project_data_dir", ""),
            "is_active": (pid == active_id)
        })
    return {"active_project": active_id, "projects": proj_list}

@app.post("/api/projects/switch")
async def switch_project(payload: dict = Body(...)):
    pid = payload.get("project_id")
    if not pid:
        raise HTTPException(status_code=400, detail="Missing project_id")
    new_cfg = config_manager.switch_project(pid)
    furigana_service.reset_tagger()
    return {"status": "success", "config": new_cfg}

@app.post("/api/projects/save")
async def save_project(payload: dict = Body(...)):
    pid = payload.get("project_id") or payload.get("identifier")
    if not pid:
        raise HTTPException(status_code=400, detail="Missing project identifier")
    success = config_manager.save_project_profile(pid, payload)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to save project profile")

@app.post("/api/projects/delete")
async def delete_project(payload: dict = Body(...)):
    pid = payload.get("project_id")
    if not pid:
        raise HTTPException(status_code=400, detail="Missing project_id")
    success = config_manager.delete_project_profile(pid)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Failed to delete project profile")

@app.get("/api/config")
async def get_config():
    return config_manager.load_config()

@app.post("/api/config")
async def update_config(request: Request):
    try:
        config_data = await request.json()
        success = config_manager.save_config(config_data)
        if success:
            # Reset furigana tagger in case unidic_dir changed
            furigana_service.reset_tagger()
            return {"status": "success"}
        else:
            return {"status": "error", "message": "Failed to save config"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── WebAI-to-API Management Endpoints ──────────────────────────────────────────

@app.get("/api/llm/webai/status")
async def get_webai_status():
    return {
        "status": "success",
        "folder": webai_service.get_webai_dir(),
        "folder_exists": os.path.exists(webai_service.get_webai_dir()),
        "local_version": webai_service.get_local_version(),
        "repo": webai_service.GITHUB_REPO
    }

@app.get("/api/llm/webai/check-update")
async def check_webai_update():
    return webai_service.check_for_update()

@app.post("/api/llm/webai/update")
async def update_webai():
    return webai_service.perform_update()

@app.get("/api/llm/webai/cookies")
async def get_webai_cookies():
    return webai_service.get_gemini_cookies()

@app.post("/api/llm/webai/cookies")
async def save_webai_cookies(payload: dict = Body(...)):
    psid = payload.get("psid", "")
    psidts = payload.get("psidts", "")
    browser = payload.get("browser", "chrome")
    return webai_service.save_gemini_cookies(psid, psidts, browser)

@app.post("/api/llm/webai/extract-cookies")
async def extract_webai_cookies(payload: dict = Body(...)):
    browser = payload.get("browser", "chrome")
    return webai_service.extract_cookies_from_browser(browser)

@app.post("/api/llm/webai/launch-login")
async def launch_webai_login():
    return webai_service.launch_verify_login()

# ─── LLM Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/llm/summary")
async def get_story_summary():
    return {"summary": llm_service.get_story_summary()}

@app.post("/api/llm/summary/clear")
async def clear_story_summary():
    return llm_service.clear_story_summary()

@app.post("/api/llm/summary/save")
async def save_story_summary(payload: dict = Body(...)):
    summary = payload.get("summary", "")
    llm_service.update_story_summary(summary)
    return {"status": "success", "message": "Story summary updated."}


@app.get("/api/llm/models")
async def get_available_llm_models():
    return await llm_service.test_connection()

import json as json_module

class LLMSingleRequest(BaseModel):
    original: str
    translation: str = ""
    all_rows: Optional[List[dict]] = None
    target_index: int = 0

class LLMBatchRequest(BaseModel):
    mode: str  # "retranslate" or "polish"
    source_tab: str = "initial"
    items: List[dict]  # [{id, original, translation}]

@app.post("/api/llm/retranslate")
async def llm_retranslate(request: LLMSingleRequest):
    """Retranslate a single row using LLM."""
    try:
        config = llm_service.get_llm_config()
        result = await llm_service.retranslate(
            original_text=request.original,
            all_rows=request.all_rows,
            target_index=request.target_index,
            config=config
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/llm/polish")
async def llm_polish(request: LLMSingleRequest):
    """Polish a single row using LLM."""
    try:
        config = llm_service.get_llm_config()
        result = await llm_service.polish(
            original_text=request.original,
            translated_text=request.translation,
            all_rows=request.all_rows,
            target_index=request.target_index,
            config=config
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/llm/batch")
async def llm_batch(request: LLMBatchRequest):
    """Batch retranslate/polish with SSE streaming for progress."""

    async def event_stream():
        config = llm_service.get_llm_config()
        total = len(request.items)
        all_context_rows = request.full_rows if request.full_rows else request.items

        for idx, item in enumerate(request.items):
            try:
                original = item.get("original", "")
                translation = item.get("translation", "")
                row_id = item.get("id", idx)
                
                # Context target index in the full scenario
                full_index = request.start_offset + idx if request.full_rows else idx

                if request.mode == "retranslate":
                    result = await llm_service.retranslate(
                        original_text=original,
                        all_rows=all_context_rows,
                        target_index=full_index,
                        config=config
                    )
                else:  # polish
                    result = await llm_service.polish(
                        original_text=original,
                        translated_text=translation,
                        all_rows=all_context_rows,
                        target_index=full_index,
                        config=config
                    )

                event_data = json_module.dumps({
                    "type": "progress",
                    "id": row_id,
                    "index": idx,
                    "total": total,
                    "result": result
                })
                yield f"data: {event_data}\n\n"

            except Exception as e:
                event_data = json_module.dumps({
                    "type": "error",
                    "id": item.get("id", idx),
                    "index": idx,
                    "total": total,
                    "message": str(e)
                })
                yield f"data: {event_data}\n\n"

        # Done event
        yield f"data: {json_module.dumps({'type': 'done', 'total': total})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

def is_japanese(text: str) -> bool:
    return bool(re.search(r'[぀-ヿ㐀-䶿一-鿿]', text or ''))

@app.post("/api/glossary/extract-vndb")
async def extract_vndb_glossary(request: Request):
    """Extract character glossary from VNDB Kana API."""
    import httpx
    body = await request.json()
    raw_vn_id = body.get("vn_id", "").strip()
    
    if not raw_vn_id:
        return {"status": "error", "message": "VNDB ID tidak boleh kosong (contoh: v22741 atau 22741)."}
        
    m = re.search(r'v?(\d+)', raw_vn_id.lower())
    if not m:
        return {"status": "error", "message": f"Format VNDB ID tidak valid: '{raw_vn_id}'. Gunakan format seperti v22741."}
    clean_vn_id = "v" + m.group(1)

    url = "https://api.vndb.org/kana/character"
    headers = {
        "User-Agent": "VNTranslationTool/3.7.0 (https://github.com/SakuraSymphonyReTranslation)",
        "Content-Type": "application/json"
    }
    query = {
        "filters": ["vn", "=", ["id", "=", clean_vn_id]],
        "fields": "name, original, gender, aliases",
        "results": 100
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=query, headers=headers)
            if resp.status_code != 200:
                return {"status": "error", "message": f"VNDB API error ({resp.status_code}): {resp.text}"}
            data = resp.json()
            characters = data.get("results", [])
            
            # If 0 characters, check if it's a release or needs relations
            if not characters:
                # Try querying VN info to check title
                vn_resp = await client.post("https://api.vndb.org/kana/vn", json={"filters": ["id", "=", clean_vn_id], "fields": "title, relations.id, relations.relation_official"}, headers=headers)
                if vn_resp.status_code == 200:
                    vn_data = vn_resp.json().get("results", [])
                    if vn_data:
                        relations = vn_data[0].get("relations", [])
                        # Try parent or original game relations
                        for rel in relations:
                            rel_id = rel.get("id")
                            if rel_id:
                                rel_query = {"filters": ["vn", "=", ["id", "=", rel_id]], "fields": "name, original, gender, aliases", "results": 100}
                                rel_resp = await client.post(url, json=rel_query, headers=headers)
                                if rel_resp.status_code == 200:
                                    rel_chars = rel_resp.json().get("results", [])
                                    if rel_chars:
                                        characters = rel_chars
                                        break
    except Exception as e:
        return {"status": "error", "message": f"Gagal menghubungi server VNDB: {str(e)}"}

    if not characters:
        return {"status": "warning", "count": 0, "entries": [], "message": f"Tidak ada karakter yang ditemukan untuk VNDB ID '{clean_vn_id}'. Pastikan ID benar."}

    glossary = []
    seen_src = set()
    gender_map = {"m": "male", "f": "female", "o": "both/other"}

    for char in characters:
        full_romaji = char.get('name', 'Unknown')
        full_kanji = char.get('original')

        gender_data = char.get('gender', 'unknown')
        gender_code = gender_data[0] if isinstance(gender_data, list) and gender_data else gender_data
        gender_text = gender_map.get(gender_code, "unknown")

        has_space_romaji = " " in full_romaji
        has_space_kanji = bool(full_kanji and " " in full_kanji)

        first_romaji = full_romaji.split(" ")[-1] if has_space_romaji else full_romaji
        first_kanji = full_kanji.split(" ")[-1] if has_space_kanji else full_kanji

        last_romaji = full_romaji.split(" ")[0] if has_space_romaji else None
        last_kanji = full_kanji.split(" ")[0] if has_space_kanji else None

        # 1. Full name
        if full_kanji and is_japanese(full_kanji) and full_kanji not in seen_src:
            glossary.append({
                "src": full_kanji,
                "dst": full_romaji,
                "info": f"{full_romaji} is {gender_text}",
                "case_sensitive": False
            })
            seen_src.add(full_kanji)

        # 2. First name
        if has_space_kanji and first_kanji and is_japanese(first_kanji) and first_kanji not in seen_src:
            glossary.append({
                "src": first_kanji,
                "dst": first_romaji,
                "info": f"{first_romaji} is {gender_text}",
                "case_sensitive": False
            })
            seen_src.add(first_kanji)

        # 3. Last name (marga)
        if last_kanji and is_japanese(last_kanji) and last_kanji not in seen_src:
            glossary.append({
                "src": last_kanji,
                "dst": last_romaji,
                "info": last_romaji,
                "case_sensitive": False
            })
            seen_src.add(last_kanji)

        # 4. Aliases
        aliases = char.get('aliases', [])
        jp_aliases = [a for a in aliases if is_japanese(a)]
        ro_aliases = [a for a in aliases if not is_japanese(a)]

        max_idx = max(len(jp_aliases), len(ro_aliases)) if (jp_aliases or ro_aliases) else 0
        for i in range(max_idx):
            try:
                src_val = jp_aliases[i]
                dst_val = ro_aliases[i] if i < len(ro_aliases) else first_romaji

                if src_val not in seen_src:
                    glossary.append({
                        "src": src_val,
                        "dst": dst_val,
                        "info": f"{dst_val} is {gender_text}",
                        "case_sensitive": False
                    })
                    seen_src.add(src_val)
            except IndexError:
                continue

    return {
        "status": "success",
        "vn_id": clean_vn_id,
        "characters_count": len(characters),
        "count": len(glossary),
        "entries": glossary,
        "message": f"Berhasil mengekstrak {len(glossary)} entri glosarium ({len(characters)} karakter) dari VNDB {clean_vn_id}!"
    }

@app.post("/api/llm/test")
async def llm_test_connection(request: Request):
    """Test LLM connection using values from frontend with strict cookie check."""
    body = await request.json()
    return await llm_service.test_connection(
        api_url_override=body.get("api_url"),
        model_override=body.get("model"),
        provider_override=body.get("provider"),
        psid_override=body.get("psid"),
        psidts_override=body.get("psidts"),
    )

if __name__ == "__main__":
    import uvicorn
    # Use port 8000 or configurable if needed
    uvicorn.run(app, host="127.0.0.1", port=8000)

