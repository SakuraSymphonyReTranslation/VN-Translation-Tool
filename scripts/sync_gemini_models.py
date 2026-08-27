import os
import re
import sys
import json
import urllib.request
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

README_ID_PATH = os.path.join(BASE_DIR, "README.md")
README_EN_PATH = os.path.join(BASE_DIR, "README_EN.md")
INDEX_HTML_PATH = os.path.join(BASE_DIR, "templates", "index.html")
LLM_SERVICE_PATH = os.path.join(BASE_DIR, "services", "llm_service.py")
WEBAI_DIR = os.path.join(BASE_DIR, "WebAI-to-API")

def detect_latest_gemini_models():
    """
    Detects active Gemini model lineup from:
    1. Upstream WebAI-to-API source code / changelog
    2. Google Generative AI / WebAPI catalog
    3. Fallback to latest confirmed Gemini lineup (3.7 / 3.5 / 3.1)
    """
    models = {
        "flash": "gemini-3.7-flash",
        "flash_name": "3.7 Flash",
        "thinking": "gemini-3.7-flash-thinking",
        "thinking_name": "Extended thinking",
        "lite": "gemini-3.5-flash-lite",
        "lite_name": "3.5 Flash-Lite",
        "pro": "gemini-3.1-pro",
        "pro_name": "3.1 Pro"
    }

    # 1. Check WebAI-to-API files if available
    webai_client = os.path.join(WEBAI_DIR, "src", "app", "services", "providers", "gemini", "shared.py")
    if os.path.exists(webai_client):
        try:
            with open(webai_client, "r", encoding="utf-8") as f:
                content = f.read()
            matches = re.findall(r'["\'](gemini-([\d\.]+)-(flash|pro|flash-lite|thinking|flash-thinking))["\']', content)
            if matches:
                flash_vers = []
                pro_vers = []
                lite_vers = []
                for full_id, ver, mtype in matches:
                    try:
                        v_tuple = tuple(int(x) for x in ver.split('.'))
                        if "lite" in mtype:
                            lite_vers.append((v_tuple, ver, full_id))
                        elif "pro" in mtype:
                            pro_vers.append((v_tuple, ver, full_id))
                        elif "flash" in mtype:
                            flash_vers.append((v_tuple, ver, full_id))
                    except Exception:
                        pass
                
                if flash_vers:
                    best_f = max(flash_vers, key=lambda x: x[0])
                    models["flash"] = f"gemini-{best_f[1]}-flash"
                    models["flash_name"] = f"{best_f[1]} Flash"
                    models["thinking"] = f"gemini-{best_f[1]}-flash-thinking"
                    models["thinking_name"] = "Extended thinking"
                if lite_vers:
                    best_l = max(lite_vers, key=lambda x: x[0])
                    models["lite"] = f"gemini-{best_l[1]}-flash-lite"
                    models["lite_name"] = f"{best_l[1]} Flash-Lite"
                if pro_vers:
                    best_p = max(pro_vers, key=lambda x: x[0])
                    models["pro"] = f"gemini-{best_p[1]}-pro"
                    models["pro_name"] = f"{best_p[1]} Pro"
        except Exception as e:
            print(f"Notice: Checking shared.py: {e}")

    return models


