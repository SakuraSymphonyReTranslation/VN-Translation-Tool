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

# ─── LLM Endpoints ───────────────────────────────────────────────────────────

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

        for idx, item in enumerate(request.items):
            try:
                original = item.get("original", "")
                translation = item.get("translation", "")
                row_id = item.get("id", idx)

                # Build context from all items
                all_rows = request.items

                if request.mode == "retranslate":
                    result = await llm_service.retranslate(
                        original_text=original,
                        all_rows=all_rows,
                        target_index=idx,
                        config=config
                    )
                else:  # polish
                    result = await llm_service.polish(
                        original_text=original,
                        translated_text=translation,
                        all_rows=all_rows,
                        target_index=idx,
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

@app.post("/api/llm/test")
async def llm_test_connection(request: Request):
    """Test LLM connection using values from frontend."""
    body = await request.json()
    return await llm_service.test_connection(
        api_url_override=body.get("api_url"),
        model_override=body.get("model"),
    )

if __name__ == "__main__":
    import uvicorn
    # Use port 8000 or configurable if needed
    uvicorn.run(app, host="127.0.0.1", port=8000)

