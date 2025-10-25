import os, platform, sys, json
from DataStorage import CodeCell, TextCell, AngleOptimizerCell, File
from Enums import *
from version import __version__
VERSION = __version__
user_path = os.path.expanduser("~")
operating_system = platform.system()

if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

default_code_colors = {
    "Version":VERSION,
    StringLiterals.CODE: {
        Style.FAST: "#00ffff",
        Style.SLOW: "#1e90ff",
        Style.STOP: "#7fffd4",
        Style.SETTER: "#ff8c00",
        Style.RETURN: "#ff6347",
        Style.INPUTS: "#00ff00",
        Style.MODIFIER: "#00ff88",
        Style.CALCS: "#ffc0cb",
        Style.NUMBERS: "#ffff00",
        Style.COMMENT: "#808080",
        Style.NEST1: "#ee82ee",
        Style.NEST2: "#4169e1",
        Style.NEST0: "#ffd700",
        Style.KW_ARG: "#ff00ff",
        Style.VARS: "#7cfc00",
        Style.STRING: "#ff3030",
        Style.BACKSLASH: "#fa8072",
        Style.COMMENT_BACKSLASH: "#424242",
        Style.CUSTOM_FUNC_PARAMETER: "#e066ff",
        Style.CUSTOM_FUNC: "#c6e2ff",
        Style.ERROR: "#ff0000",
        Style.DEFAULT: "#ffffff",
        Style.BOOL: "#0fff83"
    },
    StringLiterals.OUTPUT: {
        Style.OUTPUT_ZLABEL: "#00ffff",
        Style.OUTPUT_XLABEL: "#ee82ee",
        Style.OUTPUT_LABEL: "#ff8c00",
        Style.OUTPUT_WARNING: "#ff6347",
        Style.OUTPUT_TEXT: "#ffd700",
        Style.OUTPUT_POSITIVE: "#00ff00",
        Style.OUTPUT_NEGATIVE: "#ff6347",
        Style.OUTPUT_PLACEHOLDER: "#808080",
        Style.DEFAULT: "#ffffff"
    },
    StringLiterals.CODE_BACKGROUND: "#2e2e2e",
    StringLiterals.OUTPUT_BACKGROUND: "#2e2e2e"
}

default_text_colors = {
    "Version":VERSION,
    StringLiterals.CODE: {
        Style.HEADER1: "#00ff88",
        Style.HEADER2: "#00ff88",
        Style.HEADER3: "#00ff88",
        Style.DEFAULT: "#ffffff"
    },
    StringLiterals.RENDER: {
        Style.RENDER_HEADER1: "#00ff88",
        Style.RENDER_HEADER2: "#00ff88",
        Style.RENDER_HEADER3: "#00ff88",
        Style.LINKS: "#1fb9e8",
        Style.DEFAULT: "#ffffff",
        Style.POSITIONAL_PARAMETER: "#FF009D",
        Style.VAR_POSITIONAL_PARAMETER: "#FF4BBA",
        Style.KEYWORD_PARAMETER: "#ff6200",
        Style.POSITIONAL_OR_KEYWORD_PARAMETER: "#ffcf33",
        Style.DATATYPE: "#0ffff0"
    },
    StringLiterals.OUTPUT_BACKGROUND: "#3e3e3e",
    StringLiterals.RENDER_BLOCK_BACKGROUND: "#242424",
    StringLiterals.RENDER_CODE_BACKGROUND: "#4b4b4b",
    StringLiterals.RENDER_BACKGROUND: "#2e2e2e"
}

last_state = {
    "crashed":False,
    "tempfile":False,
    "log":""
    }

def getSettings(fileName):
    "Get settings from `fileName`. For general settings, use `getGeneralSettings`"
    path = os.path.join(getPathToSettings(), fileName)
    with open(path) as file:
        return convertKeysToInt(json.load(file))
    
def getCodeColorSettings():
    "Get the color mapping for Mothball code highlighting"
    return getSettings("Code Colors.json")

def getTextColorSettings():
    "Get the color mapping for markdown code highlighting and rendering. Mothball code blocks are handled by the code colors found by `getCodeColorSettings`."
    return getSettings("Text Colors.json")
    
def getGeneralSettings():
    "Get general settings"
    return getSettings("Settings.json")

def getNotebooks():
    "Returns the path to the Mothball notebooks."
    return os.path.join(user_path, "Documents", "Mothball", "Notebooks")

