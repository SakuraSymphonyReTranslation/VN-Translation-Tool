import pandas as pd
import os
import re
from . import config_manager

def _fallback_directory_structure():
    """
    Fallback scenario grouping when Excel file is not configured or not found.
    Scans translated_dir or original_dir for all JSON files and groups them intelligently.
    """
    trans_dir = config_manager.get_path("translated_dir")
    orig_dir = config_manager.get_path("original_dir")
    proj_dir = config_manager.get_path("project_data_dir")
    
    target_dir = ""
    for d in [trans_dir, orig_dir, proj_dir]:
        if d and os.path.exists(d):
            target_dir = d
            break
            
    if not target_dir:
        return {}
        
    try:
        files = [f for f in os.listdir(target_dir) if f.endswith(".json")]
        if not files:
            return {}
            
        groups = {}
        for f in sorted(files):
            stem = f[:-5] # remove .json
            
            # Detect group prefix (e.g. dc4_asa... -> ASA, dc3_chp1... -> CHP1, or general prefix)
            match = re.match(r'^[a-zA-Z0-9]+_([a-zA-Z0-9]{2,4})', stem)
            if match:
                group_name = match.group(1).upper()
            else:
                prefix = stem.split('_')[0] if '_' in stem else "General"
                group_name = prefix.upper()
                
            if group_name not in groups:
                groups[group_name] = []
                
            groups[group_name].append({
                "file": stem,
                "code": "",
                "segment": stem,
                "part": "",
                "mode": group_name
            })
            
        return groups
    except Exception as e:
        print(f"Error scanning fallback directory structure: {e}")
        return {}

def load_scenario_structure():
    EXCEL_PATH = config_manager.get_path("excel_path")
    
    if not EXCEL_PATH or not os.path.exists(EXCEL_PATH):
        return _fallback_directory_structure()

    try:
        xl = pd.ExcelFile(EXCEL_PATH)
        scenarios = {}
        ignore_sheets = ['mib', 'hiy', 'mic', 'sii', 'miu', 'tiy']

        for sheet_name in xl.sheet_names:
            if sheet_name in ignore_sheets:
                pass
            
            df = xl.parse(sheet_name)
            df.columns = df.columns.astype(str).str.strip()
            
            required_columns = ['Nama file']
            if not all(col in df.columns for col in required_columns):
                continue
                
            entries = []
            last_segment = ""
            last_mode = ""

            for _, row in df.iterrows():
                filename = str(row.get('Nama file', '')).strip()
                if not filename or filename.lower() == 'nan':
                    continue
                
                raw_segment = str(row.get('Nama Segment', '')).strip()
                raw_mode = str(row.get('Scenario Mode', '')).strip()
                
                if raw_segment and raw_segment.lower() != 'nan':
                    last_segment = raw_segment
                
                if raw_mode and raw_mode.lower() != 'nan':
                    last_mode = raw_mode
                
                segment = raw_segment if (raw_segment and raw_segment.lower() != 'nan') else last_segment
                mode = raw_mode if (raw_mode and raw_mode.lower() != 'nan') else last_mode

                entry = {
                    "file": filename,
                    "code": str(row.get('Kode', '')).strip(),
                    "segment": segment,
                    "part": str(row.get('Bagian', '')).strip(),
                    "mode": mode
                }
                
                for k, v in entry.items():
                    if v.lower() == 'nan':
                        entry[k] = ""
                        
                entries.append(entry)
            
            if entries:
                scenarios[sheet_name] = entries
                
        if not scenarios:
            return _fallback_directory_structure()
            
        return scenarios

    except Exception as e:
        print(f"Error reading Excel structure: {e}")
        return _fallback_directory_structure()

def get_all_scenario_modes():
    EXCEL_PATH = config_manager.get_path("excel_path")
    
    if not EXCEL_PATH or not os.path.exists(EXCEL_PATH):
        fallback = _fallback_directory_structure()
        return sorted(list(fallback.keys()))
    
    try:
        xl = pd.ExcelFile(EXCEL_PATH)
        all_modes = set()
        
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            df.columns = df.columns.astype(str).str.strip()
            
            if 'Scenario Mode' in df.columns:
                modes = df['Scenario Mode'].dropna().unique()
                for mode in modes:
                    mode_str = str(mode).strip()
                    if mode_str and mode_str.lower() != 'nan':
                        all_modes.add(mode_str)
        
        if not all_modes:
            fallback = _fallback_directory_structure()
            return sorted(list(fallback.keys()))
            
        return sorted(all_modes)
    except Exception as e:
        print(f"Error getting scenario modes: {e}")
        fallback = _fallback_directory_structure()
        return sorted(list(fallback.keys()))

def get_files_by_modes(selected_modes):
    if not selected_modes:
        return None
    
    EXCEL_PATH = config_manager.get_path("excel_path")
    
    if not EXCEL_PATH or not os.path.exists(EXCEL_PATH):
        fallback = _fallback_directory_structure()
        matching = set()
        for mode in selected_modes:
            if mode in fallback:
                for entry in fallback[mode]:
                    matching.add(entry["file"])
        return matching if matching else None
    
    try:
        xl = pd.ExcelFile(EXCEL_PATH)
        matching_files = set()
        
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            df.columns = df.columns.astype(str).str.strip()
            
            if 'Nama file' not in df.columns or 'Scenario Mode' not in df.columns:
                continue
            
            last_mode = ""
            for _, row in df.iterrows():
                filename = str(row.get('Nama file', '')).strip()
                raw_mode = str(row.get('Scenario Mode', '')).strip()
                
                if raw_mode and raw_mode.lower() != 'nan':
                    last_mode = raw_mode
                
                current_mode = raw_mode if (raw_mode and raw_mode.lower() != 'nan') else last_mode
                
                if filename and filename.lower() != 'nan':
                    if current_mode in selected_modes:
                        matching_files.add(filename)
        
        return matching_files if matching_files else None
    except Exception as e:
        print(f"Error getting files by modes: {e}")
        return None
