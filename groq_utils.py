import json
import tools
import ollama

# Define tool schemas for Groq (OpenAI format)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_screen_text_map",
            "description": "Scans the active window for buttons/fields using recursive search to find elements.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "click_element",
    #         "description": "Moves mouse slowly and clicks at coordinates.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "x": {"type": "integer", "description": "X coordinate"},
    #                 "y": {"type": "integer", "description": "Y coordinate"},
    #                 "double_click": {"type": "boolean", "description": "Whether to double click", "default": False}
    #             },
    #             "required": ["x", "y"]
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Types text slowly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launches an app via Run command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app (e.g. notepad)"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_file",
            "description": "DO NOT USE. This is a fake function. You must use the UI to save files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_hotkey",
            "description": "Performs a keyboard shortcut.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_combo": {"type": "string", "description": "Key combination (e.g. ctrl+s)"}
                },
                "required": ["key_combo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_folder_path",
            "description": "Returns absolute path to Desktop/Documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string", "description": "Folder name (e.g. Desktop, Documents)"}
                },
                "required": ["folder_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_app_hotkeys",
            "description": "Asks local Llama 3.2 for an app's keyboard shortcuts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app (e.g. Notepad, WhatsApp)"}
                },
                "required": ["app_name"]
            }
        }
    }
]

# Map names to actual functions
AVAILABLE_FUNCTIONS = {
    "get_screen_text_map": tools.get_screen_text_map,
    # "click_element": tools.click_element,  <-- DISABLED by User Request
    "type_text": tools.type_text,
    "open_app": tools.open_app,
    "press_hotkey": tools.press_hotkey,
    "get_user_folder_path": tools.get_user_folder_path,
    "get_app_hotkeys": lambda app_name: ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"List top 5 Windows keyboard shortcuts for '{app_name}'. Return ONLY the list."}])['message']['content'],
    "save_file": lambda filename: "ERROR: You cannot save files directly. YOU MUST USE THE UI (File > Save As, or Ctrl+S). This is a Windows Desktop Agent, not a backend script."
}

def execute_tool_call(tool_call):
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    if func_name not in AVAILABLE_FUNCTIONS:
        return f"Error: Function {func_name} not found."
    
    print(f"   [System] Executing {func_name} with {args}...")
    try:
        function_to_call = AVAILABLE_FUNCTIONS[func_name]
        return function_to_call(**args)
    except Exception as e:
        return f"Error executing {func_name}: {e}"
