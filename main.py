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
3. IF the app didn't open, try again.
4. START by finding the Desktop path via 'get_user_folder_path'.
5. ONLY say "MISSION COMPLETE" when the file is visibly saved and the UI is stable.

AVAILABLE TOOLS:
- open_app: Launches an application (e.g. 'notepad')
- type_text: Types text into the active window
- click_element: Moves mouse and clicks at (x, y)
- press_hotkey: Performs keyboard shortcuts (e.g. 'ctrl+s')
- get_user_folder_path: Returns path to Desktop/Documents
- get_screen_text_map: Scans screen for text

COMMAND FORMAT:
To execute a tool, you MUST output a block like this:
<function=tool_name>{"arg_name": "value"}</function>
Example: <function=type_text>{"text": "Hello"}</function>

RESTRICTIONS:
- DO NOT hallucinate tools like 'save_file'.
- To save to a specific folder:
  1. PRESS 'ctrl+s' to open the Save dialog.
  2. REASONING: "I need to change the folder first."
  3. PRESS 'alt+d' to focus the Address Bar.
  4. TYPE the full folder path and PRESS 'enter' (Wait for navigation).
  5. REASONING: "Now I can name the file."
  6. PRESS 'alt+n' to focus the File Name field.
  7. TYPE the filename and PRESS 'enter'.

WINDOWS UI KNOWLEDGE:
- 'Alt+D' -> Focuses Address Bar (File Explorer/Dialogs)
- 'Alt+N' -> Focuses File Name Field
- 'Ctrl+S' -> Save
- 'Enter' in Address Bar -> Navigates to folder

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
    model_name = "llama-3.3-70b-versatile"
    
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
            
            print("   [System] Sleeping 5s...")
            time.sleep(5)

        except Exception as e:
            print(f"   [Error] {e}")
            break

    print("--- MISSION END ---")

if __name__ == "__main__":
    print("WARNING: This script will take control of your mouse.")
    time.sleep(3)
    
    # We test the Reasoning capability
    run_agent("Open Notepad, type 'Reasoning Test', and save it to 'C:\\Users\\Public\\Documents\\reasoning_test.txt'.")