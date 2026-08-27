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
    app_cfg = config_manager.load_config()
    cookies = {
        "psid": app_cfg.get("gemini_cookie_1psid", ""),
        "psidts": app_cfg.get("gemini_cookie_1psidts", ""),
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
            
        # Also sync to VN Translation Tool config.json
        try:
            app_cfg = config_manager.load_config()
            app_cfg["gemini_cookie_1psid"] = (psid or "").strip()
            app_cfg["gemini_cookie_1psidts"] = (psidts or "").strip()
            config_manager.save_config(app_cfg)
        except Exception:
            pass

        return {
            "status": "success",
            "message": "Gemini Web cookies saved successfully!",
            "has_cookies": bool(psid and psidts)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save config.conf: {str(e)}"}

def _read_locked_file_win(src_path):
    """Read a locked file safely on Windows using kernel32 CreateFileW with full sharing."""
    import ctypes
    from ctypes import wintypes
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    handle = ctypes.windll.kernel32.CreateFileW(
        src_path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None
    )
    if handle == INVALID_HANDLE_VALUE:
        return None
    try:
        file_size = ctypes.windll.kernel32.GetFileSize(handle, None)
        if file_size <= 0:
            return None
        buf = ctypes.create_string_buffer(file_size)
        bytes_read = wintypes.DWORD()
        success = ctypes.windll.kernel32.ReadFile(handle, buf, file_size, ctypes.byref(bytes_read), None)
        if success:
            return buf.raw[:bytes_read.value]
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)
    return None

def _win_decrypt_dpapi(cipher_bytes):
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(cipher_bytes, None, None, None, 0)[1]
    except Exception:
        pass
    try:
        import ctypes
        from ctypes import wintypes
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]
        blob_in = DATA_BLOB(len(cipher_bytes), ctypes.cast(ctypes.create_string_buffer(cipher_bytes), ctypes.POINTER(ctypes.c_byte)))
        blob_out = DATA_BLOB()
        if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            out_bytes = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return out_bytes
    except Exception:
        pass
    return None

def _win_decrypt_aes_gcm(key, iv, ciphertext, tag):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext + tag, None)
    except Exception:
        pass
    try:
        from Cryptodome.Cipher import AES
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        return cipher.decrypt_and_verify(ciphertext, tag)
    except Exception:
        pass
    return None