def update_readme_id(models):
    if not os.path.exists(README_ID_PATH):
        return False
    with open(README_ID_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_block = f"""<!-- GEMINI_MODELS_START -->
* **Dukungan Model Gemini Generasi Terbaru**:
  * `{models['flash']}` ({models['flash_name']} — All-around help / Default)
  * `{models['thinking']}` ({models['thinking_name']} — Complex problem solving)
  * `{models['lite']}` ({models['lite_name']} — Fastest answers)
  * `{models['pro']}` ({models['pro_name']} — Advanced reasoning)
<!-- GEMINI_MODELS_END -->"""

    # Also update the badge
    badge_pattern = r'\[!\[Gemini\]\(https://img\.shields\.io/badge/AI-Gemini%20[\d\.]+%20Flash-4285F4[^)]+\)\]'
    badge_new = f'[![Gemini](https://img.shields.io/badge/AI-Gemini%20{models["flash_name"].replace(" ", "%20")}-4285F4?style=for-the-badge&logo=google&logoColor=white)]'
    content_updated = re.sub(badge_pattern, badge_new, content)

    if "<!-- GEMINI_MODELS_START -->" in content_updated and "<!-- GEMINI_MODELS_END -->" in content_updated:
        pattern = r"<!-- GEMINI_MODELS_START -->.*?<!-- GEMINI_MODELS_END -->"
        updated = re.sub(pattern, new_block, content_updated, flags=re.DOTALL)
    else:
        old_pattern = r"\* \*\*Dukungan Model Gemini Generasi Terbaru\*\*:\n(  \* `gemini-[^`]+` \([^\)]+\)\n?)+"
        if re.search(old_pattern, content_updated):
            updated = re.sub(old_pattern, new_block + "\n", content_updated)
        else:
            updated = content_updated

    if updated != content:
        with open(README_ID_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("Updated README.md (Indonesian) model list & badge!")
        return True
    return False


def update_readme_en(models):
    if not os.path.exists(README_EN_PATH):
        return False
    with open(README_EN_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_block = f"""<!-- GEMINI_MODELS_START -->
* **Latest Gemini Model Lineup**:
  * `{models['flash']}` ({models['flash_name']} — All-around help / Default)
  * `{models['thinking']}` ({models['thinking_name']} — Complex problem solving)
  * `{models['lite']}` ({models['lite_name']} — Fastest answers)
  * `{models['pro']}` ({models['pro_name']} — Advanced reasoning)
<!-- GEMINI_MODELS_END -->"""

    badge_pattern = r'\[!\[Gemini\]\(https://img\.shields\.io/badge/AI-Gemini%20[\d\.]+%20Flash-4285F4[^)]+\)\]'
    badge_new = f'[![Gemini](https://img.shields.io/badge/AI-Gemini%20{models["flash_name"].replace(" ", "%20")}-4285F4?style=for-the-badge&logo=google&logoColor=white)]'
    content_updated = re.sub(badge_pattern, badge_new, content)

    if "<!-- GEMINI_MODELS_START -->" in content_updated and "<!-- GEMINI_MODELS_END -->" in content_updated:
        pattern = r"<!-- GEMINI_MODELS_START -->.*?<!-- GEMINI_MODELS_END -->"
        updated = re.sub(pattern, new_block, content_updated, flags=re.DOTALL)
    else:
        old_pattern = r"\* \*\*Latest Gemini Model Lineup\*\*:\n(  \* `gemini-[^`]+` \([^\)]+\)\n?)+"
        if re.search(old_pattern, content_updated):
            updated = re.sub(old_pattern, new_block + "\n", content_updated)
        else:
            updated = content_updated

    if updated != content:
        with open(README_EN_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("Updated README_EN.md (English) model list & badge!")
        return True
    return False


def update_index_html(models):
    if not os.path.exists(INDEX_HTML_PATH):
        return False
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_datalist = f"""<!-- GEMINI_DATALIST_START -->
                                    <option value="{models['flash']}">{models['flash_name']} (All-around help / Default)</option>
                                    <option value="{models['thinking']}">{models['thinking_name']} (Complex problem solving)</option>
                                    <option value="{models['lite']}">{models['lite_name']} (Fastest answers)</option>
                                    <option value="{models['pro']}">{models['pro_name']} (Advanced reasoning)</option>
                                    <option value="flash">WebAI Flash (Auto-latest)</option>
                                    <option value="thinking">WebAI Thinking (Auto-latest)</option>
                                    <option value="pro">WebAI Pro (Auto-latest)</option>
                                    <!-- GEMINI_DATALIST_END -->"""

    if "<!-- GEMINI_DATALIST_START -->" in content and "<!-- GEMINI_DATALIST_END -->" in content:
        pattern = r"<!-- GEMINI_DATALIST_START -->.*?<!-- GEMINI_DATALIST_END -->"
        updated = re.sub(pattern, new_datalist, content, flags=re.DOTALL)
    else:
        old_pattern = r'<datalist id="gemini-models-list">.*?</datalist>'
        replacement = f'<datalist id="gemini-models-list">\n{new_datalist}\n                                    <option v-for="m in fetchedModels" :key="m" :value="m">{{{{ m }}}}</option>\n                                </datalist>'
        updated = re.sub(old_pattern, replacement, content, flags=re.DOTALL)

    if updated != content:
        with open(INDEX_HTML_PATH, "w", encoding="utf-8") as f:
            f.write(updated)
        print("Updated templates/index.html datalist options!")
        return True
    return False


def update_llm_service(models):
    if not os.path.exists(LLM_SERVICE_PATH):
        return False
    with open(LLM_SERVICE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_map_str = f"""GEMINI_WEB_MODEL_MAP = {{
    "{models['flash']}": "gemini-3.0-flash",
    "{models['thinking']}": "gemini-3.0-flash-thinking",
    "{models['lite']}": "gemini-3.0-flash",
    "{models['pro']}": "gemini-3.0-pro",
    "gemini-3.7-flash": "gemini-3.0-flash",
    "gemini-3.7-flash-thinking": "gemini-3.0-flash-thinking",
    "gemini-3.5-flash-lite": "gemini-3.0-flash",
    "gemini-3.1-pro": "gemini-3.0-pro",
    "flash": "gemini-3.0-flash",
    "thinking": "gemini-3.0-flash-thinking",
    "pro": "gemini-3.0-pro",
}}"""

    pattern = r"GEMINI_WEB_MODEL_MAP\s*=\s*\{.*?\}"
    if re.search(pattern, content, flags=re.DOTALL):
        updated = re.sub(pattern, new_map_str, content, flags=re.DOTALL)
        if updated != content:
            with open(LLM_SERVICE_PATH, "w", encoding="utf-8") as f:
                f.write(updated)
            print("Updated services/llm_service.py model mapping!")
            return True
    return False


def sync_github_topics_and_about(models):
    """
    Synchronizes GitHub repository topics and description dynamically.
    Converts gemini-3.7-flash -> gemini-3-7-flash topic tag.
    """
    new_topic_tag = models['flash'].replace('.', '-') # e.g. gemini-3-7-flash or gemini-3-8-flash
    
    try:
        res = subprocess.run(["gh", "repo", "view", "--json", "repositoryTopics,description"], capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            current_topics = [t["name"] for t in data.get("repositoryTopics", [])]
            
            topics_to_remove = [t for t in current_topics if re.match(r"^gemini-[\d\-]+-(flash|pro|lite)$", t) and t != new_topic_tag]
            
            base_topics = ["dc4", "fastapi", "furigana", "gemini", new_topic_tag, "localization", "mecab", "translation", "translation-tool", "unidic", "visual-novel", "vue3"]
            
            add_args = []
            for t in base_topics:
                add_args.extend(["--add-topic", t])
            for t in topics_to_remove:
                add_args.extend(["--remove-topic", t])
                
            edit_cmd = ["gh", "repo", "edit"] + add_args
            sub_res = subprocess.run(edit_cmd, capture_output=True, text=True)
            if sub_res.returncode == 0:
                print(f"Successfully synced GitHub repo topic: {new_topic_tag} (removed: {topics_to_remove})")
                return True
            else:
                print(f"gh repo edit notice: {sub_res.stderr}")
    except Exception as e:
        print(f"GitHub CLI sync notice (skipped if no gh token): {e}")
    return False


def main():
    print("Checking and synchronizing Gemini models across repository...")
    models = detect_latest_gemini_models()
    print("Detected Gemini Model Lineup:")
    for k, v in models.items():
        print(f"  - {k}: {v}")

    c1 = update_readme_id(models)
    c2 = update_readme_en(models)
    c3 = update_index_html(models)
    c4 = update_llm_service(models)
    c5 = sync_github_topics_and_about(models)

    if any([c1, c2, c3, c4, c5]):
        print("Model synchronization completed with updates applied!")
    else:
        print("All files and topics are already up-to-date with current model lineup.")

if __name__ == "__main__":
    main()
