const { createApp, ref, computed, onMounted, watch } = Vue;

createApp({
    setup() {
        // Data
        const scenarios = ref({});
        const activeFile = ref(null);
        const translationData = ref([]);
        const searchQuery = ref("");
        const isLoading = ref(false);
        const isSaving = ref(false);
        const hasUnsavedChanges = ref(false);
        const expandedRoutes = ref({});
        const config = ref({});
        const projectList = ref([]);
        const activeProjectId = ref('dc4_plus_harmony');
        const currentProjectIdentifier = ref('dc4_plus_harmony');
        const currentProjectName = ref('D.C.4 Plus Harmony');
        const showNewProjectModal = ref(false);
        const newProjIdentifier = ref('');
        const newProjName = ref('');
        const availableCacheFolders = ref([]);
        const isRefreshingCaches = ref(false);
        const isIndexingAll = ref(false);
        const indexAllMsg = ref('');
        const webaiStatus = ref({ local_version: '0.6.0', folder: '', folder_exists: true });
        const webaiUpdateInfo = ref(null);
        const isCheckingWebaiUpdate = ref(false);
        const isUpdatingWebai = ref(false);
        const geminiCookies = ref({ psid: '', psidts: '', browser: 'chrome', has_cookies: false });
        const showCookieFields = ref(false);
        const isExtractingCookies = ref(false);
        const cookieMsg = ref('');
        const webaiUpdateMsg = ref('');
        let editRevision = 0;
        let activeSavePromise = null;

        // UI State
        const activeTab = ref('initial'); // initial, machine, better, best
        const showSplitView = ref(false);
        const secondaryTab = ref('machine');

        const showSettings = ref(false);
        const showLlmConfig = ref(true);
        const fetchedModels = ref([]);
        const isFetchingModels = ref(false);
        const showSearchModal = ref(false);
        const globalSearchQuery = ref("");
        const isRegexSearch = ref(false);
        const searchInInitialOnly = ref(false);
        const searchResults = ref([]);
        const searchRomaji = ref(false); // Toggle for global romaji search

        const isSearching = ref(false);
        const hasSearched = ref(false);
        const showSaveAs = ref(false);
        const searchResultCount = ref(0);

        // Replace & Case options
        const globalReplaceQuery = ref("");
        const matchCase = ref(false);
        const preserveCase = ref(false);
        const isReplacing = ref(false);
        const replaceResultMsg = ref("");
        const searchModalTab = ref("search");

        // Theme Color
        const themePresets = [
            { name: 'Blue', hex: '#3B82F6', bg: '#1E293B' },
            { name: 'Cyan', hex: '#06B6D4', bg: '#0F1D2B' },
            { name: 'Teal', hex: '#14B8A6', bg: '#0F1F1D' },
            { name: 'Green', hex: '#22C55E', bg: '#0F1F15' },
            { name: 'Lime', hex: '#84CC16', bg: '#171F0F' },
            { name: 'Yellow', hex: '#EAB308', bg: '#1F1C0F' },
            { name: 'Orange', hex: '#F97316', bg: '#1F170F' },
            { name: 'Red', hex: '#EF4444', bg: '#1F0F0F' },
            { name: 'Rose', hex: '#F43F5E', bg: '#1F0F14' },
            { name: 'Pink', hex: '#EC4899', bg: '#1F0F18' },
            { name: 'Purple', hex: '#A855F7', bg: '#180F1F' },
            { name: 'Violet', hex: '#8B5CF6', bg: '#150F1F' },
        ];
        const savedTheme = localStorage.getItem('dc4_theme_color') || '#3B82F6';
        const themeColor = ref(savedTheme);
        const customThemeColor = ref(savedTheme);
        const showThemePicker = ref(false);

        // Secondary Color
        const savedSecondary = localStorage.getItem('dc4_secondary_color') || '#3B82F6';
        const secondaryColor = ref(savedSecondary);
        const customSecondaryColor = ref(savedSecondary);

        const applyThemeColor = (hex) => {
            themeColor.value = hex;
            customThemeColor.value = hex;
            localStorage.setItem('dc4_theme_color', hex);

            // Convert hex to RGB for CSS custom properties
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);

            // Find matching preset for background, or generate one
            const preset = themePresets.find(p => p.hex === hex);
            const bgHex = preset ? preset.bg : generateDarkBg(r, g, b);
            const br = parseInt(bgHex.slice(1, 3), 16);
            const bg = parseInt(bgHex.slice(3, 5), 16);
            const bb = parseInt(bgHex.slice(5, 7), 16);

            const root = document.documentElement;
            root.style.setProperty('--theme-color', hex);
            root.style.setProperty('--theme-rgb', `${r}, ${g}, ${b}`);
            root.style.setProperty('--theme-bg', bgHex);
            root.style.setProperty('--theme-bg-rgb', `${br}, ${bg}, ${bb}`);

            // Apply background colors dynamically
            document.body.style.backgroundColor = bgHex;

            // Generate lighter shade for sidebar/top-bar
            const lr = Math.min(255, Math.round(br * 1.4 + r * 0.05));
            const lg = Math.min(255, Math.round(bg * 1.4 + g * 0.05));
            const lb = Math.min(255, Math.round(bb * 1.4 + b * 0.05));
            const sidebarBg = `rgb(${lr}, ${lg}, ${lb})`;
            root.style.setProperty('--theme-sidebar-bg', sidebarBg);

            // Generate darker shade for editor area
            const dr2 = Math.max(0, Math.round(br * 0.7));
            const dg2 = Math.max(0, Math.round(bg * 0.7));
            const db2 = Math.max(0, Math.round(bb * 0.7));
            const editorBg = `rgb(${dr2}, ${dg2}, ${db2})`;
            root.style.setProperty('--theme-editor-bg', editorBg);

            // Border color
            const bdr = Math.min(255, Math.round(lr * 1.3));
            const bdg = Math.min(255, Math.round(lg * 1.3));
            const bdb = Math.min(255, Math.round(lb * 1.3));
            root.style.setProperty('--theme-border', `rgb(${bdr}, ${bdg}, ${bdb})`);

            // Hover color (slightly lighter than sidebar)
            const hr = Math.min(255, Math.round(lr * 1.15));
            const hg = Math.min(255, Math.round(lg * 1.15));
            const hb = Math.min(255, Math.round(lb * 1.15));
            root.style.setProperty('--theme-hover', `rgb(${hr}, ${hg}, ${hb})`);
        };

        const applySecondaryColor = (hex) => {
            secondaryColor.value = hex;
            customSecondaryColor.value = hex;
            localStorage.setItem('dc4_secondary_color', hex);

            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);

            const root = document.documentElement;
            root.style.setProperty('--theme-secondary', hex);
            root.style.setProperty('--theme-secondary-rgb', `${r}, ${g}, ${b}`);
        };

        const selectSecondaryPreset = (preset) => {
            applySecondaryColor(preset.hex);
        };

        const onCustomSecondaryChange = (e) => {
            applySecondaryColor(e.target.value);
        };

        const generateDarkBg = (r, g, b) => {
            // Create a subtle dark background tinted by the accent color
            const dr = Math.round(15 + (r / 255) * 16);
            const dg = Math.round(15 + (g / 255) * 16);
            const db = Math.round(15 + (b / 255) * 16);
            return `#${dr.toString(16).padStart(2, '0')}${dg.toString(16).padStart(2, '0')}${db.toString(16).padStart(2, '0')}`;
        };

        const selectThemePreset = (preset) => {
            applyThemeColor(preset.hex);
        };

        const onCustomColorChange = (e) => {
            applyThemeColor(e.target.value);
        };

        // Close theme picker on outside click
        document.addEventListener('click', (e) => {
            if (showThemePicker.value && !e.target.closest('[data-theme-picker]')) {
                showThemePicker.value = false;
            }
            if (showWallpaperPicker.value && !e.target.closest('[data-wallpaper-picker]')) {
                showWallpaperPicker.value = false;
            }
        });

        // Wallpaper
        const wallpapers = ref([]);
        const activeWallpaper = ref(localStorage.getItem('dc4_wallpaper') || '');
        const showWallpaperPicker = ref(false);

        const loadWallpapers = async () => {
            try {
                const res = await fetch('/api/wallpapers');
                const data = await res.json();
                wallpapers.value = data.wallpapers || [];
            } catch (e) {
                console.error("Failed to load wallpapers", e);
            }
        };

        const applyWallpaper = (filename) => {
            activeWallpaper.value = filename;
            localStorage.setItem('dc4_wallpaper', filename);

            if (filename) {
                document.body.classList.add('wallpaper-active');
            } else {
                document.body.classList.remove('wallpaper-active');
            }
        };

        const selectWallpaper = (filename) => {
            applyWallpaper(filename);
        };

        const clearWallpaper = () => {
            applyWallpaper('');
        };

        // Scenario Mode Filter
        const availableModes = ref([]);
        const selectedModes = ref([]);
        const firstMatchOnly = ref(false);

        const saveAsFilename = ref("");

        // Bulk State
        const showBulkModal = ref(false);
        const bulkFiles = ref([]);
        const selectedBulkFiles = ref([]);
        const isScanning = ref(false);
        const isProcessingBulk = ref(false);
        const bulkSuffix = ref("_v1");

        // LLM State
        const showLlmBatchModal = ref(false);
        const llmBatchMode = ref('retranslate');
        const llmBatchSourceTab = ref('initial');
        const llmBatchRange = ref('all');
        const llmBatchRunning = ref(false);
        const llmBatchProgress = ref({ current: 0, total: 0 });
        const llmBatchCurrentItem = ref(null);
        const llmBatchErrors = ref([]);
        const llmTestLoading = ref(false);
        const llmTestResult = ref(null);
        let llmBatchAbortController = null;

        // Resizable Columns & Preview
        const originalColumnWidth = ref(parseInt(localStorage.getItem('originalColumnWidth')) || 40);
        const selectedRowId = ref(null);
        const selectedColumn = ref(null); // 'original' or 'translation'
        const showPreview = ref(true);

        // In-File Search State
        const showInFileSearch = ref(false);
        const inFileSearchQuery = ref('');
        const inFileSearchResults = ref([]);
        const inFileSearchIndex = ref(-1);
        const inFileHighlightId = ref(null);
        const inFileSearchRomaji = ref(false);





        // Furigana State
        const showFurigana = ref(false);
        const furiganaMode = ref('hiragana'); // hiragana, katakana, romaji
        const isFetchingFurigana = ref(false);

        // Virtual Scrolling
        const ROW_HEIGHT = 58; // Approximate height of each row in pixels
        const VISIBLE_BUFFER = 15; // Extra rows above/below viewport
        const scrollTop = ref(0);
        const containerHeight = ref(800);

        const visibleRange = computed(() => {
            const totalRows = translationData.value.length;
            if (totalRows === 0) return { start: 0, end: 0 };

            // Use fallback height if container not yet sized
            const height = containerHeight.value > 0 ? containerHeight.value : 800;
            const startRow = Math.max(0, Math.floor(scrollTop.value / ROW_HEIGHT) - VISIBLE_BUFFER);
            const visibleCount = Math.ceil(height / ROW_HEIGHT) + (VISIBLE_BUFFER * 2);
            const endRow = Math.min(totalRows, startRow + visibleCount);

            return { start: startRow, end: endRow };
        });

        const visibleRows = computed(() => {
            const { start, end } = visibleRange.value;
            return translationData.value.slice(start, end);
        });

        const virtualScrollTopPad = computed(() => {
            return visibleRange.value.start * ROW_HEIGHT;
        });

        const virtualScrollBottomPad = computed(() => {
            const totalRows = translationData.value.length;
            return Math.max(0, (totalRows - visibleRange.value.end) * ROW_HEIGHT);
        });

        let _scrollRAF = null;
        const onEditorScroll = (e) => {
            if (_scrollRAF) return; // Skip if already queued
            _scrollRAF = requestAnimationFrame(() => {
                scrollTop.value = e.target.scrollTop;
                containerHeight.value = e.target.clientHeight;
                _scrollRAF = null;
            });
        };

        // Computed: Filtered Scenarios
        const filteredRoutes = computed(() => {
            if (!searchQuery.value) return scenarios.value;

            const result = {};
            const query = searchQuery.value.toLowerCase();

            for (const [route, files] of Object.entries(scenarios.value)) {
                const filteredFiles = files.filter(f =>
                    f.file.toLowerCase().includes(query) ||
                    f.part.toLowerCase().includes(query) ||
                    f.segment.toLowerCase().includes(query)
                );

                if (filteredFiles.length > 0) {
                    result[route] = filteredFiles;
                    expandedRoutes.value[route] = true;
                }
            }
            return result;
        });

        // Toggle route accordion
        const toggleRoute = (route) => {
            expandedRoutes.value[route] = !expandedRoutes.value[route];
        };

        // Cache Folders Scanning & Sync
        const fetchCacheFolders = async () => {
            isRefreshingCaches.value = true;
            try {
                const res = await fetch('/api/project-data-folders');
                if (res.ok) {
                    availableCacheFolders.value = await res.json();
                }
            } catch (e) {
                console.error("Failed to fetch cache folders", e);
            } finally {
                isRefreshingCaches.value = false;
            }
        };

        const onCacheFolderSelect = (e) => {
            const selected = e.target.value;
            if (selected) {
                config.value.project_data_dir = selected;
            }
        };

        // WebAI-to-API Update Management
        const fetchWebaiStatus = async () => {
            try {
                const res = await fetch('/api/llm/webai/status');
                if (res.ok) {
                    webaiStatus.value = await res.json();
                }
            } catch (e) {
                console.error("Failed to fetch WebAI status", e);
            }
        };

        const checkWebaiUpdate = async () => {
            isCheckingWebaiUpdate.value = true;
            webaiUpdateMsg.value = '';
            try {
                const res = await fetch('/api/llm/webai/check-update');
                if (res.ok) {
                    const data = await res.json();
                    webaiUpdateInfo.value = data;
                    if (data.local_version) {
                        webaiStatus.value.local_version = data.local_version;
                    }
                    if (data.has_update) {
                        webaiUpdateMsg.value = `New version ${data.latest_version} available! (${data.release_name})`;
                    } else if (data.status === 'success') {
                        webaiUpdateMsg.value = `WebAI-to-API is already up to date (v${data.local_version}).`;
                    } else {
                        webaiUpdateMsg.value = `Notice: ${data.error || 'Could not verify remote version.'}`;
                    }
                }
            } catch (e) {
                webaiUpdateMsg.value = `Failed to check update: ${e.message}`;
            } finally {
                isCheckingWebaiUpdate.value = false;
            }
        };

        const performWebaiUpdate = async () => {
            if (!confirm(`Are you sure you want to update WebAI-to-API to ${webaiUpdateInfo.value?.latest_version || 'latest'}?\n\nUser settings (config.conf) will be preserved.`)) {
                return;
            }
            isUpdatingWebai.value = true;
            webaiUpdateMsg.value = 'Downloading and applying update from GitHub...';
            try {
                const res = await fetch('/api/llm/webai/update', { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    webaiUpdateMsg.value = data.message;
                    if (data.version) {
                        webaiStatus.value.local_version = data.version;
                    }
                    await fetchWebaiStatus();
                    await checkWebaiUpdate();
                    alert(data.message);
                } else {
                    webaiUpdateMsg.value = `Error updating: ${data.message}`;
                    alert("Update failed: " + data.message);
                }
            } catch (e) {
                webaiUpdateMsg.value = `Update failed: ${e.message}`;
                alert("Update error: " + e.message);
            } finally {
                isUpdatingWebai.value = false;
            }
        };

        // Gemini Web Cookies & Auth
        const fetchCookies = async () => {
            try {
                const res = await fetch('/api/llm/webai/cookies');
                if (res.ok) {
                    geminiCookies.value = await res.json();
                }
            } catch (e) {
                console.error("Failed to load Gemini cookies", e);
            }
        };

        const saveCookies = async () => {
            try {
                const res = await fetch('/api/llm/webai/cookies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(geminiCookies.value)
                });
                const data = await res.json();
                const msg = data.message || data.detail || (res.ok ? "Cookies saved successfully!" : "Error saving cookies");
                cookieMsg.value = msg;
                if (res.ok) {
                    geminiCookies.value.has_cookies = Boolean(geminiCookies.value.psid && geminiCookies.value.psidts);
                    alert(msg);
                } else {
                    alert("Notice (" + res.status + "): " + msg + "\n\nPastikan Anda me-restart server 'py app.py' di terminal agar rute baru aktif.");
                }
            } catch (e) {
                cookieMsg.value = "Failed to save: " + e.message;
                alert("Save error: " + e.message);
            }
        };

        const autoExtractCookies = async () => {
            isExtractingCookies.value = true;
            cookieMsg.value = 'Extracting cookies from installed browsers...';
            try {
                const res = await fetch('/api/llm/webai/extract-cookies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ browser: geminiCookies.value.browser || 'chrome' })
                });
                const data = await res.json();
                const msg = data.message || data.detail || "Cookie extraction finished.";
                cookieMsg.value = msg;
                if (res.ok && data.status === 'success') {
                    await fetchCookies();
                    alert(msg);
                } else {
                    alert(msg);
                }
            } catch (e) {
                cookieMsg.value = "Extraction error: " + e.message;
                alert("Extraction error: " + e.message);
            } finally {
                isExtractingCookies.value = false;
            }
        };

        const launchWebLogin = async () => {
            try {
                const res = await fetch('/api/llm/webai/launch-login', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });
                const data = await res.json();
                const msg = data.message || data.detail || "Opening Gemini Web...";
                cookieMsg.value = msg;
                if (res.ok) {
                    alert(msg);
                } else {
                    window.open("https://gemini.google.com", "_blank");
                    alert("Membuka gemini.google.com di browser baru! Silakan login akun Google Anda, lalu salin token __Secure-1PSID & __Secure-1PSIDTS.");
                }
            } catch (e) {
                window.open("https://gemini.google.com", "_blank");
                cookieMsg.value = "Membuka gemini.google.com di tab browser.";
                alert("Membuka gemini.google.com di tab browser baru! Silakan login.");
            }
        };

        // Summary Chaining
        const clearSummary = async () => {
            config.value.current_story_summary = '';
            try {
                await fetch('/api/llm/summary/clear', { method: 'POST' });
            } catch (e) {
                console.error("Failed to clear summary", e);
            }
        };

        const resetSummaryPrompt = () => {
            config.value.summary_chaining_prompt = "If the <summary> section is provided above, use this running story context to maintain narrative continuity, character voices, emotional tone, and terminology consistency across translation batches.\n\nAfter completing the translations, generate an updated running story summary (in {{targetLang}}) capturing:\n- Current scene, location, and atmosphere\n- Active characters and their interactions / emotional state\n- Key plot developments, decisions, or core topics discussed\n\nYour summary output MUST be enclosed in <summary>...</summary> tags at the very end of your response, INSIDE the ```plaintext block.";
        };

        // Project Management
        const fetchProjects = async () => {
            try {
                const res = await fetch('/api/projects');
                if (res.ok) {
                    const data = await res.json();
                    activeProjectId.value = data.active_project || 'dc4_plus_harmony';
                    projectList.value = data.projects || [];
                    const activeP = projectList.value.find(p => p.id === activeProjectId.value);
                    if (activeP) {
                        currentProjectIdentifier.value = activeP.identifier || activeP.id;
                        currentProjectName.value = activeP.name || activeP.id;
                    }
                }
            } catch (e) {
                console.error("Failed to load projects", e);
            }
        };

        const onProjectSelectChange = async () => {
            try {
                // Immediately update local UI fields based on selected project
                const activeP = projectList.value.find(p => p.id === activeProjectId.value);
                if (activeP) {
                    currentProjectIdentifier.value = activeP.identifier || activeP.id;
                    currentProjectName.value = activeP.name || activeP.id;
                    config.value.original_dir = activeP.original_dir || '';
                    config.value.translated_dir = activeP.translated_dir || '';
                    config.value.excel_path = activeP.excel_path || '';
                    config.value.project_data_dir = activeP.project_data_dir || `project_data\\${activeP.identifier}`;
                }

                const res = await fetch('/api/projects/switch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_id: activeProjectId.value })
                });
                if (res.ok) {
                    const data = await res.json();
                    config.value = data.config;
                    await fetchProjects();
                    await fetchCacheFolders();
                    activeFile.value = null;
                    translationData.value = [];
                    await loadScenarios();
                    await loadScenarioModes();
                }
            } catch (e) {
                console.error("Failed to switch project", e);
            }
        };

        const onIdentifierInput = () => {
            const clean = currentProjectIdentifier.value.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
            currentProjectIdentifier.value = clean;
            config.value.active_project = clean;
            if (!config.value.project_data_dir || config.value.project_data_dir.startsWith('project_data\\')) {
                config.value.project_data_dir = `project_data\\${clean}`;
            }
        };

        const onProjectNameInput = () => {
            config.value.project_name = currentProjectName.value;
        };

        const openNewProjectModal = () => {
            newProjIdentifier.value = '';
            newProjName.value = '';
            showNewProjectModal.value = true;
        };

        const confirmCreateProject = async () => {
            const cleanId = (newProjIdentifier.value || 'new_project').trim().toLowerCase().replace(/[^a-z0-9_-]/g, '_');
            const name = (newProjName.value || cleanId).trim();
            
            try {
                const res = await fetch('/api/projects/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        project_id: cleanId,
                        identifier: cleanId,
                        name: name,
                        original_dir: '',
                        translated_dir: '',
                        excel_path: '',
                        project_data_dir: `project_data\\${cleanId}`
                    })
                });
                if (res.ok) {
                    showNewProjectModal.value = false;
                    await fetchProjects();
                    activeProjectId.value = cleanId;
                    await onProjectSelectChange();
                }
            } catch (e) {
                alert("Failed to create project: " + e.message);
            }
        };

        const deleteCurrentProject = async () => {
            if (!confirm(`Are you sure you want to delete project profile "${currentProjectName.value}" (${activeProjectId.value})?\n\nNote: Cached files in project_data folder will NOT be deleted.`)) {
                return;
            }
            try {
                const res = await fetch('/api/projects/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_id: activeProjectId.value })
                });
                if (res.ok) {
                    await fetchProjects();
                    await onProjectSelectChange();
                }
            } catch (e) {
                alert("Failed to delete project: " + e.message);
            }
        };

        // Load Config
        const loadConfig = async () => {
            try {
                const res = await fetch('/api/config');
                config.value = await res.json();
            } catch (e) {
                console.error("Failed to load config", e);
            }
        };

        // Save Config
        const handleSaveConfig = () => {
            // Do the async work
            (async () => {
                try {
                    // console.log("Config value:", config.value);

                    const res = await fetch('/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config.value)
                    });

                    if (!res.ok) {
                        const errText = await res.text();
                        throw new Error("Server: " + res.status + " " + errText);
                    }

                    const data = await res.json();
                    if (data.status === 'success') {
                        showSettings.value = false;
                        alert("Settings saved! Page will reload.");
                        window.location.reload();
                    } else {
                        throw new Error("API Status: " + data.status);
                    }
                } catch (e) {
                    alert("Error saving: " + e.message);
                    console.error(e);
                }
            })();
        };

        // Expose to window for fallback (optional, keeping for safety but not using in HTML)
        window.globalSaveConfig = handleSaveConfig;

        // Global Search
        const loadScenarioModes = async () => {
            try {
                const res = await fetch('/api/scenario-modes');
                const data = await res.json();
                availableModes.value = data.modes;
                selectedModes.value = [...data.modes]; // Select all by default
            } catch (e) {
                console.error("Failed to load scenario modes", e);
            }
        };

        const toggleAllModes = () => {
            if (selectedModes.value.length === availableModes.value.length) {
                selectedModes.value = [];
            } else {
                selectedModes.value = [...availableModes.value];
            }
        };

        const performGlobalSearch = async () => {
            if (!globalSearchQuery.value) return;
            isSearching.value = true;
            hasSearched.value = true;
            searchResults.value = [];

            try {
                const payload = {
                    query: globalSearchQuery.value,
                    is_regex: isRegexSearch.value,
                    search_in_initial_only: searchInInitialOnly.value,

                    first_match_only: firstMatchOnly.value,
                    match_case: matchCase.value,
                    search_romaji: searchRomaji.value
                };

                // Only add scenario_modes if not all modes are selected
                if (selectedModes.value.length < availableModes.value.length && selectedModes.value.length > 0) {
                    payload.scenario_modes = selectedModes.value;
                }

                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const data = await response.json();
                    searchResults.value = data.results;
                    searchResultCount.value = data.count || data.results.length;
                }
            } catch (error) {
                console.error("Search error:", error);
            } finally {
                isSearching.value = false;
            }
        };

        const performGlobalReplace = async () => {
            if (!globalSearchQuery.value) return;

            const confirmMsg = `Replace all occurrences of "${globalSearchQuery.value}" with "${globalReplaceQuery.value}"?\n\nThis will modify project files directly. This action cannot be undone.`;
            if (!confirm(confirmMsg)) return;

            isReplacing.value = true;
            replaceResultMsg.value = "";

            try {
                const payload = {
                    query: globalSearchQuery.value,
                    replacement: globalReplaceQuery.value,
                    is_regex: isRegexSearch.value,
                    match_case: matchCase.value,
                    preserve_case: preserveCase.value,
                    search_in_initial_only: searchInInitialOnly.value,
                    search_romaji: searchRomaji.value
                };

                // Only add scenario_modes if not all modes are selected
                if (selectedModes.value.length < availableModes.value.length && selectedModes.value.length > 0) {
                    payload.scenario_modes = selectedModes.value;
                }

                const response = await fetch('/api/replace', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const data = await response.json();
                    replaceResultMsg.value = `Replaced ${data.replaced_count} occurrences in ${data.file_count} files`;

                    // Re-run search to update results
                    await performGlobalSearch();

                    // Reload current file if one is open (it may have been modified)
                    if (activeFile.value) {
                        const currentFile = activeFile.value;
                        activeFile.value = null; // Force reload
                        await selectScenario(currentFile);
                    }
                } else {
                    replaceResultMsg.value = "Replace failed!";
                }
            } catch (error) {
                console.error("Replace error:", error);
                replaceResultMsg.value = "Replace error: " + error.message;
            } finally {
                isReplacing.value = false;
            }
        };

        const navigateToResult = async (result) => {
            // Find the file object in our current list
            let targetFile = null;
            // Iterate routes to find file (Check FULL list, not filtered)
            for (const route in scenarios.value) {
                const found = scenarios.value[route].find(f => f.file === result.file);
                if (found) {
                    targetFile = found;
                    break;
                }
            }

            // If not found in Excel structure (e.g. it's a _copy file), create a virtual entry
            if (!targetFile) {
                targetFile = {
                    file: result.file,
                    segment: result.file,
                    part: "Search Result",
                    mode: "N/A"
                };
            }

            if (targetFile) {
                showSearchModal.value = false;
                await selectScenario(targetFile);

                // Scroll to the target row using virtual scroll position
                setTimeout(() => {
                    const editorEl = document.querySelector('.editor-container');
                    if (editorEl) {
                        // Scroll to the row's calculated position
                        const targetScrollTop = result.id * ROW_HEIGHT - (editorEl.clientHeight / 2);
                        editorEl.scrollTo({ top: Math.max(0, targetScrollTop), behavior: 'smooth' });

                        // Wait for scroll + render, then highlight
                        setTimeout(() => {
                            const rows = document.querySelectorAll('.translation-row');
                            for (const row of rows) {
                                // Find the row by its displayed ID
                                const idEl = row.querySelector('.col-id');
                                if (idEl && idEl.textContent.trim() === `#${result.id + 1}`) {
                                    // Remove any existing highlights
                                    document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                                        el.classList.remove('in-file-match-highlight');
                                    });
                                    
                                    // Add the highlight class
                                    row.classList.add('in-file-match-highlight');
                                    
                                    // Store the highlighted row ID so we can remove it later
                                    inFileHighlightId.value = result.id;
                                    break;
                                }
                            }
                        }, 600);
                    }
                }, 300);
            }
        };

        // Load scenarios from API
        const loadScenarios = async () => {
            try {
                const res = await fetch('/api/scenarios');
                scenarios.value = await res.json();
                for (const route of Object.keys(scenarios.value)) {
                    expandedRoutes.value[route] = true;
                }
            } catch (e) {
                console.error("Failed to load scenarios", e);
            }
        };

        // Select a scenario
        const selectScenario = async (fileEntry) => {
            if (activeFile.value && activeFile.value.file === fileEntry.file) return;

            if (activeFile.value && hasUnsavedChanges.value) {
                const saved = await saveTranslation();
                if (!saved) return;
            }

            // Clear any highlights when switching files
            document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                el.classList.remove('in-file-match-highlight');
            });
            inFileHighlightId.value = null;

            activeFile.value = fileEntry;
            isLoading.value = true;
            translationData.value = [];

            try {
                const res = await fetch(`/api/translation/${fileEntry.file}`);
                const data = await res.json();
                translationData.value = data;
                ensurePolishedColumn();
                hasUnsavedChanges.value = false;
            } catch (e) {
                console.error("Failed to load translation", e);
            } finally {
                isLoading.value = false;
                // Auto-fetch furigana if toggle is on
                if (showFurigana.value) {
                    fetchFurigana();
                }
            }
        };

        // Furigana Functions
        const escapeHtml = (text) => {
            if (!text) return '';
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/\n/g, '<br>');
        };

        const fetchFurigana = async () => {
            if (translationData.value.length === 0) return;

            isFetchingFurigana.value = true;
            try {
                const texts = translationData.value.map(row => row.original);

                // Send in batches of 100 to avoid huge payloads
                const batchSize = 100;
                for (let i = 0; i < texts.length; i += batchSize) {
                    const batch = texts.slice(i, i + batchSize);
                    const res = await fetch('/api/furigana', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ texts: batch, mode: furiganaMode.value })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        data.results.forEach((html, idx) => {
                            const rowIdx = i + idx;
                            if (translationData.value[rowIdx]) {
                                translationData.value[rowIdx].furiganaHtml = html;
                            }
                        });
                    }
                }
            } catch (e) {
                console.error('Failed to fetch furigana', e);
            } finally {
                isFetchingFurigana.value = false;
            }
        };

        const toggleFurigana = () => {
            showFurigana.value = !showFurigana.value;
            if (showFurigana.value && translationData.value.length > 0) {
                // Always refetch when toggling on
                fetchFurigana();
            } else if (!showFurigana.value) {
                // Clear cached furigana data on toggle off
                translationData.value.forEach(row => { row.furiganaHtml = null; });
            }
        };

        const onFuriganaModeChange = () => {
            // Clear old data and refetch with new mode
            translationData.value.forEach(row => { row.furiganaHtml = null; });
            if (showFurigana.value && translationData.value.length > 0) {
                fetchFurigana();
            }
        };

        const markDirty = () => {
            editRevision += 1;
            hasUnsavedChanges.value = true;
        };

        const saveIfDirty = async () => {
            if (hasUnsavedChanges.value) {
                await saveTranslation();
            }
        };

        // Save translation
        const saveTranslation = async () => {
            if (!activeFile.value) return true;
            if (activeSavePromise) return activeSavePromise;

            const filename = activeFile.value.file;
            const revisionBeingSaved = editRevision;
            const payload = {
                items: translationData.value
            };

            activeSavePromise = (async () => {
                isSaving.value = true;
                try {
                    const res = await fetch(`/api/translation/${filename}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });

                    if (!res.ok) throw new Error("Failed to save");

                    if (activeFile.value?.file === filename && editRevision === revisionBeingSaved) {
                        hasUnsavedChanges.value = false;
                    }
                    console.log("Saved successfully");
                    return true;
                } catch (e) {
                    console.error("Failed to save", e);
                    alert("Failed to save translation!");
                    return false;
                } finally {
                    isSaving.value = false;
                    activeSavePromise = null;
                }
            })();

            return activeSavePromise;
        };

        // Open Save As Modal
        const openSaveAs = () => {
            if (!activeFile.value) return;
            saveAsFilename.value = activeFile.value.file + "_copy";
            showSaveAs.value = true;
        };

        // Confirm Save As
        const confirmSaveAs = async () => {
            if (!saveAsFilename.value) return;

            isSaving.value = true;
            try {
                const payload = {
                    current_filename: activeFile.value.file,
                    new_filename: saveAsFilename.value,
                    items: translationData.value
                };

                const res = await fetch('/api/save_as', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) throw new Error("Failed");

                showSaveAs.value = false;
                isSaving.value = false;
                // Reload scenarios to show new file? 
                // Actually new file might not be in Excel, so it won't show up in list unless we add it to Excel?
                // or maybe we should list files from directory too?
                // For now, just alert success.
                alert(`Saved as ${saveAsFilename.value} successfully! Note: It won't appear in the list unless added to Excel.`);

            } catch (e) {
                console.error("Failed to save as", e);
                isSaving.value = false;
                alert("Failed to save copy!");
            }
        }


        // Bulk Actions
        const closeBulkModal = () => {
            showBulkModal.value = false;
            // bulkFiles.value = [];
            // selectedBulkFiles.value = [];
        };

        const scanForModified = async () => {
            isScanning.value = true;
            try {
                const res = await fetch('/api/bulk/scan');
                const data = await res.json();
                bulkFiles.value = data.files;
                selectedBulkFiles.value = [...data.files]; // Select all by default
            } catch (e) {
                console.error("Scan error", e);
                alert("Failed to scan files");
            } finally {
                isScanning.value = false;
            }
        };

        const toggleSelectAllBulk = () => {
            if (selectedBulkFiles.value.length === bulkFiles.value.length) {
                selectedBulkFiles.value = [];
            } else {
                selectedBulkFiles.value = [...bulkFiles.value];
            }
        };

        const performBulkSave = async () => {
            if (selectedBulkFiles.value.length === 0 || !bulkSuffix.value) return;

            isProcessingBulk.value = true;
            try {
                const res = await fetch('/api/bulk/save_as', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        files: selectedBulkFiles.value,
                        suffix: bulkSuffix.value
                    })
                });

                const data = await res.json();

                if (data.status === 'success') {
                    alert(`Processed ${data.processed} files successfully.` + (data.errors.length ? `\nErrors: ${data.errors.join(', ')}` : ''));
                    closeBulkModal();
                } else {
                    alert("Bulk save failed.");
                }

            } catch (e) {
                console.error("Bulk save error", e);
                alert("Error performing bulk save");
            } finally {
                isProcessingBulk.value = false;
            }
        };

        // Resizable Columns & Preview Functions
        const selectedRow = computed(() => {
            if (selectedRowId.value === null) return null;
            return translationData.value[selectedRowId.value];
        });

        const translationColumnWidth = computed(() => 100 - originalColumnWidth.value);

        const handleCellFocus = (rowId, column) => {
            // Clear any search highlights when user starts editing
            document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                el.classList.remove('in-file-match-highlight');
            });
            inFileHighlightId.value = null;
            
            selectedRowId.value = rowId;
            selectedColumn.value = column;
            showPreview.value = true;
        };

        const startResize = (event) => {
            event.preventDefault();
            const startX = event.clientX;
            const startWidth = originalColumnWidth.value;

            const onMouseMove = (e) => {
                const editorWidth = document.querySelector('.editor-container').offsetWidth;
                const deltaX = e.clientX - startX;
                const deltaPercent = (deltaX / editorWidth) * 100;
                let newWidth = startWidth + deltaPercent;

                // Constrain between 20% and 80%
                newWidth = Math.max(20, Math.min(80, newWidth));
                originalColumnWidth.value = newWidth;
                localStorage.setItem('originalColumnWidth', newWidth);
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        };

        onMounted(() => {
            fetchProjects();
            fetchCacheFolders();
            loadConfig();
            loadScenarios();
            loadScenarioModes();

            // Apply saved theme color
            applyThemeColor(themeColor.value);
            applySecondaryColor(secondaryColor.value);

            // Load and apply wallpaper
            loadWallpapers();
            applyWallpaper(activeWallpaper.value);

            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                // Ctrl+F → Open Global Search (Search tab)
                if (e.ctrlKey && e.key === 'f') {
                    e.preventDefault();
                    showSearchModal.value = true;
                    searchModalTab.value = 'search';
                }
                // Ctrl+H → Open Global Search (Replace tab)
                if (e.ctrlKey && e.key === 'h') {
                    e.preventDefault();
                    showSearchModal.value = true;
                    searchModalTab.value = 'replace';
                }
                // Ctrl+, → Open Settings
                if (e.ctrlKey && e.key === ',') {
                    e.preventDefault();
                    showSettings.value = true;
                }
                // Ctrl+G → Open In-File Search
                if (e.ctrlKey && e.key === 'g') {
                    e.preventDefault();
                    openInFileSearch();
                }
                // Ctrl+S -> Save current file
                if (e.ctrlKey && e.key.toLowerCase() === 's') {
                    e.preventDefault();
                    saveTranslation();
                }
                // Escape → Close modals
                if (e.key === 'Escape') {
                    if (showInFileSearch.value) closeInFileSearch();
                    else if (showSearchModal.value) showSearchModal.value = false;
                    else if (showSettings.value) showSettings.value = false;
                    else if (showSaveAs.value) showSaveAs.value = false;
                    else if (showBulkModal.value) closeBulkModal();
                    else if (showLlmBatchModal.value) closeLlmBatchModal();
                }
            });

            // Attach virtual scroll listener
            const editorEl = document.querySelector('.editor-container');
            if (editorEl) {
                editorEl.addEventListener('scroll', onEditorScroll, { passive: true });
                containerHeight.value = editorEl.clientHeight;
            }

            window.addEventListener('beforeunload', (event) => {
                if (!hasUnsavedChanges.value) return;
                event.preventDefault();
                event.returnValue = '';
            });
        });

        // ─── In-File Search Functions ────────────────────────────────────

        const openInFileSearch = () => {
            showInFileSearch.value = true;
            setTimeout(() => {
                const el = document.getElementById('in-file-search-input');
                if (el) el.focus();
            }, 50);
        };

        const closeInFileSearch = () => {
            showInFileSearch.value = false;
            inFileSearchQuery.value = '';
            inFileSearchResults.value = [];
            inFileSearchIndex.value = -1;
            inFileHighlightId.value = null;
            // Clear any highlights
            document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                el.classList.remove('in-file-match-highlight');
            });
        };

        const performInFileSearch = () => {
            const q = inFileSearchQuery.value.trim().toLowerCase();
            if (!q || translationData.value.length === 0) {
                inFileSearchResults.value = [];
                inFileSearchIndex.value = -1;
                inFileHighlightId.value = null;
                // Clear any global search highlights
                document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                    el.classList.remove('in-file-match-highlight');
                });
                return;
            }

            const matches = [];

            // Generate Kana variants for Romaji search
            let queryKana = "";
            let queryKata = "";
            // Better heuristic: if romaji search is enabled and query looks like romaji
            if (inFileSearchRomaji.value && looksLikeRomaji(q)) {
                try {
                    const converted = romajiToKana(q);
                    if (converted && converted !== q) {
                        queryKana = converted;
                        queryKata = hiraToKata(converted);
                    }
                } catch (e) {
                    console.error("Romaji conversion error:", e);
                }
            }

            translationData.value.forEach((row, idx) => {
                // Helper to check text
                const checkText = (text) => {
                    if (!text) return false;
                    const val = text.toLowerCase();
                    if (val.includes(q)) return true;
                    if (queryKana && val.includes(queryKana)) return true;
                    if (queryKata && val.includes(queryKata)) return true;
                    return false;
                };

                // Search in original
                if (checkText(row.original)) {
                    matches.push(idx);
                    return;
                }
                // Search in reading (Kanji -> Kana match)
                if (row.reading && checkText(row.reading)) {
                    matches.push(idx);
                    return;
                }
                // Search in all translation columns
                if (row.translations) {
                    for (const key of ['initial', 'machine', 'better', 'best', 'polished']) {
                        if (checkText(row.translations[key])) {
                            matches.push(idx);
                            return;
                        }
                    }
                }
                // Search by row ID (#number)
                if ((`#${row.id + 1}`).includes(q) || (`${row.id + 1}`).includes(q)) {
                    matches.push(idx);
                }
            });

            inFileSearchResults.value = matches;
            if (matches.length > 0) {
                inFileSearchIndex.value = 0;
                scrollToInFileMatch(0);
            } else {
                inFileSearchIndex.value = -1;
                inFileHighlightId.value = null;
            }
        };

        const scrollToInFileMatch = (idx) => {
            const rowIdx = inFileSearchResults.value[idx];
            if (rowIdx == null) return;
            inFileHighlightId.value = rowIdx;

            const editorEl = document.querySelector('.editor-container');
            if (editorEl) {
                const targetScrollTop = rowIdx * ROW_HEIGHT - (editorEl.clientHeight / 2);
                editorEl.scrollTo({ top: Math.max(0, targetScrollTop), behavior: 'smooth' });

                // Wait for scroll + render, then highlight
                setTimeout(() => {
                    const rows = document.querySelectorAll('.translation-row');
                    for (const row of rows) {
                        // Find the row by its displayed ID
                        const idEl = row.querySelector('.col-id');
                        if (idEl && parseInt(idEl.textContent.trim().substring(1)) - 1 === rowIdx) {
                            // Remove any existing highlights
                            document.querySelectorAll('.in-file-match-highlight').forEach(el => {
                                el.classList.remove('in-file-match-highlight');
                            });
                            
                            // Add the highlight class
                            row.classList.add('in-file-match-highlight');
                            break;
                        }
                    }
                }, 300);
            }
        };

        const nextInFileMatch = () => {
            if (inFileSearchResults.value.length === 0) return;
            inFileSearchIndex.value = (inFileSearchIndex.value + 1) % inFileSearchResults.value.length;
            scrollToInFileMatch(inFileSearchIndex.value);
        };

        const prevInFileMatch = () => {
            if (inFileSearchResults.value.length === 0) return;
            inFileSearchIndex.value = (inFileSearchIndex.value - 1 + inFileSearchResults.value.length) % inFileSearchResults.value.length;
            scrollToInFileMatch(inFileSearchIndex.value);
        };

        // ─── Romaji Conversion ───────────────────────────────────────────

        const HIRA_TO_ROMAJI_MAP = {
            'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
            'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
            'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
            'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
            'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
            'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
            'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
            'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
            'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
            'わ': 'wa', 'ゐ': 'wi', 'ゑ': 'we', 'を': 'wo',
            'ん': 'n',
            'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
            'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
            'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
            'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
            'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
            'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
            'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
            'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
            'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
            'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
            'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
            'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
            'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
            'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
            'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
            'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
            'ー': '-',
        };

        const ROMAJI_TO_HIRA_MAP = {};
        Object.entries(HIRA_TO_ROMAJI_MAP).forEach(([k, v]) => {
            if (v) ROMAJI_TO_HIRA_MAP[v] = k;
        });
        const ROMAJI_KEYS = Object.keys(ROMAJI_TO_HIRA_MAP).sort((a, b) => b.length - a.length);

        const looksLikeRomaji = (text) => {
            if (!text) return false;
            
            // Check if text contains Latin letters but no Japanese characters
            const hasLatinChars = /[a-zA-Z]/.test(text);
            const hasJapaneseChars = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]/.test(text);
            
            // If it has Latin chars but no Japanese chars, it's likely romaji
            if (hasLatinChars && !hasJapaneseChars) {
                return true;
            }
            
            // Additional check: if it's mostly Latin chars with some common separators
            const latinCount = (text.match(/[a-zA-Z]/g) || []).length;
            const latinRatio = text ? latinCount / text.length : 0;
            if (latinRatio > 0.6 && !hasJapaneseChars) {
                return true;
            }
            
            return false;
        };

        const romajiToKana = (text) => {
            if (!text) return "";
            text = text.toLowerCase();
            let result = "";
            let i = 0;
            while (i < text.length) {
                // 1. Match table
                let matched = false;
                for (const key of ROMAJI_KEYS) {
                    if (text.startsWith(key, i)) {
                        result += ROMAJI_TO_HIRA_MAP[key];
                        i += key.length;
                        matched = true;
                        break;
                    }
                }
                if (matched) continue;

                // 2. Double consonants
                if (i + 1 < text.length && text[i] === text[i + 1] && !['a', 'e', 'i', 'o', 'u', 'n'].includes(text[i])) {
                    result += 'っ';
                    i++;
                    continue;
                }

                // 3. 'n'
                if (text[i] === 'n') {
                    result += 'ん';
                    i++;
                    continue;
                }

                // 4. Pass through
                result += text[i];
                i++;
            }
            return result;
        };

        const hiraToKata = (text) => {
            return text.split('').map(ch => {
                const code = ch.charCodeAt(0);
                if (code >= 0x3041 && code <= 0x3096) {
                    return String.fromCharCode(code + 0x60);
                }
                return ch;
            }).join('');
        };

        // ─── LLM Functions ───────────────────────────────────────────────

        // Ensure polished column exists on loaded data
        const ensurePolishedColumn = () => {
            for (const row of translationData.value) {
                if (!row.translations.hasOwnProperty('polished')) {
                    row.translations.polished = '';
                }
            }
        };

        // Glossary helpers
        const addGlossaryEntry = () => {
            if (!config.value.llm_glossary) config.value.llm_glossary = [];
            config.value.llm_glossary.push({ src: '', dst: '', info: '', case_sensitive: false });
        };

        const removeGlossaryEntry = (idx) => {
            config.value.llm_glossary.splice(idx, 1);
        };

        const importGlossaryFile = () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                try {
                    const text = await file.text();
                    const entries = JSON.parse(text);
                    if (!Array.isArray(entries)) {
                        alert('Invalid format: expected a JSON array of glossary entries.');
                        return;
                    }
                    if (!config.value.llm_glossary) config.value.llm_glossary = [];
                    let added = 0;
                    for (const entry of entries) {
                        if (entry.src && entry.dst) {
                            config.value.llm_glossary.push({
                                src: entry.src || '',
                                dst: entry.dst || '',
                                info: entry.info || '',
                                case_sensitive: entry.case_sensitive || false,
                            });
                            added++;
                        }
                    }
                    alert(`Imported ${added} glossary entries from ${file.name}`);
                } catch (err) {
                    alert('Failed to parse glossary JSON: ' + err.message);
                }
            };
            input.click();
        };

        const exportGlossary = () => {
            const data = config.value.llm_glossary || [];
            const blob = new Blob([JSON.stringify(data, null, 4)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'glossary.json';
            a.click();
            URL.revokeObjectURL(url);
        };

        // Fetch LLM models
        const fetchLlmModels = async () => {
            isFetchingModels.value = true;
            try {
                const res = await fetch('/api/llm/models');
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'connected' && data.models && data.models.length > 0) {
                        fetchedModels.value = data.models;
                        alert(`Found ${data.models.length} model(s):\n` + data.models.join('\n'));
                    } else if (data.status === 'error') {
                        alert(data.message);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch models", e);
            } finally {
                isFetchingModels.value = false;
            }
        };

        // Test LLM connection
        const testLlmConnection = async () => {
            llmTestLoading.value = true;
            llmTestResult.value = null;
            try {
                const res = await fetch('/api/llm/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: config.value.llm_provider || 'gemini_web',
                        api_url: config.value.llm_api_url,
                        model: config.value.llm_model,
                    }),
                });
                const data = await res.json();
                llmTestResult.value = data;
                if (data.status === 'connected' && data.models && data.models.length > 0) {
                    fetchedModels.value = data.models;
                }
            } catch (e) {
                llmTestResult.value = { status: 'error', message: 'Request failed: ' + e.message };
            } finally {
                llmTestLoading.value = false;
            }
        };

        // Per-row retranslate
        const llmRetranslateRow = async (row) => {
            if (row._llmLoading) return;
            row._llmLoading = true;
            try {
                const idx = translationData.value.findIndex(r => r.id === row.id);
                const contextRows = translationData.value.map(r => ({ original: r.original }));
                const res = await fetch('/api/llm/retranslate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        original: row.original,
                        all_rows: contextRows,
                        target_index: idx >= 0 ? idx : 0
                    })
                });
                const data = await res.json();
                if (data.status === 'success' && data.result) {
                    row.translations.polished = data.result;
                } else {
                    alert('LLM error: ' + (data.message || 'Unknown error'));
                }
            } catch (e) {
                alert('LLM request failed: ' + e.message);
            } finally {
                row._llmLoading = false;
            }
        };

        // Per-row polish
        const llmPolishRow = async (row) => {
            if (row._llmLoading) return;
            row._llmLoading = true;
            try {
                const idx = translationData.value.findIndex(r => r.id === row.id);
                const contextRows = translationData.value.map(r => ({ original: r.original }));
                const translation = row.translations[activeTab.value] || row.translations.initial || '';
                const res = await fetch('/api/llm/polish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        original: row.original,
                        translation: translation,
                        all_rows: contextRows,
                        target_index: idx >= 0 ? idx : 0
                    })
                });
                const data = await res.json();
                if (data.status === 'success' && data.result) {
                    row.translations.polished = data.result;
                } else {
                    alert('LLM error: ' + (data.message || 'Unknown error'));
                }
            } catch (e) {
                alert('LLM request failed: ' + e.message);
            } finally {
                row._llmLoading = false;
            }
        };

        // Batch item count
        const llmBatchItemCount = computed(() => {
            if (!translationData.value.length) return 0;
            if (llmBatchRange.value === 'empty') {
                return translationData.value.filter(r => !r.translations.polished).length;
            }
            return translationData.value.length;
        });

        // Start LLM batch
        const startLlmBatch = async () => {
            if (!activeFile.value || llmBatchRunning.value) return;

            llmBatchRunning.value = true;
            llmBatchErrors.value = [];
            llmBatchCurrentItem.value = null;

            // Build items to process
            let items = translationData.value;
            if (llmBatchRange.value === 'empty') {
                items = items.filter(r => !r.translations.polished);
            }

            const payload = {
                mode: llmBatchMode.value,
                source_tab: llmBatchSourceTab.value,
                items: items.map(r => ({
                    id: r.id,
                    original: r.original,
                    translation: r.translations[llmBatchSourceTab.value] || r.translations.initial || ''
                }))
            };

            llmBatchProgress.value = { current: 0, total: payload.items.length };

            try {
                llmBatchAbortController = new AbortController();
                const response = await fetch('/api/llm/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                    signal: llmBatchAbortController.signal
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // Keep incomplete line

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        try {
                            const event = JSON.parse(line.slice(6));

                            if (event.type === 'progress') {
                                llmBatchProgress.value = { current: event.index + 1, total: event.total };
                                llmBatchCurrentItem.value = {
                                    id: event.id,
                                    original: payload.items[event.index]?.original || '',
                                    result: event.result
                                };

                                // Update the actual data
                                const row = translationData.value.find(r => r.id === event.id);
                                if (row && event.result) {
                                    row.translations.polished = event.result;
                                }
                            } else if (event.type === 'error') {
                                llmBatchProgress.value = { current: event.index + 1, total: event.total };
                                llmBatchErrors.value.push(event.message);
                            } else if (event.type === 'done') {
                                // Auto-save after batch completes
                                await saveTranslation();
                            }
                        } catch (parseErr) {
                            console.error('SSE parse error:', parseErr);
                        }
                    }
                }
            } catch (e) {
                if (e.name !== 'AbortError') {
                    console.error('Batch LLM error:', e);
                    alert('Batch processing failed: ' + e.message);
                }
            } finally {
                llmBatchRunning.value = false;
                llmBatchAbortController = null;
                // Save even if stopped early
                if (llmBatchProgress.value.current > 0) {
                    await saveTranslation();
                }
            }
        };

        // Stop LLM batch
        const stopLlmBatch = () => {
            if (llmBatchAbortController) {
                llmBatchAbortController.abort();
            }
        };

        // Close LLM batch modal
        const closeLlmBatchModal = () => {
            if (llmBatchRunning.value) {
                if (!confirm('Batch processing is running. Stop and close?')) return;
                stopLlmBatch();
            }
            showLlmBatchModal.value = false;
        };

        return {
            // WebAI-to-API
            webaiStatus,
            webaiUpdateInfo,
            isCheckingWebaiUpdate,
            isUpdatingWebai,
            webaiUpdateMsg,
            fetchWebaiStatus,
            checkWebaiUpdate,
            performWebaiUpdate,
            geminiCookies,
            showCookieFields,
            isExtractingCookies,
            cookieMsg,
            fetchCookies,
            saveCookies,
            autoExtractCookies,
            launchWebLogin,

            // Projects & Cache Management
            projectList,
            activeProjectId,
            currentProjectIdentifier,
            currentProjectName,
            showNewProjectModal,
            newProjIdentifier,
            newProjName,
            fetchProjects,
            onProjectSelectChange,
            onIdentifierInput,
            onProjectNameInput,
            openNewProjectModal,
            confirmCreateProject,
            deleteCurrentProject,
            availableCacheFolders,
            isRefreshingCaches,
            fetchCacheFolders,
            onCacheFolderSelect,

            scenarios,
            filteredRoutes,
            expandedRoutes,
            toggleRoute,
            activeFile,
            translationData,
            searchQuery,
            isLoading,
            isSaving,
            hasUnsavedChanges,
            config,
            availableCacheFolders,
            isRefreshingCaches,
            fetchCacheFolders,
            onCacheFolderSelect,
            activeTab,
            showSplitView,
            secondaryTab,
            showSettings,
            showLlmConfig,
            showSearchModal,
            globalSearchQuery,
            isRegexSearch,
            searchInInitialOnly,
            searchResults,
            isSearching,
            hasSearched,
            searchResultCount,
            firstMatchOnly,
            searchRomaji,
            performGlobalSearch,

            navigateToResult,
            // Replace & Case
            globalReplaceQuery,
            matchCase,
            preserveCase,
            isReplacing,
            replaceResultMsg,
            performGlobalReplace,
            searchModalTab,
            // Theme
            themePresets,
            themeColor,
            customThemeColor,
            applyThemeColor,
            selectThemePreset,
            onCustomColorChange,
            showThemePicker,
            // Secondary Color
            secondaryColor,
            customSecondaryColor,
            applySecondaryColor,
            selectSecondaryPreset,
            onCustomSecondaryChange,
            // Wallpaper
            wallpapers,
            activeWallpaper,
            showWallpaperPicker,
            selectWallpaper,
            clearWallpaper,
            availableModes,
            selectedModes,
            toggleAllModes,
            showSaveAs,
            saveAsFilename,
            selectScenario,
            saveTranslation,
            markDirty,
            saveIfDirty,
            openSaveAs,
            confirmSaveAs,
            handleSaveConfig,
            // Bulk
            showBulkModal,
            bulkFiles,
            selectedBulkFiles,
            isScanning,
            isProcessingBulk,
            bulkSuffix,
            closeBulkModal,
            scanForModified,
            toggleSelectAllBulk,
            performBulkSave,
            // Resizable & Preview
            originalColumnWidth,
            translationColumnWidth,
            selectedRowId,
            selectedRow,
            selectedColumn,
            showPreview,
            handleCellFocus,
            startResize,
            // Furigana
            showFurigana,
            furiganaMode,
            isFetchingFurigana,
            toggleFurigana,
            fetchFurigana,
            onFuriganaModeChange,
            escapeHtml,
            // In-File Search
            showInFileSearch,
            inFileSearchQuery,
            inFileSearchResults,
            inFileSearchIndex,
            inFileHighlightId,
            inFileSearchRomaji,
            openInFileSearch,

            closeInFileSearch,
            performInFileSearch,
            nextInFileMatch,
            prevInFileMatch,
            // Virtual Scrolling
            visibleRows,
            virtualScrollTopPad,
            virtualScrollBottomPad,
            // LLM
            showLlmBatchModal,
            llmBatchMode,
            llmBatchSourceTab,
            llmBatchRange,
            llmBatchRunning,
            llmBatchProgress,
            llmBatchCurrentItem,
            llmBatchErrors,
            llmBatchItemCount,
            llmTestLoading,
            llmTestResult,
            testLlmConnection,
            clearSummary,
            resetSummaryPrompt,
            fetchLlmModels,
            fetchedModels,
            isFetchingModels,
            addGlossaryEntry,
            removeGlossaryEntry,
            importGlossaryFile,
            exportGlossary,
            llmRetranslateRow,
            llmPolishRow,
            startLlmBatch,
            stopLlmBatch,
            closeLlmBatchModal,
        };
    }
}).mount('#app');