def getMacros():
    "Returns the default path to Mothball generated macros."
    return os.path.join(user_path, "Documents", "Mothball", "Macros")

default_settings = {
    "Ask before deleting a cell": False,
    "Max mothball code lines": 0,
    "Max markdown code lines": 0,
    "Max mothball output lines": 0,
    "Max markdown output lines": 0,
    "Default Font": "Consolas",
    "Default Font Size": 14,
    "Macro Folders": {'default': getMacros()},
    "Version": VERSION
}

def createDirectories():
    """
    Create related files for Mothball settings, and saved notebooks, based on the operating system.

    Windows: AppData/Roaming \\
    Mac: Library/Application Support \\
    Linux: .config

    Nothing happens if the directories already exist.
    """
    
    path = None
    # Make Setting Directory
    if operating_system == "Windows":
        path = os.path.join(user_path, "AppData", "Roaming", "Mothball", "Mothball Settings")
        os.makedirs(path, exist_ok=True)

    elif operating_system == "Darwin":
        path = os.path.join(user_path, "Library", "Application Support", "Mothball", "Mothball Settings")
        os.makedirs(path, exist_ok=True)
    
    elif operating_system == "Linux":
        path = os.path.join(user_path, ".config", "Mothball", "Mothball Settings")
        os.makedirs(path, exist_ok=True)

    # If jsons doesn't exist, add it
    if not os.path.exists(os.path.join(path, "Code Colors.json")):
        with open(os.path.join(path, "Code Colors.json"), "w") as file:
            json.dump(default_code_colors, file)
    
    if not os.path.exists(os.path.join(path, "Text Colors.json")):
        with open(os.path.join(path, "Text Colors.json"), "w") as file:
            json.dump(default_text_colors, file)

    if not os.path.exists(os.path.join(path, "Settings.json")):
        with open(os.path.join(path, "Settings.json"), "w") as file:
            json.dump(default_settings, file)
    
    
    # Make Saved Notebook Directory
    os.makedirs(os.path.join(user_path, "Documents", "Mothball", "Notebooks"),exist_ok=True)
    os.makedirs(os.path.join(user_path, "Documents", "Mothball", "Macros"),exist_ok=True)

    # Crash Logs
    os.makedirs(os.path.join(user_path, "Documents", "Mothball", "Logs"),exist_ok=True)
    if not os.path.exists(os.path.join(user_path, "Documents", "Mothball", "Logs", "crash_logs.txt")):
        with open(os.path.join(user_path, "Documents", "Mothball", "Logs", "crash_logs.txt"), "w") as file:
            file.write("Crash Logs File\n")

    # Last State
    p = os.path.join(base_path, "Last_State")
    os.makedirs(p, exist_ok=True)
    if not os.path.exists(os.path.join(p, "LastState.json")):
        with open(os.path.join(p, "LastState.json"), "w") as file:
            json.dump(last_state, file)
    if not os.path.exists(os.path.join(p, "tempfile.json")):
        with open(os.path.join(p, "tempfile.json"), "w") as file:
            json.dump({}, file)

def getPathtoLogs():
    return os.path.join(user_path, "Documents", "Mothball", "Logs", "crash_logs.txt")

def getPathToLastState():
    return os.path.join(base_path, "Last_State")

def getPathToSettings():
    """
    Returns the path to Mothball settings directory

    Windows: AppData/Roaming \\
    Mac: Library/Application Support \\
    Linux: .config

    Raises `FileNotFoundError` if it doesn't exist.
    """
    path = None
    if operating_system == "Windows":
        path = os.path.join(user_path, "AppData", "Roaming", "Mothball", "Mothball Settings")
    elif operating_system == "Darwin":
        path = os.path.join(user_path, "Library", "Application Support", "Mothball", "Mothball Settings")
    elif operating_system == "Linux":
        path = os.path.join(user_path, ".config", "Mothball", "Mothball Settings")
    if path is None:
        raise FileNotFoundError(f"No directory exists to settings")
    return path

def convertKeysToInt(dictionary: dict):
    new_dict = {}
    for key,value in dictionary.items():
        if isinstance(key, str) and key.isnumeric():
            key = int(key)
            new_dict[key] = None
        else:
            new_dict[key] = None
        if isinstance(value, dict):
            new_dict[key] = convertKeysToInt(value)
        else:
            new_dict[key] = value
    
    return new_dict

