# VN Translation Tool

<div align="center">

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Frontend-Vue.js%203-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
  [![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

  <br>

  **[🇮🇩 Bahasa Indonesia](README.md)** | **[🇬🇧 English](README_EN.md)**

</div>

**VN Translation Tool** is a modern local web application purpose-built for translating, editing, polishing, and localizing **Visual Novel (VN)** script files (such as Circus Engine / D.C. Series, LucaSystem, and generic JSON-based game scripts).

It features a streamlined *side-by-side editor*, automatic Furigana annotations, character glossary management, intelligent Romaji & Regex search, and deep AI/LLM integration (**Local LLM / WebAI-to-API Gemini**) without cumbersome manual copy-pasting.

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [Interface Overview](#-interface-overview)
- [System Requirements](#-system-requirements)
- [Installation & Running](#-installation--running)
- [User Guide (Step-by-Step)](#-user-guide-step-by-step)
  - [1. Project Profile & Directory Setup](#1-project-profile--directory-setup)
  - [2. Script Navigation & Editing](#2-script-navigation--editing)
  - [3. AI / LLM Translation & Polishing](#3-ai--llm-translation--polishing)
  - [4. Glossary & Character Consistency](#4-glossary--character-consistency)
  - [5. Global Search & Find-and-Replace](#5-global-search--find-and-replace)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Contributing & License](#-contributing--license)

---

## ✨ Key Features

### 🎮 1. Multi-Project Management & Cache Isolation
* **Multiple Game Support**: Manage and switch between multiple visual novel projects (e.g., *D.C.4 Plus Harmony*, *Da Capo 4*, *D.C.III Platinum Partner*, *D.C.III Dream Days*, etc.) within a single instance.
* **Isolated Cache (`project_data/<slug>`)**: Each project maintains its own dedicated cache directory, ensuring rich saves, editing states, and translation histories remain strictly separated.
* **Dropdown Sync & Custom Paths**: Easily select existing cache folders via dropdown or define custom directories directly from the settings modal.

### 📝 2. Modern Side-by-Side Script Editor
* **Original Japanese (Raw JP) vs. Translation Columns**: Clean parallel layout for effortless context comparison.
* **5 Tiered Translation Layers**:
  * `Initial` — Base translation / raw game import.
  * `Machine` — Raw machine translation (MTL).
  * `Better` — First-pass draft improvements.
  * `Best` — Refined and verified translations.
  * `Polished` — Final publication-ready localized script.
* **Smart Priority Export**: On save, the system automatically exports the highest available translation layer (`Polished` > `Best` > `Better` > `Initial` > `Machine`) to the game-ready JSON.
* **Split View**: Compare two translation tabs side-by-side (e.g., `Initial` vs. `Polished`).
* **Auto-Healing & Auto-Sync**: Automatically repairs and synchronizes missing Japanese raw text whenever the original JSON directory is properly linked.

### 📖 3. Furigana Parser & Smart Romaji Search
* **Automatic Kanji Readings**: Integrated MeCab / UniDic engine to display furigana over kanji in real-time.
* **Romaji-Powered Search**: Searching `arisu` instantly matches kanji `有里栖`, hiragana `ありす`, or katakana `アリス`.
* **Regex & In-File Search**: Filter lines using regular expressions and jump directly to target dialogue matches.

### 🤖 4. LLM & WebAI-to-API Manager Integration
* **OpenAI API & Gemini Compatible**: Works out-of-the-box with standard `/v1/chat/completions` endpoints (e.g., Ollama, LM Studio, vLLM, WebAI-to-API).
* **Built-in WebAI-to-API Manager**:
  * Seamlessly connects to the local `WebAI-to-API` server (port `6969`) to utilize browser-based Gemini models.
  * **GitHub Auto-Update**: 1-click *Check Update* and *Update Now* buttons to upgrade the local WebAI-to-API runtime directly from official GitHub releases.
* **Batch Translation & Polishing**: Retranslate or polish entire scenario files in batches with real-time SSE progress indicators.
* **Automated Glossary Injection**: Character names, honorifics (e.g., `Sora-nee`, `Icchan`), and translation conventions are injected into prompts automatically.

---

## 🖥️ Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🌐 VN Translation Tool [🎮 D.C.4 Plus Harmony]         🤖 LLM  📚 Bulk  ⚙️ Settings│
├───────────────────┬─────────────────────────────────────────────────────────┤
│ 🔍 Search files.. │ Scenario: dc4_nin20190511b.json           [💾 Save] [📋 Copy]   │
├───────────────────┼────────────────────────────┬────────────────────────────┤
│ 📁 PROLOGUE       │ #1 「諳子」ご飯はちゃんと..│ #1 「Sorane」Is the food.. │
│  ├─ page 1 line 1 │ #2 「諳子」食べ過ぎには..  │ #2 「Sorane」Don't overeat.│
│  └─ page 1 line 2 │ #3 一登                     │ #3 Ichito                  │
│ 📁 ROUTE NINO     │ #4 「了解ー……っと」        │ #4 「Roger that...」       │
└───────────────────┴────────────────────────────┴────────────────────────────┘
```

---

## 📦 System Requirements

* **Operating System**: Windows 10 / 11, macOS, or Linux
* **Python**: Version `3.10` or higher
* **Browser**: Microsoft Edge, Google Chrome, Mozilla Firefox, or Chromium-based browsers

---

## 🚀 Installation & Running

### 1. Clone the Repository
```bash
git clone https://github.com/SakuraSymphonyReTranslation/VN-Translation-Tool.git
cd VN-Translation-Tool
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Application
```bash
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:8000`**

---

## 📖 User Guide (Step-by-Step)

### 1. Project Profile & Directory Setup
1. Press **`Ctrl + ,`** or click the **Settings (⚙️)** gear icon in the top right.
2. Under **Project Profile & Identifier**:
   * Choose an existing profile or click **`+ New Project`** to create a profile for a new game.
   * Provide the **Project Identifier** (e.g., `dc3_platinum_partner`).
3. Under **Directories**, configure the paths:
   * **Original JSON Directory**: Folder containing original Japanese script JSON files.
   * **Translated JSON Directory**: Target folder for game-import JSON files.
   * **Excel Structure File (Optional)**: `.xlsx` file defining scenario flow and categorization.
   * **Project Data Directory**: Working rich save directory (select from dropdown or type custom path).
4. Click **Save Changes**.

---

### 2. Script Navigation & Editing
1. Select a scenario from the sidebar hierarchy.
2. The dialogue rows will render side-by-side:
   * **Left Column**: Original Japanese text (with Furigana annotations if enabled).
   * **Right Column**: Translation input matching your active layer (`Initial`, `Machine`, `Better`, `Best`, `Polished`).
3. Edit dialogue lines directly in the text boxes.
4. Press **`Ctrl + S`** or click **Save** to persist changes.

---

### 3. AI / LLM Translation & Polishing
1. **Start the WebAI Server**:
   * Double-click [`start_webai.bat`](start_webai.bat) in the project root folder.
   * The `WebAI-to-API` server will launch on port `6969`.
2. **Verify Connection**:
   * Navigate to **Settings (⚙️) → LLM Configuration**.
   * Set API URL to `http://localhost:6969/v1` and Model to `gemini-3.0-flash` or `gemini-3.7-flash`.
   * Click **Test Connection** to confirm status shows **Connected!**.
3. **Single Line Translation**:
   * Click the AI action icons next to any individual row to retranslate or polish on the fly.
4. **Batch Translation**:
   * Click **LLM Batch (🤖)** on the top sidebar.
   * Choose mode (*Retranslate* / *Polish*), line range, and click **Start**.

---

### 4. Glossary & Character Consistency
1. Open **Settings (⚙️) → LLM Configuration → Glossary**.
2. Click **`+ Add`** to insert terms:
   * Source (JP): `芳乃 さくら` $\rightarrow$ Target: `Yoshino Sakura` | Info: `Female`
   * Source (JP): `俺` $\rightarrow$ Target: `I / Me` | Info: `First-person pronoun`
3. Export and import glossaries as JSON for cross-project sharing.

---

### 5. Global Search & Find-and-Replace
* **Global Search (`Ctrl + F`)**: Scan across all scenario files with support for Japanese, Romaji, and regular expressions.
* **Find & Replace (`Ctrl + H`)**: Mass replace terminology across scenarios with optional *Preserve Case*.
* **In-File Search (`Ctrl + G`)**: Jump quickly across lines within the currently open scenario.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + S`** | Save current scenario |
| **`Ctrl + F`** | Open Global Search modal |
| **`Ctrl + H`** | Open Find & Replace modal |
| **`Ctrl + G`** | Open In-File Search bar |
| **`Ctrl + ,`** | Open Settings modal |
| **`Ctrl + Shift + S`** | Open Save Copy As dialog |
| **`Esc`** | Close open modals and search overlays |

---

## ❓ Troubleshooting & FAQ

#### Q: Why is the original Japanese column blank?
> **Answer**: Ensure **Original JSON Directory** in Settings points directly to the folder containing raw Japanese `.json` files. Once pointed correctly, opening any file will automatically restore and backfill the Japanese raw text (*auto-heal*).

#### Q: Test Connection fails with "Cannot connect to http://localhost:6969/v1"?
> **Answer**: Ensure `start_webai.bat` is running in a separate terminal window.

#### Q: Browser UI displays cached older scripts?
> **Answer**: Press **`Ctrl + F5`** (or `Ctrl + Shift + R`) to force a hard refresh and bypass stale browser caches.

---

## 📄 License & Credits

* **License**: Released under the [MIT License](LICENSE).
* **Maintainer**: [Sakura Symphony Re; Translation](https://github.com/SakuraSymphonyReTranslation)
* **WebAI-to-API**: Based on upstream runtime by [Amm1rr/WebAI-to-API](https://github.com/Amm1rr/WebAI-to-API).
