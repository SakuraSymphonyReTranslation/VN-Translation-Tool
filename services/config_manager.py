import json
import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(BASE_DIR)
    RESOURCE_DIR = BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DEFAULT_PROJECT_DATA_BASE = os.path.join(BASE_DIR, "project_data")

DEFAULT_PROJECTS = {
    "dc4_plus_harmony": {
        "identifier": "dc4_plus_harmony",
        "name": "D.C.4 Plus Harmony",
        "original_dir": r"H:\Games\D.C.4 Da Capo 4 Plus Harmony\Advdata\MES.old\json",
        "translated_dir": r"H:\Games\D.C.4 Da Capo 4 Plus Harmony\indo json\json",
        "excel_path": r"G:\DC4PH_Scenario_Mode.xlsx",
        "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, "Da Capo 4 Plus Harmony")
    },
    "da_capo_4": {
        "identifier": "da_capo_4",
        "name": "Da Capo 4",
        "original_dir": "",
        "translated_dir": "",
        "excel_path": r"G:\DC4_Scenario_Mode.xlsx",
        "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, "Da Capo 4")
    },
    "dc3_platinum_partner": {
        "identifier": "dc3_platinum_partner",
        "name": "D.C.III Platinum Partner",
        "original_dir": "",
        "translated_dir": "",
        "excel_path": "",
        "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, "dc3_platinum_partner")
    },
    "dc3_dream_days": {
        "identifier": "dc3_dream_days",
        "name": "D.C.III Dream Days",
        "original_dir": "",
        "translated_dir": "",
        "excel_path": "",
        "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, "dc3_dream_days")
    }
}

DEFAULT_CONFIG = {
    "active_project": "dc4_plus_harmony",
    "projects": DEFAULT_PROJECTS,
    "original_dir": r"H:\Games\D.C.4 Da Capo 4 Plus Harmony\Advdata\MES.old\json",
    "translated_dir": r"H:\Games\D.C.4 Da Capo 4 Plus Harmony\indo json\json",
    "excel_path": r"G:\DC4PH_Scenario_Mode.xlsx",
    "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, "Da Capo 4 Plus Harmony"),
    "unidic_dir": "",
    # LLM Configuration
    "llm_provider": "gemini_web",
    "llm_api_url": "http://localhost:6969/v1",
    "llm_model": "gemini-3.7-flash",
    "llm_temperature": 0.7,
    "llm_max_tokens": 1024,
    "llm_context_window": 5,
    "llm_glossary": [],
    "llm_retranslate_prompt": "",
    "llm_polish_prompt": "",
    "gemini_cookie_1psid": "",
    "gemini_cookie_1psidts": "" 
}

def _sanitize_identifier(identifier: str) -> str:
    if not identifier:
        return "default"
    clean = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in identifier.strip().lower())
    return clean or "default"

def resolve_project_data_dir(input_path: str, fallback_identifier: str = "default") -> str:
    if not input_path or input_path.strip() == "project_data":
        return os.path.join(DEFAULT_PROJECT_DATA_BASE, fallback_identifier)
    
    clean = input_path.strip()
    if os.path.isabs(clean):
        return clean
    
    if clean.startswith("project_data\\") or clean.startswith("project_data/"):
        sub = clean[len("project_data/"):].strip("\\/")
        return os.path.join(DEFAULT_PROJECT_DATA_BASE, sub)
        
    return os.path.join(DEFAULT_PROJECT_DATA_BASE, clean)

