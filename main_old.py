import os
import time
import sys
from dotenv import load_dotenv
from groq import Groq
import groq_utils
from memory_manager import MemoryJanitor
import tools

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("FATAL ERROR: GROQ_API_KEY not found in .env file.")
    print("Please get a free key from https://console.groq.com/keys")
    sys.exit(1)

client = Groq(api_key=api_key)
janitor = MemoryJanitor(user_id="demo_agent")
HISTORY = [] 

# --- SYSTEM INSTRUCTION (PARANOID MODE) ---
SYSTEM_PROMPT = """
You are a Closed-Loop Windows Desktop Agent. 
You DO NOT assume actions worked. You VERIFY them using the provided Screen State.

PROTOCOL:
1. READ the 'CURRENT SCREEN STATE' provided in every user message.
2. IF you see "Confirm Save As" or "already exists", you must resolve it (e.g., press 'y' or click 'Yes').
3. IF the app didn't open via Run command, try searching for it: PRESS Windows key, TYPE app name, PRESS Enter.
4. IF that also fails, try again or ask for help.
5. START by finding the Desktop path via 'get_user_folder_path'.
6. ONLY say "MISSION COMPLETE" when the file is visibly saved and the UI is stable.

AVAILABLE TOOLS:
- open_app: Launches an application. Args: {"app_name": "notepad"}
- type_text: Types text. Args: {"text": "hello", "press_enter": true}
- click_element: Clicks at (x, y). Args: {"x": 100, "y": 200, "double_click": false}
- press_hotkey: Keyboard shortcuts. Args: {"key_combo": "ctrl+s"}
- get_user_folder_path: Returns path. Args: {"folder_name": "Desktop"}
- get_screen_text_map: Scans screen. Args: {}
- get_app_hotkeys: Asks Llama for hotkeys. Args: {"app_name": "Notepad"}

COMMAND FORMAT:
To execute a tool, you MUST output a block like this:
<function=tool_name>{"arg_name": "value"}</function>
Example: <function=type_text>{"text": "Hello"}</function>

RESTRICTIONS:
- DO NOT hallucinate tools like 'save_file'.
- ALWAYS use keyboard shortcuts (Hotkeys) for saving. DO NOT use the mouse to click 'File' > 'Save'.
- To save to a specific folder:
  1. PRESS 'ctrl+s' to open the Save dialog.
  2. REASONING: "I need to set the filename first."
  3. PRESS 'alt+n' to focus the File Name field.
  4. TYPE the filename. Args: {"text": "filename.txt", "press_enter": false}
  5. REASONING: "Now I can change the folder."
  6. PRESS 'alt+d' to focus the Address Bar.
  7. TYPE the full folder path and PRESS 'enter' (Wait for navigation).
  8. REASONING: "Finally, I can save."
  9. PRESS 'alt+s' or 'enter' to Save.

WINDOWS UI KNOWLEDGE:
- 'Alt+D' -> Focuses Address Bar (File Explorer/Dialogs)
- 'Alt+N' -> Focuses File Name Field
- 'Ctrl+S' -> Save
- 'Enter' in Address Bar -> Navigates to folder

GENERAL_HEURISTICS:
1. LAUNCH PROTOCOL:
   - Try 'open_app' (Run command) first.
   - CRITICAL FALLBACK: If 'open_app' fails or it is a Store App (like WhatsApp, Spotify), do this:
     PRESS 'win', TYPE app name, PRESS 'enter'.
   - NEVER assume an app is not installed until you try Windows Search.

2. SEARCH/NAVIGATION PROTOCOL:
   - Do NOT guess coordinates.
   - USE 'get_app_hotkeys' to find tools for the specific app.
   - Look for UI elements: "Search", "Find", "Magnifying Glass" icon in the screen text map.
   - If no search bar is found, click the window center to focus and just TYPE.

3. VERIFICATION PROTOCOL:
   - You MUST confirm success by reading the screen state.
   - Example: If opening a chat, you must see the person's name on screen.
   - Example: If saving a file, you must see "Saved" or the file icon on Desktop.

"""

