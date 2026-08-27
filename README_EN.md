# VN Translation Tool

<div align="center">

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Frontend-Vue.js%203-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
  [![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![Gemini](https://img.shields.io/badge/AI-Gemini%203.7%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://gemini.google.com/)
  [![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

  <br>

  **[🇮🇩 Bahasa Indonesia](README.md)** | **[🇬🇧 English](README_EN.md)**

</div>

**VN Translation Tool** is a modern local web application designed to streamline the translation, editing, polishing, and localization workflow for **Visual Novel (VN)** scripts (including Circus / D.C. Series engines, LucaSystem, and JSON-based game formats).

The tool integrates a clean side-by-side editor, automatic Furigana parsing, intelligent glossary injection, Romaji & Regex search, and a **Hybrid AI Engine** (supporting direct native connections to **Google Gemini Web 3.7** via browser cookies without requiring external servers, as well as **Local LLMs / OpenAI API**).

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [UI Layout](#-ui-layout)
- [System Requirements](#-system-requirements)
- [Installation & Getting Started](#-installation--getting-started)
- [Step-by-Step Guide](#-step-by-step-guide)
  - [1. Project Setup & Game Directories](#1-project-setup--game-directories)
  - [2. Script Navigation & Translation](#2-script-navigation--translation)
  - [3. AI-Powered Translation (Hybrid: Direct Gemini Web & Custom LLM)](#3-ai-powered-translation-hybrid-direct-gemini-web--custom-llm)
  - [4. Glossary & Character Names](#4-glossary--character-names)
  - [5. Global Search & Find-and-Replace](#5-global-search--find-and-replace)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [License & Contributions](#-license--contributions)

---

## ✨ Key Features

### 🎮 1. Multi-Project Management & Cache Isolation
* **Multiple Game Profiles**: Seamlessly switch between projects (e.g. *D.C.4 Plus Harmony*, *Da Capo 4*, *D.C.III Platinum Partner*, *D.C.III Dream Days*, etc.).
* **Independent Cache Folders (`project_data/<slug>`)**: Keeps progress status, rich saves, and translation cache completely isolated between different games.
* **Auto-Sync & Custom Paths**: Easily select existing cache folders or generate new ones dynamically from Settings.

### 📝 2. Modern Side-by-Side Script Editor
* **Raw JP vs Translated Side-by-Side**: Clear contextual alignment for rapid reading and editing.
* **5 Translation Tiers**:
  * `Initial` — Original base translation from game extract.
  * `Machine` — Raw machine translation (MTL).
  * `Better` — First draft improvements.
  * `Best` — Filtered, high-quality revisions.
  * `Polished` — Final localized prose ready for in-game release.
* **Smart Export Priority**: Automatically exports the highest available tier (`Polished` > `Best` > `Better` > `Initial` > `Machine`) when saving to game JSON.
* **Split View**: Side-by-side comparison of any two tiers (e.g. `Initial` vs `Polished`).
* **Auto-Heal & Auto-Sync**: Automatically repairs and re-populates missing Japanese source text if directory paths were misconfigured.

### 📖 3. Furigana Parser & Smart Romaji Search
* **Kanji Furigana Generation**: Built-in MeCab / UniDic support for real-time furigana ruby display over kanji.
* **Romaji-to-Japanese Matching**: Typing `arisu` finds `有里栖`, `ありす`, and `アリス`.
* **Regex & In-File Search**: Filter lines using regular expressions and jump directly to matches.

### 🤖 4. Hybrid AI Engine (Direct Gemini Web & Custom LLM)
* **Mode 1: Gemini Web Direct API (Native & Zero-Server Setup)**:
  * Connects directly to **Google Gemini Web** using browser session cookies (`__Secure-1PSID` & `__Secure-1PSIDTS`).
  * **No external local server (`start_webai.bat`) required**.
  * Features **Auto-Extract** (extracts cookies from Chrome/Edge/Firefox) and **Launch Login** (opens Google Gemini in browser).
* **Mode 2: Custom LLM / OpenAI API / WebAI Server**:
  * Fully compatible with standard OpenAI endpoints (`/v1/chat/completions`) such as **Ollama**, **LM Studio**, **vLLM**, or local **WebAI-to-API** on port `6969`.
<!-- GEMINI_MODELS_START -->
* **Latest Gemini Model Lineup**:
  * `gemini-3.7-flash` (3.7 Flash — All-around help / Default)
  * `gemini-3.7-flash-thinking` (Extended thinking — Complex problem solving)
  * `gemini-3.5-flash-lite` (3.5 Flash-Lite — Fastest answers)
  * `gemini-3.1-pro` (3.1 Pro — Advanced reasoning)
<!-- GEMINI_MODELS_END -->
* **🔗 Summary Chaining (Memori Estafet)**:
  * Chains running story memory across consecutive translation batches.
  * Prevents AI hallucinations and maintains narrative continuity, emotional tone, and character relationships across scene transitions.
  * Includes editable *Current Summary* and custom *Summary Prompt* controls.
* **💖 Adult / 18+ Visual Novel Support (H-Scene Safe & Uncensored)**:
  * Tailored with specialized fictional Visual Novel localization system directives.
  * Faithfully translates dramatic, romantic, intimate, and adult (H-scene) dialogues and Japanese vocal onomatopoeia (e.g., gasps, moans, breaths) with 100% emotional fidelity without censorship, filtering, or refusals.
* **Dynamic `🔄 Fetch Models`**: Fetch all available active models dynamically from your AI endpoint.
* **Batch Translation & Polishing**: Translate or polish full scenarios in bulk with real-time SSE progress streaming.
* **Automatic Glossary Injection**: Preserves character names, genders, and honorifics consistently across AI calls.
* **Automated GitHub Actions Sync**: Includes a daily automated GitHub Actions workflow to update the upstream WebAI module safely without breaking custom integrations.

---

## 🖥️ UI Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🌐 VN Translation Tool [🎮 D.C.4 Plus Harmony]         🤖 LLM  📚 Bulk  ⚙️ Settings│
├───────────────────┬─────────────────────────────────────────────────────────┤
│ 🔍 Search scenario│ Scenario: dc4_nin20190511b.json           [💾 Save] [📋 Copy]   │
├───────────────────┼────────────────────────────┬────────────────────────────┤
│ 📁 PROLOGUE       │ #1 「諳子」ご飯はちゃんと..│ #1 「Sorane」Eat your meals│
│  ├─ page 1 line 1 │ #2 「諳子」食べ過ぎには..  │ #2 「Sorane」Don't overeat │
│  └─ page 1 line 2 │ #3 一登                     │ #3 Ichito                  │
│ 📁 ROUTE NINO     │ #4 「了解ー……っと」        │ #4 「All right... got it」 │
└───────────────────┴────────────────────────────┴────────────────────────────┘
```

---

## 📦 System Requirements

* **Operating System**: Windows 10 / 11, macOS, or Linux
* **Python**: Version `3.10` or higher
* **Browser**: Google Chrome, Microsoft Edge, Mozilla Firefox, or Chromium-based browsers

---

## 🚀 Installation & Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/SakuraSymphonyReTranslation/VN-Translation-Tool.git
cd VN-Translation-Tool
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 📖 Step-by-Step Guide

### 1. Project Setup & Game Directories
1. Press **`Ctrl + ,`** or click the **Settings (⚙️)** gear icon in the top header.
2. In **Project Profile & Identifier**:
   * Choose an existing profile (e.g. `D.C.4 Plus Harmony`) or click **`+ New Project`**.
   * Specify the **Project Identifier** (e.g., `dc3_platinum_partner`).
3. In **Directories**, set your target game folders:
   * **Original JSON Directory**: Folder containing raw Japanese `.json` files.
   * **Translated JSON Directory**: Target output folder for translated `.json` files.
   * **Excel Structure File (Optional)**: `.xlsx` scenario index.
   * **Project Data Directory**: Cache folder name for the project.
4. Click **Save Changes**.

---

### 2. Script Navigation & Translation
1. Select any scenario from the left sidebar.
2. The scenario will display side-by-side:
   * **Left Column**: Original Japanese script (with Furigana if enabled).
   * **Right Column**: Translation input area for the active tier (`Initial`, `Machine`, `Better`, `Best`, `Polished`).
3. Edit any line directly in the table.
4. Press **`Ctrl + S`** or click **Save** to write changes to disk.

---

### 3. AI-Powered Translation (Hybrid Mode)

#### Option A: Direct Google Gemini Web (Recommended - Zero Server Setup)
1. Open **Settings (`Ctrl + ,`) → LLM Configuration**.
2. Select **`Gemini Web (Direct API)`**.
3. Under **Gemini Web Token & Cookies**:
   * Click **`Auto-Extract`** to grab cookies automatically from your browser, **OR**:
   * Click **`Edit Cookies`** and paste `__Secure-1PSID` & `__Secure-1PSIDTS` from DevTools (`gemini.google.com` > F12 > Application > Cookies), then click **`Save Cookies`**.
4. Click **Test Connection** — status will show 🟢 **Connected**!

#### Option B: Custom LLM / OpenAI API / WebAI Server
1. Open **Settings (`Ctrl + ,`) → LLM Configuration**.
2. Select **`Custom LLM / OpenAI API`**.
3. Set your **API Base URL** (e.g., `http://localhost:11434/v1` for Ollama or `http://localhost:6969/v1` for WebAI-to-API).
4. Click **Test Connection**.

#### Translating Text:
* **Per Row**: Click the robot/lightning icon next to any row to retranslate or polish that line.
* **Bulk Translation**: Click **LLM Batch (🤖)** in the sidebar header, select target range, and click **Start**.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + S`** | Save current scenario |
| **`Ctrl + F`** | Open Global Search modal |
| **`Ctrl + H`** | Open Find & Replace modal |
| **`Ctrl + G`** | Open In-File Search bar |
| **`Ctrl + ,`** | Open Settings modal |
| **`Ctrl + Shift + S`** | Save Copy As |
| **`Esc`** | Close any active modal or drawer |

---

## 🤝 License & Contributions

Licensed under the **MIT License**. Contributions, issues, and feature requests are welcome at [SakuraSymphonyReTranslation/VN-Translation-Tool](https://github.com/SakuraSymphonyReTranslation/VN-Translation-Tool).
