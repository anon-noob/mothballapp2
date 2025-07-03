import os, platform, json
from DataStorage import CodeCell, TextCell, File

VERSION = "v1.1.0"

default_code_colors = {
    "Code": {
        "fast": "#00ffff",
        "slow": "#1e90ff",
        "stop": "#7fffd4",
        "setters": "#ff8c00",
        "returners": "#ff6347",
        "inputs": "#00ff00",
        "modifiers": "#00ff88",
        "calculators": "#ffc0cb",
        "numbers": "#ffff00",
        "comment": "#808080",
        "bracket1": "#ee82ee",
        "bracket2": "#4169e1",
        "bracket0": "#ffd700",
        "keyword": "#ff00ff",
        "variable": "#7cfc00",
        "string": "#ff3030",
        "backslash": "#fa8072",
        "commentBackslash": "#424242",
        "customFunctionParameter": "#e066ff",
        "customFunction": "#c6e2ff",
        "error": "#ff0000",
        "default": "#ffffff"
    },
    "Output": {
        "zLabel": "#00ffff",
        "xLabel": "#ee82ee",
        "label": "#ff8c00",
        "warning": "#ff6347",
        "text": "#ffd700",
        "positiveNumber": "#00ff00",
        "negativeNumber": "#ff6347",
        "placeholder": "#808080",
        "default": "#ffffff"
    },
    "Code Background": "#2e2e2e",
    "Output Background": "#2e2e2e"
}

default_text_colors = {
    "Code": {
        "heading1": "#00ff88",
        "heading2": "#00ff88",
        "heading3": "#00ff88",
        "default": "#ffffff"
    },
    "Render": {
        "heading1": "#00ff88",
        "heading2": "#00ff88",
        "heading3": "#00ff88",
        "links": "#1fb9e8",
        "default": "#ffffff",
        "Output Background": "#3e3e3e",
        "Block Background": "#242424",
        "Positional Parameter": "#FF009D",
        "Var Positional Parameter": "#FF4BBA",
        "Keyword Parameter": "#ff6200",
        "Positional or Keyword Parameter": "#ffcf33",
        "datatype": "#0ffff0"
    },
    "Code Background": "#2e2e2e",
    "Render Background": "#2e2e2e"
}

default_settings = {
    "Ask before deleting a cell": False,
    "Max mothball code lines": 0,
    "Max markdown code lines": 0,
    "Max mothball output lines": 0,
    "Max markdown output lines": 0,
    "Default Font": "Consolas",
    "Default Font Size": 14,
    "Version": VERSION
}

user_path = os.path.expanduser("~")
operating_system = platform.system()

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

def getSettings(fileName):
    "Get settings from `fileName`. For general settings, use `getGeneralSettings`"
    path = os.path.join(getPathToSettings(), fileName)
    with open(path) as file:
        return json.load(file)
    
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

def loadFile(filepath):
    "Load and parse a file, returning a `File` object"
    with open(filepath) as file:
        f=json.load(file)

    i = 0
    entries = {}
    while True:
        a = f.get(str(i))
        if a is None:
            break
        if a['type'] == "text":
            entries[i] = TextCell(**a)
        elif a['type'] == "code":
            entries[i] = CodeCell(**a)

        i += 1

    return File(f['fileName'], f['version'], entries)

def reindexFiles():
    "Reindex cells to start at 0 instead of 1, for versions 1.1.0 and above"
    notebooks_path = getNotebooks()
    files = [f for f in os.listdir(notebooks_path) if os.path.isfile(os.path.join(notebooks_path, f))]

    for file in files:
        try:
            with open(os.path.join(notebooks_path,file), "r") as f:
                data = json.load(f)
            
            if data["version"] == VERSION:
                continue
            if str(0) in data: # already reindexed
                continue

            new_data = {"fileName": data["fileName"], "version": VERSION}

            i = 1
            while str(i) in data:
                new_data[str(i-1)] = data[str(i)]
                i += 1

            with open(os.path.join(notebooks_path,file), "w") as f:
                json.dump(new_data, f, indent=4)
        
        except Exception as e:
            pass
        
if __name__ == "__main__":
    # For deleting unnecessary files
    def deleteAll():
        if operating_system == "Windows":
            path = os.path.join(user_path, "AppData", "Roaming", "Mothball", "Mothball Settings")
        elif operating_system == "Darwin":
            path = os.path.join(user_path, "Library", "Application Support", "Mothball", "Mothball Settings")
        elif operating_system == "Linux":
            path = os.path.join(user_path, ".config", "Mothball", "Mothball Settings")
        
        print("Delete All:", os.listdir(path))
        r = input("Confirm? (y/n) ").strip().lower()
        if r == "y":
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        else:
            print("Cancelled")
    
    deleteAll()