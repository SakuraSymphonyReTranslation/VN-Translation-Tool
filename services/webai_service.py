import os
import sys
import json
import re
import urllib.request
import zipfile
import shutil
import tempfile
from . import config_manager

GITHUB_REPO = "Amm1rr/WebAI-to-API"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_TAGS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"

def get_webai_dir():
    return os.path.join(config_manager.BASE_DIR, "WebAI-to-API")

def get_local_version():
    webai_dir = get_webai_dir()
    if not os.path.exists(webai_dir):
        old_dir = os.path.join(config_manager.BASE_DIR, "WebAI-to-API-0.4.0-modified")
        if os.path.exists(old_dir):
            webai_dir = old_dir
        else:
            return "Not Installed"
            
    pyproject_path = os.path.join(webai_dir, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error reading local pyproject.toml: {e}")
            
    changelog_path = os.path.join(webai_dir, "Changelog.md")
    if os.path.exists(changelog_path):
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                first_line = f.readline()
            match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', first_line)
            if match:
                return match.group(1)
        except Exception:
            pass
            
    return "0.4.0"

def _clean_version(ver_str: str) -> tuple:
    if not ver_str:
        return (0, 0, 0)
    cleaned = re.sub(r'^[^\d]*', '', ver_str.strip())
    parts = []
    for p in cleaned.split('.'):
        num = re.match(r'^\d+', p)
        if num:
            parts.append(int(num.group(0)))
        else:
            parts.append(0)
    return tuple(parts)

def check_for_update():
    local_ver = get_local_version()
    webai_dir = get_webai_dir()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            latest_tag = data.get("tag_name", "")
            release_name = data.get("name", latest_tag)
            release_notes = data.get("body", "")
            published_at = data.get("published_at", "")
            zip_url = data.get("zipball_url") or f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{latest_tag}.zip"
            
            local_tuple = _clean_version(local_ver)
            remote_tuple = _clean_version(latest_tag)
            
            has_update = remote_tuple > local_tuple
            
            return {
                "status": "success",
                "folder": webai_dir,
                "folder_exists": os.path.exists(webai_dir),
                "local_version": local_ver,
                "latest_version": latest_tag,
                "has_update": has_update,
                "release_name": release_name,
                "release_notes": release_notes[:500] + ("..." if len(release_notes) > 500 else ""),
                "published_at": published_at,
                "download_url": zip_url,
                "repo": GITHUB_REPO
            }
    except Exception as e:
        print(f"Error checking GitHub latest release: {e}")
        try:
            req_tags = urllib.request.Request(GITHUB_TAGS_URL, headers=headers)
            with urllib.request.urlopen(req_tags, timeout=10) as resp:
                tags_data = json.loads(resp.read().decode())
                if tags_data and len(tags_data) > 0:
                    latest_tag = tags_data[0].get("name", "")
                    local_tuple = _clean_version(local_ver)
                    remote_tuple = _clean_version(latest_tag)
                    has_update = remote_tuple > local_tuple
                    zip_url = tags_data[0].get("zipball_url") or f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{latest_tag}.zip"
                    return {
                        "status": "success",
                        "folder": webai_dir,
                        "folder_exists": os.path.exists(webai_dir),
                        "local_version": local_ver,
                        "latest_version": latest_tag,
                        "has_update": has_update,
                        "release_name": f"Release {latest_tag}",
                        "release_notes": "Tag update from GitHub",
                        "published_at": "",
                        "download_url": zip_url,
                        "repo": GITHUB_REPO
                    }
        except Exception as tag_err:
            print(f"Error checking GitHub tags: {tag_err}")

        return {
            "status": "error",
            "folder": webai_dir,
            "folder_exists": os.path.exists(webai_dir),
            "local_version": local_ver,
            "latest_version": local_ver,
            "has_update": False,
            "error": str(e),
            "repo": GITHUB_REPO
        }

def perform_update():
    webai_dir = get_webai_dir()
    os.makedirs(webai_dir, exist_ok=True)
    
    update_info = check_for_update()
    if update_info.get("status") != "success":
        return {"status": "error", "message": f"Could not fetch update info: {update_info.get('error')}"}
        
    download_url = update_info.get("download_url")
    if not download_url:
        return {"status": "error", "message": "No download URL available"}
        
    backup_files = {}
    config_conf_path = os.path.join(webai_dir, "config.conf")
    if os.path.exists(config_conf_path):
        try:
            with open(config_conf_path, "r", encoding="utf-8") as f:
                backup_files["config.conf"] = f.read()
        except Exception:
            pass
            
    temp_dir = tempfile.mkdtemp(prefix="webai_update_")
    zip_path = os.path.join(temp_dir, "update.zip")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(zip_path, "wb") as out_f:
            shutil.copyfileobj(resp, out_f)
            
        extract_dir = os.path.join(temp_dir, "extracted")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        extracted_items = os.listdir(extract_dir)
        source_root = extract_dir
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
            source_root = os.path.join(extract_dir, extracted_items[0])
            
        for item in os.listdir(source_root):
            src_item = os.path.join(source_root, item)
            dst_item = os.path.join(webai_dir, item)
            if os.path.isdir(src_item):
                if os.path.exists(dst_item):
                    shutil.rmtree(dst_item)
                shutil.copytree(src_item, dst_item)
            else:
                shutil.copy2(src_item, dst_item)
                
        if "config.conf" in backup_files:
            try:
                with open(config_conf_path, "w", encoding="utf-8") as f:
                    f.write(backup_files["config.conf"])
            except Exception:
                pass
                
        new_version = get_local_version()
        return {
            "status": "success",
            "message": f"WebAI-to-API updated successfully to {new_version}!",
            "version": new_version,
            "folder": webai_dir
        }
    except Exception as e:
        print(f"Error applying WebAI update: {e}")
        return {"status": "error", "message": f"Failed to apply update: {str(e)}"}
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
