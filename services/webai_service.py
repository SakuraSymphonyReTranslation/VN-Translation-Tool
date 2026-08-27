import os
import sys
import json
import re
import urllib.request
import zipfile
import shutil
import tempfile
import configparser
import subprocess
from . import config_manager

GITHUB_REPO = "Amm1rr/WebAI-to-API"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_TAGS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"

def get_webai_dir():
    return os.path.join(config_manager.BASE_DIR, "WebAI-to-API")

def get_config_conf_path():
    return os.path.join(get_webai_dir(), "config.conf")

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
            
    return "0.6.0"

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

# ─── Gemini Web Cookie Management ─────────────────────────────────────────────

def get_gemini_cookies():
    conf_path = get_config_conf_path()
    cookies = {
        "psid": "",
        "psidts": "",
        "browser": "chrome",
        "has_cookies": False
    }
    
    if os.path.exists(conf_path):
        try:
            cfg = configparser.ConfigParser()
            cfg.read(conf_path, encoding="utf-8")
            if cfg.has_section("Cookies"):
                cookies["psid"] = cfg.get("Cookies", "gemini_cookie_1psid", fallback="")
                cookies["psidts"] = cfg.get("Cookies", "gemini_cookie_1psidts", fallback="")
            if cfg.has_section("Browser"):
                cookies["browser"] = cfg.get("Browser", "name", fallback="chrome")
        except Exception as e:
            print(f"Error reading config.conf: {e}")
            
    cookies["has_cookies"] = bool(cookies["psid"] and cookies["psidts"])
    return cookies

def save_gemini_cookies(psid: str, psidts: str, browser: str = "chrome"):
    conf_path = get_config_conf_path()
    webai_dir = get_webai_dir()
    os.makedirs(webai_dir, exist_ok=True)
    
    cfg = configparser.ConfigParser()
    if os.path.exists(conf_path):
        try:
            cfg.read(conf_path, encoding="utf-8")
        except Exception:
            pass
            
    if not cfg.has_section("Browser"):
        cfg.add_section("Browser")
    cfg.set("Browser", "name", browser)
    
    if not cfg.has_section("AI"):
        cfg.add_section("AI")
    cfg.set("AI", "default_ai", "gemini")
    cfg.set("AI", "default_model_gemini", "gemini-3.7-flash")
    
    if not cfg.has_section("Cookies"):
        cfg.add_section("Cookies")
    cfg.set("Cookies", "gemini_cookie_1psid", (psid or "").strip())
    cfg.set("Cookies", "gemini_cookie_1psidts", (psidts or "").strip())
    
    if not cfg.has_section("EnabledAI"):
        cfg.add_section("EnabledAI")
    cfg.set("EnabledAI", "gemini", "true")
    
    try:
        with open(conf_path, "w", encoding="utf-8") as f:
            cfg.write(f)
        return {
            "status": "success",
            "message": "Gemini Web cookies saved successfully to config.conf!",
            "has_cookies": bool(psid and psidts)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save config.conf: {str(e)}"}

def extract_cookies_from_browser(browser_name: str = "chrome"):
    """Extract Google/Gemini cookies directly from installed browser."""
    webai_src = os.path.join(get_webai_dir(), "src")
    if webai_src not in sys.path:
        sys.path.insert(0, webai_src)
        
    try:
        from app.utils.browser import CrossPlatformCookieExtractor
        extractor = CrossPlatformCookieExtractor()
        
        # Try requested browser first, then fallbacks
        browsers_to_try = [browser_name] + [b for b in ["chrome", "edge", "brave", "firefox"] if b != browser_name]
        
        for b in browsers_to_try:
            try:
                cookies = extractor.get_cookies_with_fallback(b)
                if cookies:
                    psid = ""
                    psidts = ""
                    for c in cookies:
                        if hasattr(c, 'domain') and "google" in c.domain:
                            if c.name == "__Secure-1PSID" and c.value:
                                psid = c.value
                            elif c.name == "__Secure-1PSIDTS" and c.value:
                                psidts = c.value
                                
                    if psid and psidts:
                        save_gemini_cookies(psid, psidts, b)
                        return {
                            "status": "success",
                            "message": f"Successfully extracted Gemini cookies from {b.title()}!",
                            "browser": b,
                            "psid_preview": psid[:12] + "...",
                            "psidts_preview": psidts[:12] + "...",
                            "has_cookies": True
                        }
            except Exception as b_err:
                print(f"Extraction failed for {b}: {b_err}")
                
        return {
            "status": "error",
            "message": "Could not auto-extract cookies from browser. Please ensure your browser has logged into gemini.google.com, or enter __Secure-1PSID & __Secure-1PSIDTS manually, or launch Web Login."
        }
    except Exception as e:
        return {"status": "error", "message": f"Cookie extractor error: {str(e)}"}

def launch_verify_login():
    """Launch verify_login.py in a separate console window."""
    webai_dir = get_webai_dir()
    script_path = os.path.join(webai_dir, "verify_login.py")
    if not os.path.exists(script_path):
        return {"status": "error", "message": "verify_login.py not found in WebAI-to-API"}
        
    try:
        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", f"cd /d \"{webai_dir}\" && python verify_login.py"],
                cwd=webai_dir,
                shell=True
            )
        else:
            subprocess.Popen([sys.executable, script_path], cwd=webai_dir)
            
        return {
            "status": "success",
            "message": "Launched Gemini Web Login window! Please complete the login in the browser window."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to launch login script: {str(e)}"}