def run_agent(goal):
    global HISTORY
    print(f"--- STARTING MISSION (GROQ): {goal} ---")
    
    past_tips = janitor.retrieve_context(goal)
    context_str = "\n".join(past_tips) if past_tips else "No prior knowledge."
    print(f"[Memory] Retrieved Context: {context_str}")

    # Initialize Conversation History
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"GOAL: {goal}. \nCONTEXT: {context_str}"}
    ]
    
    # --- CLOSED LOOP EXECUTION ---
    MAX_TURNS = 15
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    for i in range(MAX_TURNS):
        print(f"\n[Step {i+1}] Observing & Thinking...")
        
        try:
            # 1. FORCE-FEED VISION
            print("   [System] Scanning screen...")
            current_screen_text = tools.get_screen_text_map()
            
            # 2. Add Observation to History
            observation_msg = (
                f"--- CURRENT SCREEN STATE (What you see right now) ---\n"
                f"{current_screen_text}\n"
                f"----------------------------------------------------\n"
                f"Based on this state, did the last action work? What is the next step?"
            )
            messages.append({"role": "user", "content": observation_msg})

            # 3. Call Groq (No native tools, manual parsing)
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1024
            )
            
            response_msg = completion.choices[0].message
            content = response_msg.content or ""
            print(f"   [Agent]: {content}")
            HISTORY.append(f"Response: {content}")
            messages.append(response_msg)

            # 4. Manual Tool Parsing
            # Look for <function=name>args</function> or JSON blocks
            import re
            
            # Pattern: <function=name>{args}</function>
            # Note: The model often outputs <function=open_app>{"app_name": "notepad"}</function>
            tool_pattern = r'<function=(\w+)>(.*?)</function>'
            matches = re.findall(tool_pattern, content, re.DOTALL)
            
            if matches:
                print(f"   [System] Detected {len(matches)} tool calls (Text Mode)...")
                for func_name, args_str in matches:
                    try:
                        # Clean args
                        import json
                        args = json.loads(args_str)
                        
                        # Mock a tool call object for verify/execute
                        print(f"   [System] Executing {func_name} with {args}...")
                        
                        if func_name in groq_utils.AVAILABLE_FUNCTIONS:
                            result = groq_utils.AVAILABLE_FUNCTIONS[func_name](**args)
                        else:
                            result = f"Error: Function {func_name} not found."
                            
                        # Feed result back as USER message (since we aren't using native tool roles)
                        messages.append({"role": "user", "content": f"Tool '{func_name}' Output: {result}"})
                        print(f"   [Tool Output]: {result}")
                        
                    except Exception as e:
                        print(f"   [Error Parsing Tool]: {e}")
                        messages.append({"role": "user", "content": f"Error executing {func_name}: {e}"})
            else:
                # Fallback: Check for markdown code blocks with simple calls
                pass

            # --- CHECK COMPLETION ---
            # Check most recent message for completion signal
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                last_content = last_msg.get("content", "")
            else:
                last_content = last_msg.content or ""
                
            if last_content and "MISSION COMPLETE" in last_content:
                print("   [System] Agent indicated task completion. Stopping.")
                break
            
            # --- MEMORY PRUNING ---
            # Basic prudence: if history gets too long, we might need to trim interaction
            # For simplicity in this script, we just proceed.
            
            print("   [System] Sleeping 2s...")
            time.sleep(2)

        except Exception as e:
            print(f"   [Error] {e}")
            break

    print("--- MISSION END ---")

if __name__ == "__main__":
    print("WARNING: This script will take control of your mouse.")
    time.sleep(3)
    
    # We test the Reasoning capability
    run_agent("Open Notepad, write a code to check if a number is prime or not in  python, and save it as prime.py")
    #Notepad, write a code to check if a number is prime or not in  python, and save it as prime.py in the default location