def extract_cookies_from_browser(browser_name: str = "auto"):
    """
    Universal multi-browser cookie extractor supporting:
    Chrome, Edge, Brave, Firefox, LibreWolf, Waterfox, Floorp, Zen, Opera, Opera GX, Vivaldi, Thorium, Arc.
    """
    browser_clean = (browser_name or "auto").lower()

    # 1. Try browser_cookie3 if installed
    try:
        import browser_cookie3
        b3_map = {
            "chrome": browser_cookie3.chrome,
            "edge": browser_cookie3.edge,
            "brave": browser_cookie3.brave,
            "firefox": browser_cookie3.firefox,
            "opera": browser_cookie3.opera,
            "opera_gx": browser_cookie3.opera_gx if hasattr(browser_cookie3, "opera_gx") else browser_cookie3.opera,
            "vivaldi": browser_cookie3.vivaldi if hasattr(browser_cookie3, "vivaldi") else None
        }
        order = [browser_clean] if browser_clean in b3_map else list(b3_map.keys())
        for b_key in order:
            b_fn = b3_map.get(b_key)
            if b_fn:
                try:
                    cj = b_fn(domain_name="google.com")
                    psid, psidts = "", ""
                    for c in cj:
                        if c.name == "__Secure-1PSID":
                            psid = c.value
                        elif c.name == "__Secure-1PSIDTS":
                            psidts = c.value
                    if psid and psidts:
                        save_gemini_cookies(psid, psidts, b_key)
                        return {
                            "status": "success",
                            "message": f"Berhasil mengekstrak cookie Gemini dari browser {b_key.title()}!",
                            "browser": b_key,
                            "psid_preview": psid[:12] + "...",
                            "psidts_preview": psidts[:12] + "...",
                            "has_cookies": True
                        }
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Try Firefox & Gecko engines (Unencrypted SQLite)
    firefox_base_dirs = [
        ("firefox", os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")),
        ("waterfox", os.path.expandvars(r"%APPDATA%\Waterfox\Profiles")),
        ("librewolf", os.path.expandvars(r"%APPDATA%\LibreWolf\Profiles")),
        ("floorp", os.path.expandvars(r"%APPDATA%\Floorp\Profiles")),
        ("zen", os.path.expandvars(r"%APPDATA%\zen\Profiles"))
    ]

    if browser_clean in ["auto", "firefox", "waterfox", "librewolf", "floorp", "zen"]:
        for b_label, f_dir in firefox_base_dirs:
            if not os.path.exists(f_dir):
                continue
            for prof in os.listdir(f_dir):
                db_path = os.path.join(f_dir, prof, "cookies.sqlite")
                if os.path.exists(db_path):
                    raw_db = _read_locked_file_win(db_path)
                    if not raw_db:
                        continue
                    temp_db = tempfile.NamedTemporaryFile(delete=False)
                    temp_db.write(raw_db)
                    temp_db.close()
                    try:
                        conn = sqlite3.connect(temp_db.name)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%google%' AND name IN ('__Secure-1PSID', '__Secure-1PSIDTS')")
                        ff_cookies = dict(cursor.fetchall())
                        conn.close()
                        if "__Secure-1PSID" in ff_cookies and "__Secure-1PSIDTS" in ff_cookies:
                            psid = ff_cookies["__Secure-1PSID"]
                            psidts = ff_cookies["__Secure-1PSIDTS"]
                            save_gemini_cookies(psid, psidts, b_label)
                            return {
                                "status": "success",
                                "message": f"Berhasil mengekstrak cookie Gemini dari {b_label.title()}!",
                                "browser": b_label,
                                "psid_preview": psid[:12] + "...",
                                "psidts_preview": psidts[:12] + "...",
                                "has_cookies": True
                            }
                    except Exception:
                        pass
                    finally:
                        try:
                            os.unlink(temp_db.name)
                        except Exception:
                            pass

    # 3. Direct Chromium Decryption Engine (DPAPI + AES-GCM for Chrome, Edge, Brave, Opera, Vivaldi, Thorium, Arc)
    chromium_paths = {
        "chrome": [os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"), os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Beta\User Data")],
        "edge": [os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"), os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge Dev\User Data")],
        "brave": [os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data")],
        "opera": [os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable")],
        "opera_gx": [os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable")],
        "vivaldi": [os.path.expandvars(r"%LOCALAPPDATA%\Vivaldi\User Data")],
        "thorium": [os.path.expandvars(r"%LOCALAPPDATA%\Thorium\User Data")],
        "arc": [os.path.expandvars(r"%LOCALAPPDATA%\The Browser Company\Arc\User Data")],
        "chromium": [os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data")]
    }

    chrom_order = [browser_clean] if browser_clean in chromium_paths else list(chromium_paths.keys())

    for b_key in chrom_order:
        for base_dir in chromium_paths.get(b_key, []):
            if not os.path.exists(base_dir):
                continue
            local_state_path = os.path.join(base_dir, "Local State")
            if not os.path.exists(local_state_path):
                continue
            decrypted_key = None
            try:
                raw_ls = _read_locked_file_win(local_state_path)
                local_state = json.loads(raw_ls.decode('utf-8', errors='ignore')) if raw_ls else {}
                enc_key_b64 = local_state.get("os_crypt", {}).get("encrypted_key")
                if enc_key_b64:
                    enc_key = base64.b64decode(enc_key_b64)[5:]
                    decrypted_key = _win_decrypt_dpapi(enc_key)
            except Exception:
                pass

            profiles = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Guest Profile"]
            for prof in profiles:
                for c_sub in [os.path.join(prof, "Network", "Cookies"), os.path.join(prof, "Cookies"), "Cookies"]:
                    c_path = os.path.join(base_dir, c_sub)
                    if os.path.exists(c_path):
                        raw_db = _read_locked_file_win(c_path)
                        if not raw_db:
                            continue
                        temp_db = tempfile.NamedTemporaryFile(delete=False)
                        temp_db.write(raw_db)
                        temp_db.close()
                        cookies_found = {}
                        try:
                            conn = sqlite3.connect(temp_db.name)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE '%google%'")
                            for name, value, enc_val in cursor.fetchall():
                                if name in ["__Secure-1PSID", "__Secure-1PSIDTS"]:
                                    if value:
                                        cookies_found[name] = value
                                    elif enc_val and decrypted_key:
                                        if enc_val.startswith(b"v10") or enc_val.startswith(b"v11"):
                                            iv = enc_val[3:15]
                                            ciphertext = enc_val[15:-16]
                                            tag = enc_val[-16:]
                                            dec = _win_decrypt_aes_gcm(decrypted_key, iv, ciphertext, tag)
                                            if dec:
                                                cookies_found[name] = dec.decode('utf-8', errors='ignore')
                                        else:
                                            dec = _win_decrypt_dpapi(enc_val)
                                            if dec:
                                                cookies_found[name] = dec.decode('utf-8', errors='ignore')
                            conn.close()
                        except Exception:
                            pass
                        finally:
                            try:
                                os.unlink(temp_db.name)
                            except Exception:
                                pass

                        if "__Secure-1PSID" in cookies_found and "__Secure-1PSIDTS" in cookies_found:
                            psid = cookies_found["__Secure-1PSID"]
                            psidts = cookies_found["__Secure-1PSIDTS"]
                            save_gemini_cookies(psid, psidts, b_key)
                            return {
                                "status": "success",
                                "message": f"Berhasil mengekstrak cookie Gemini dari browser {b_key.title()}!",
                                "browser": b_key,
                                "psid_preview": psid[:12] + "...",
                                "psidts_preview": psidts[:12] + "...",
                                "has_cookies": True
                            }

    return {
        "status": "warning",
        "message": "Fitur keamanan Windows/Chromium (App-Bound Encryption) membatasi akses file cookie saat browser aktif. Silakan klik tombol 'Launch Login' (atau buka gemini.google.com), tekan F12 > Application > Cookies, salin nilai __Secure-1PSID & __Secure-1PSIDTS ke kolom lalu klik 'Save Cookies'."
    }


():
    """Open Gemini Web in browser for login."""
    import webbrowser
    try:
        webbrowser.open("https://gemini.google.com")
        return {
            "status": "success",
            "message": "Opened gemini.google.com in your browser! Please log in, then copy __Secure-1PSID & __Secure-1PSIDTS or click Auto-Extract."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to open browser: {str(e)}"}