def saveSettings(obj, fileName):
    path = os.path.join(getPathToSettings(), fileName)
    with open(path, "w") as file:
        json.dump(obj, file)

def saveGeneralSettings(obj):
    saveSettings(obj, "Settings.json")

def saveCodeColorSettings(obj):
    saveSettings(obj, "Code Colors.json")

def saveTextColorSettings(obj):
    saveSettings(obj, "Text Colors.json")


def loadFile(filepath):
    "Load and parse a Mothball file, returning a `File` object"
    with open(filepath) as file:
        f=json.load(file)

    i = 0
    entries = {}
    while True:
        a = f.get(str(i))
        if a is None:
            break
        try:
            if a['cell_type'] == CellType.TEXT:
                entries[i] = TextCell(**a)
            elif a['cell_type'] == CellType.XZ or a['cell_type'] == CellType.Y:
                entries[i] = CodeCell(**a)
            elif a['cell_type'] == CellType.OPTIMIZE:
                entries[i] = AngleOptimizerCell(**a)
            else:
                entries[i] = CodeCell('',CellType.XZ,"# OOPS! I couldn't load this file!",None,False,[])
        except Exception as e:
            try:
                entries[i] = CodeCell('',CellType.XZ,a['code'],None,False,[])
            except Exception as ee:
                entries[i] = CodeCell('',CellType.XZ,"# OOPS! I couldn't load this file!",None,False,[])

        i += 1

    return File(f['fileName'], f['version'], entries)

def versionIsOutdated(version_str: str):
    """
    Compares the `version_str` with the current version given by `VERSION`, returning True if `VERSION` is later than `version_str`
    
    Version is in the format `major.minor.patch`, where `major`, `minor`, `patch` are integers.
    """
    
    original_version = [int(x) for x in VERSION.split(".")]
    compared_to = [int(x) for x in version_str.split(".")]

    for i,j in zip(original_version, compared_to):
        if i > j:
            return True
        elif i < j:
            return False
    return False

# idk i shouldve done version mapping much sooner
def getDefaultSettings():
    return default_settings, default_code_colors, default_text_colors

def settings_version_upgrade(original_version: str, to_version: str, func = None):
    g = getGeneralSettings()
    c = getCodeColorSettings()
    t = getTextColorSettings()

    if not ('Version' in g):
        g['Version'] = original_version
    if not ('Version' in c):
        c['Version'] = original_version
    if not ('Version' in t):
        t['Version'] = original_version

    # assert g['Version'] == original_version
    # assert c['Version'] == original_version
    # assert t['Version'] == original_version

    g['Version'] = to_version
    c['Version'] = to_version
    t['Version'] = to_version

    if func is not None:
        g,c,t = func(g,c,t)
    
    saveGeneralSettings(g)
    saveCodeColorSettings(c)
    saveTextColorSettings(t)

    return g,c,t    

def v1_1_4_to_v1_1_5_settings(g,c,t):
    oldpath = "Path to Minecraft Macro Folder"
    if oldpath in g:
        p = g.pop(oldpath)
        g["Macro Folders"] = {'default': getMacros(), "path1": p}

    return g,c,t

settings_version_map = {
    "1.1.3": lambda: settings_version_upgrade("1.1.3", "1.1.4"),
    "1.1.4": lambda: settings_version_upgrade("1.1.4", "1.1.5", v1_1_4_to_v1_1_5_settings),
    "1.1.5": lambda: settings_version_upgrade("1.1.5", "1.1.6"),
    "1.1.6": lambda: settings_version_upgrade("1.1.6", "1.1.7")}

def notebook_version_upgrade(path: str, original_version: str, to_version: str, func = None):
    with open(path) as f:
        d = json.load(f)

    assert d['version'] == original_version
    d['version'] = to_version

    if func is not None:
        d = func(d)

    with open(path, "w") as f:
        json.dump(d, f)
    
    return d


notebooks_version_map = {
    "1.1.3": lambda path: notebook_version_upgrade(path, "1.1.3", "1.1.4"),
    "1.1.4": lambda path: notebook_version_upgrade(path, "1.1.4", "1.1.5"),
    "1.1.5": lambda path: notebook_version_upgrade(path, "1.1.5", "1.1.6"),
    "1.1.6": lambda path: notebook_version_upgrade(path, "1.1.6", "1.1.7")}