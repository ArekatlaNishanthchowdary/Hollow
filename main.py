import os
import time
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, NotFound, ResourceExhausted

from memory_manager import MemoryJanitor
import tools

# --- SETUP ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("FATAL ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

genai.configure(api_key=api_key)
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
"""

def run_agent(goal):
    global HISTORY
    print(f"--- STARTING MISSION: {goal} ---")
    
    past_tips = janitor.retrieve_context(goal)
    context_str = "\n".join(past_tips) if past_tips else "No prior knowledge."
    print(f"[Memory] Retrieved Context: {context_str}")

    tool_list = [
        tools.open_app, 
        tools.get_screen_text_map, 
        tools.click_element, 
        tools.type_text, 
        tools.press_hotkey, 
        tools.get_user_folder_path
    ]
    
    # Try 2.5, fallback to 2.0
    model_name = 'gemini-2.5-flash'
    try:
        model = genai.GenerativeModel(model_name=model_name, tools=tool_list, system_instruction=SYSTEM_PROMPT)
        chat = model.start_chat(enable_automatic_function_calling=True)
    except:
        print("Switching to Gemini 2.0...")
        model = genai.GenerativeModel(model_name='gemini-2.0-flash', tools=tool_list, system_instruction=SYSTEM_PROMPT)
        chat = model.start_chat(enable_automatic_function_calling=True)

    # Initial Prompt
    next_instruction = f"GOAL: {goal}. \nCONTEXT: {context_str}"
    
    # --- CLOSED LOOP EXECUTION ---
    MAX_TURNS = 15
    
    for i in range(MAX_TURNS):
        print(f"\n[Step {i+1}] Observing & Thinking...")
        
        try:
            # 1. FORCE-FEED VISION (The Fix)
            # We grab the screen state manually so the agent CANNOT ignore it.
            print("   [System] Scanning screen...")
            current_screen_text = tools.get_screen_text_map()
            
            # 2. Construct the "Reality Check" Prompt
            full_prompt = (
                f"{next_instruction}\n\n"
                f"--- CURRENT SCREEN STATE (What you see right now) ---\n"
                f"{current_screen_text}\n"
                f"----------------------------------------------------\n"
                f"Based on this state, did the last action work? What is the next step?"
            )

            # 3. Send to Gemini
            response = chat.send_message(full_prompt)
            
            if response.text:
                print(f"   [Agent]: {response.text}")
                HISTORY.append(f"Response: {response.text[:100]}...")
            
            # --- MEMORY PRUNING ---
            if len(HISTORY) >= 5:
                print("   [Janitor] Triggering Memory Optimization...")
                HISTORY = janitor.prune_history(HISTORY)

            if "MISSION COMPLETE" in response.text:
                print("   [System] Agent indicated task completion. Stopping.")
                break
            
            # Reset instruction for next loop (The agent guides itself now)
            next_instruction = "Check the screen state above. Proceed."
            
            print("   [System] Sleeping 5s...")
            time.sleep(5)

        except ResourceExhausted:
            print("   [Error] Rate Limit Hit. Waiting 60s...")
            time.sleep(60)
        except Exception as e:
            print(f"   [Error] {e}")
            break

    print("--- MISSION END ---")

if __name__ == "__main__":
    print("WARNING: This script will take control of your mouse.")
    time.sleep(3)
    
    # We test the "File Exists" scenario
    run_agent("Open Notepad, type 'Observation Test', and save it to Desktop as 'test_obs.txt'. If it exists, overwrite it.")