def get_available_cache_folders():
    base_dir = DEFAULT_PROJECT_DATA_BASE
    if not os.path.exists(base_dir):
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass
        return []
    
    folders = []
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                try:
                    json_count = len([f for f in os.listdir(item_path) if f.endswith(".json")])
                except Exception:
                    json_count = 0
                folders.append({
                    "name": item,
                    "path": item_path,
                    "relative_path": f"project_data\\{item}",
                    "file_count": json_count
                })
    except Exception as e:
        print(f"Error listing cache folders: {e}")
        
    return sorted(folders, key=lambda x: x["name"].lower())

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if "projects" not in data or not isinstance(data["projects"], dict) or len(data["projects"]) == 0:
            data["projects"] = dict(DEFAULT_PROJECTS)
            
        active_id = data.get("active_project", "dc4_plus_harmony")
        if active_id not in data["projects"]:
            if data["projects"]:
                active_id = next(iter(data["projects"].keys()))
                data["active_project"] = active_id
            else:
                data["projects"] = dict(DEFAULT_PROJECTS)
                active_id = "dc4_plus_harmony"
                data["active_project"] = active_id
                
        active_proj = data["projects"][active_id]
        
        if "identifier" not in active_proj:
            active_proj["identifier"] = active_id
        if "name" not in active_proj:
            active_proj["name"] = active_id.replace("_", " ").title()
            
        proj_data_dir = active_proj.get("project_data_dir")
        if not proj_data_dir or proj_data_dir == "project_data":
            active_proj["project_data_dir"] = os.path.join(DEFAULT_PROJECT_DATA_BASE, active_proj["identifier"])
        else:
            active_proj["project_data_dir"] = resolve_project_data_dir(proj_data_dir, active_proj["identifier"])
            
        data["original_dir"] = active_proj.get("original_dir", "")
        data["translated_dir"] = active_proj.get("translated_dir", "")
        data["excel_path"] = active_proj.get("excel_path", "")
        data["project_data_dir"] = active_proj.get("project_data_dir", os.path.join(DEFAULT_PROJECT_DATA_BASE, active_proj["identifier"]))
        
        try:
            os.makedirs(data["project_data_dir"], exist_ok=True)
        except Exception:
            pass
            
        return data
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    try:
        active_id = config.get("active_project", "dc4_plus_harmony")
        active_id = _sanitize_identifier(active_id)
        config["active_project"] = active_id
        
        if "projects" not in config or not isinstance(config["projects"], dict):
            config["projects"] = {}
            
        custom_proj_dir = config.get("project_data_dir")
        resolved_proj_dir = resolve_project_data_dir(custom_proj_dir, active_id)
            
        if active_id not in config["projects"]:
            config["projects"][active_id] = {
                "identifier": active_id,
                "name": config.get("project_name", active_id.replace("_", " ").title()),
                "original_dir": config.get("original_dir", ""),
                "translated_dir": config.get("translated_dir", ""),
                "excel_path": config.get("excel_path", ""),
                "project_data_dir": resolved_proj_dir
            }
        else:
            proj = config["projects"][active_id]
            proj["identifier"] = active_id
            if "project_name" in config and config["project_name"]:
                proj["name"] = config["project_name"]
            proj["original_dir"] = config.get("original_dir", proj.get("original_dir", ""))
            proj["translated_dir"] = config.get("translated_dir", proj.get("translated_dir", ""))
            proj["excel_path"] = config.get("excel_path", proj.get("excel_path", ""))
            proj["project_data_dir"] = resolved_proj_dir
                
        config["project_data_dir"] = resolved_proj_dir
        
        try:
            os.makedirs(resolved_proj_dir, exist_ok=True)
        except Exception:
            pass

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_path(key):
    config = load_config()
    return config.get(key, DEFAULT_CONFIG.get(key, ""))

def get_active_project():
    config = load_config()
    active_id = config.get("active_project", "dc4_plus_harmony")
    projects = config.get("projects", {})
    return active_id, projects.get(active_id, {})

def switch_project(project_id: str):
    config = load_config()
    clean_id = _sanitize_identifier(project_id)
    
    if clean_id not in config.get("projects", {}):
        config.setdefault("projects", {})[clean_id] = {
            "identifier": clean_id,
            "name": clean_id.replace("_", " ").title(),
            "original_dir": "",
            "translated_dir": "",
            "excel_path": "",
            "project_data_dir": os.path.join(DEFAULT_PROJECT_DATA_BASE, clean_id)
        }
        
    config["active_project"] = clean_id
    active_proj = config["projects"][clean_id]
    config["original_dir"] = active_proj.get("original_dir", "")
    config["translated_dir"] = active_proj.get("translated_dir", "")
    config["excel_path"] = active_proj.get("excel_path", "")
    config["project_data_dir"] = active_proj.get("project_data_dir", os.path.join(DEFAULT_PROJECT_DATA_BASE, clean_id))
    
    save_config(config)
    return config

def save_project_profile(project_id: str, profile_data: dict):
    config = load_config()
    clean_id = _sanitize_identifier(project_id or profile_data.get("identifier", ""))
    
    if not clean_id:
        return False
        
    custom_dir = profile_data.get("project_data_dir")
    resolved_dir = resolve_project_data_dir(custom_dir, clean_id)
        
    config.setdefault("projects", {})[clean_id] = {
        "identifier": clean_id,
        "name": profile_data.get("name", clean_id.replace("_", " ").title()),
        "original_dir": profile_data.get("original_dir", ""),
        "translated_dir": profile_data.get("translated_dir", ""),
        "excel_path": profile_data.get("excel_path", ""),
        "project_data_dir": resolved_dir
    }
    
    if config.get("active_project") == clean_id:
        proj = config["projects"][clean_id]
        config["original_dir"] = proj["original_dir"]
        config["translated_dir"] = proj["translated_dir"]
        config["excel_path"] = proj["excel_path"]
        config["project_data_dir"] = proj["project_data_dir"]
        
    return save_config(config)

def delete_project_profile(project_id: str):
    config = load_config()
    clean_id = _sanitize_identifier(project_id)
    
    if clean_id in config.get("projects", {}):
        del config["projects"][clean_id]
        if config.get("active_project") == clean_id:
            if config["projects"]:
                config["active_project"] = next(iter(config["projects"].keys()))
            else:
                config["projects"] = dict(DEFAULT_PROJECTS)
                config["active_project"] = "dc4_plus_harmony"
        save_config(config)
        return True
    return False
