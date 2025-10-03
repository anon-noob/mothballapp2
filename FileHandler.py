import os, platform, json
from DataStorage import CodeCell, TextCell, AngleOptimizerCell, File
from Enums import *
from version import __version__

VERSION = __version__
user_path = os.path.expanduser("~")
operating_system = platform.system()

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
    
    # ADD minigames later
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

# def reindexFiles():
#     "Reindex cells to start at 0 instead of 1, for versions 1.1.0 and above"
#     notebooks_path = getNotebooks()
#     files = [f for f in os.listdir(notebooks_path) if os.path.isfile(os.path.join(notebooks_path, f))]

#     for file in files:
#         try:
#             with open(os.path.join(notebooks_path,file), "r") as f:
#                 data = json.load(f)
            
#             if not versionIsOutdated(data["version"]):
#                 continue
#             if str(0) in data: # already reindexed
#                 continue

#             new_data = {"fileName": data["fileName"], "version": VERSION}

#             i = 1
#             while str(i) in data:
#                 new_data[str(i-1)] = data[str(i)]
#                 i += 1

#             with open(os.path.join(notebooks_path,file), "w") as f:
#                 json.dump(new_data, f, indent=4)
        
#         except Exception as e:
#             pass

# def updateFiles():
#     notebooks_path = getNotebooks()
#     files = [f for f in os.listdir(notebooks_path) if os.path.isfile(os.path.join(notebooks_path, f))]

#     for file in files:
#         try:
#             with open(os.path.join(notebooks_path,file), "r") as f:
#                 data = json.load(f)

#             i = 0
#             while str(i) in data:
#                 if 'type' in data[str(i)]:
#                     del data[str(i)]['type']
#                 if isinstance(data[str(i)]['mode'], str) or isinstance(data[str(i)]['mode'], int):
#                     a = data[str(i)]['mode']
#                     data[str(i)]['cell_type'] = {"xz": 0, "y": 1, "text": 2}.get(a, a)
#                     if a != 2:
#                         del data[str(i)]['mode']
#                     else:
#                         data[str(i)]['mode'] = StringLiterals.RENDER

#                 i += 1
            
#             with open(os.path.join(notebooks_path,file), "w") as f:
#                 json.dump(data, f, indent=4)
#         except Exception as e:
#             pass

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

def v1_1_4_to_v1_1_5_settings():
    g = getGeneralSettings()
    c = getCodeColorSettings()
    t = getTextColorSettings()

    g['Version'] = "1.1.5"
    c['Version'] = "1.1.5"
    t['Version'] = "1.1.5"

    oldpath = "Path to Minecraft Macro Folder"
    if oldpath in g:
        p = g.pop(oldpath)
    g["Macro Folders"] = {'default': getMacros(), "path1": p}

    saveGeneralSettings(g)
    saveCodeColorSettings(c)
    saveTextColorSettings(t)

    return g,c,t

def v1_1_3_to_v1_1_4_settings():
    g = getGeneralSettings()
    c = getCodeColorSettings()
    t = getTextColorSettings()

    g['Version'] = "1.1.4"
    c['Version'] = "1.1.4"
    t['Version'] = "1.1.4"

    saveGeneralSettings(g)
    saveCodeColorSettings(c)
    saveTextColorSettings(t)

    return g,c,t

settings_version_map = {
    "1.1.3": v1_1_3_to_v1_1_4_settings,
    "1.1.4": v1_1_4_to_v1_1_5_settings}

def v1_1_3_to_v1_1_4_notebook(path: str):
    with open(path) as f:
        d = json.load(f)

    d['version'] = '1.1.4'

    with open(path, "w") as f:
        json.dump(d, f)
    
    return d

def v1_1_4_to_v1_1_5_notebook(path: str):
    with open(path) as f:
        d = json.load(f)

    d['version'] = '1.1.5'

    with open(path, "w") as f:
        json.dump(d, f)
    
    return d

notebooks_version_map = {
    "1.1.3": v1_1_3_to_v1_1_4_notebook,
    "1.1.4": v1_1_4_to_v1_1_5_notebook}

# if __name__ == '__main__':
#     def deleteAll():
#         if operating_system == "Windows":
#             path = os.path.join(user_path, "AppData", "Roaming", "Mothball", "Mothball Settings")
#         elif operating_system == "Darwin":
#             path = os.path.join(user_path, "Library", "Application Support", "Mothball", "Mothball Settings")
#         elif operating_system == "Linux":
#             path = os.path.join(user_path, ".config", "Mothball", "Mothball Settings")
        
#         print("Delete All:", os.listdir(path))
#         r = input("Confirm? (y/n) ").strip().lower()
#         if r == "y":
#             for filename in os.listdir(path):
#                 file_path = os.path.join(path, filename)
#                 if os.path.isfile(file_path):
#                     os.remove(file_path)
#         else:
#             print("Cancelled")

#     deleteAll()